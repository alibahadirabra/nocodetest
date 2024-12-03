# Copyright (c) 2015, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import functools
import gc
import logging
import os
import re

from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.http import generate_etag, is_resource_modified, quote_etag
from werkzeug.middleware.profiler import ProfilerMiddleware
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.wrappers import Request, Response
from werkzeug.wsgi import ClosingIterator

import traquent
import traquent.api
import traquent.handler
import traquent.monitor
import traquent.rate_limiter
import traquent.recorder
import traquent.utils.response
from traquent import _
from traquent.auth import SAFE_HTTP_METHODS, UNSAFE_HTTP_METHODS, HTTPRequest, validate_auth
from traquent.middlewares import StaticDataMiddleware
from traquent.utils import CallbackManager, cint, get_site_name
from traquent.utils.data import escape_html
from traquent.utils.error import log_error_snapshot
from traquent.website.serve import get_response

_site = None
_sites_path = os.environ.get("SITES_PATH", ".")


# If gc.freeze is done then importing modules before forking allows us to share the memory
if traquent._tune_gc:
	import gettext

	import babel
	import babel.messages
	import bleach
	import num2words
	import pydantic

	import traquent.boot
	import traquent.client
	import traquent.core.doctype.file.file
	import traquent.core.doctype.user.user
	import traquent.database.mariadb.database  # Load database related utils
	import traquent.database.query
	import traquent.desk.desktop  # workspace
	import traquent.desk.form.save
	import traquent.model.db_query
	import traquent.query_builder
	import traquent.utils.background_jobs  # Enqueue is very common
	import traquent.utils.data  # common utils
	import traquent.utils.jinja  # web page rendering
	import traquent.utils.jinja_globals
	import traquent.utils.redis_wrapper  # Exact redis_wrapper
	import traquent.utils.safe_exec
	import traquent.utils.typing_validations  # any whitelisted method uses this
	import traquent.website.path_resolver  # all the page types and resolver
	import traquent.website.router  # Website router
	import traquent.website.website_generator  # web page doctypes

# end: module pre-loading


def after_response_wrapper(app):
	"""Wrap a WSGI application to call after_response hooks after we have responded.

	This is done to reduce response time by deferring expensive tasks."""

	@functools.wraps(app)
	def application(environ, start_response):
		return ClosingIterator(
			app(environ, start_response),
			(
				traquent.rate_limiter.update,
				traquent.recorder.dump,
				traquent.request.after_response.run,
				traquent.destroy,
			),
		)

	return application


@after_response_wrapper
@Request.application
def application(request: Request):
	response = None

	try:
		rollback = True

		init_request(request)

		validate_auth()

		if request.method == "OPTIONS":
			response = Response()

		elif traquent.form_dict.cmd:
			from traquent.deprecation_dumpster import deprecation_warning

			deprecation_warning(
				"unknown",
				"v17",
				f"{traquent.form_dict.cmd}: Sending `cmd` for RPC calls is deprecated, call REST API instead `/api/method/cmd`",
			)
			traquent.handler.handle()
			response = traquent.utils.response.build_response("json")

		elif request.path.startswith("/api/"):
			response = traquent.api.handle(request)

		elif request.path.startswith("/backups"):
			response = traquent.utils.response.download_backup(request.path)

		elif request.path.startswith("/private/files/"):
			response = traquent.utils.response.download_private_file(request.path)

		elif request.method in ("GET", "HEAD", "POST"):
			response = get_response()

		else:
			raise NotFound

	except HTTPException as e:
		return e

	except Exception as e:
		response = handle_exception(e)

	else:
		rollback = sync_database(rollback)

	finally:
		# Important note:
		# this function *must* always return a response, hence any exception thrown outside of
		# try..catch block like this finally block needs to be handled appropriately.

		if rollback and request.method in UNSAFE_HTTP_METHODS and traquent.db:
			traquent.db.rollback()

		try:
			run_after_request_hooks(request, response)
		except Exception:
			# We can not handle exceptions safely here.
			traquent.logger().error("Failed to run after request hook", exc_info=True)

	log_request(request, response)
	# return 304 if unmodified
	if not response.direct_passthrough:
		etag = generate_etag(response.data)
		if not is_resource_modified(request.environ, etag):
			return Response(status=304, headers={"ETag": quote_etag(etag)})
	process_response(response)

	return response


def run_after_request_hooks(request, response):
	if not getattr(traquent.local, "initialised", False):
		return

	for after_request_task in traquent.get_hooks("after_request"):
		traquent.call(after_request_task, response=response, request=request)


def init_request(request):
	traquent.local.request = request
	traquent.local.request.after_response = CallbackManager()

	traquent.local.is_ajax = traquent.get_request_header("X-Requested-With") == "XMLHttpRequest"

	site = _site or request.headers.get("X-traquent-Site-Name") or get_site_name(request.host)
	traquent.init(site, sites_path=_sites_path, force=True)

	if not (traquent.local.conf and traquent.local.conf.db_name):
		# site does not exist
		raise NotFound

	if traquent.local.conf.maintenance_mode:
		traquent.connect()
		if traquent.local.conf.allow_reads_during_maintenance:
			setup_read_only_mode()
		else:
			raise traquent.SessionStopped("Session Stopped")
	else:
		traquent.connect(set_admin_as_user=False)
	if request.path.startswith("/api/method/upload_file"):
		from traquent.core.api.file import get_max_file_size

		request.max_content_length = get_max_file_size()
	else:
		request.max_content_length = cint(traquent.local.conf.get("max_file_size")) or 25 * 1024 * 1024
	make_form_dict(request)

	if request.method != "OPTIONS":
		traquent.local.http_request = HTTPRequest()

	for before_request_task in traquent.get_hooks("before_request"):
		traquent.call(before_request_task)


def setup_read_only_mode():
	"""During maintenance_mode reads to DB can still be performed to reduce downtime. This
	function sets up read only mode

	- Setting global flag so other pages, desk and database can know that we are in read only mode.
	- Setup read only database access either by:
	    - Connecting to read replica if one exists
	    - Or setting up read only SQL transactions.
	"""
	traquent.flags.read_only = True

	# If replica is available then just connect replica, else setup read only transaction.
	if traquent.conf.read_from_replica:
		traquent.connect_replica()
	else:
		traquent.db.begin(read_only=True)


def log_request(request, response):
	if hasattr(traquent.local, "conf") and traquent.local.conf.enable_traquent_logger:
		traquent.logger("traquent.web", allow_site=traquent.local.site).info(
			{
				"site": get_site_name(request.host),
				"remote_addr": getattr(request, "remote_addr", "NOTFOUND"),
				"pid": os.getpid(),
				"user": getattr(traquent.local.session, "user", "NOTFOUND"),
				"base_url": getattr(request, "base_url", "NOTFOUND"),
				"full_path": getattr(request, "full_path", "NOTFOUND"),
				"method": getattr(request, "method", "NOTFOUND"),
				"scheme": getattr(request, "scheme", "NOTFOUND"),
				"http_status_code": getattr(response, "status_code", "NOTFOUND"),
			}
		)


def process_response(response):
	if not response:
		return

	# cache control
	# read: https://simonhearne.com/2022/caching-header-best-practices/
	if traquent.local.response.can_cache:
		response.headers.extend(
			{
				# default: 5m (proxy), 5m (client), 3h (allow stale resources for this long if upstream is down)
				"Cache-Control": "public,s-maxage=300,max-age=300,stale-while-revalidate=10800",
				# for revalidation of a stale resource
				"ETag": quote_etag(generate_etag(response.data)),
			}
		)
	else:
		response.headers.extend(
			{
				"Cache-Control": "no-store,no-cache,must-revalidate,max-age=0",
			}
		)

	# Set cookies, only if response is non-cacheable to avoid proxy cache invalidation
	if hasattr(traquent.local, "cookie_manager") and not traquent.local.response.can_cache:
		traquent.local.cookie_manager.flush_cookies(response=response)

	# rate limiter headers
	if hasattr(traquent.local, "rate_limiter"):
		response.headers.extend(traquent.local.rate_limiter.headers())

	if trace_id := traquent.monitor.get_trace_id():
		response.headers.extend({"X-traquent-Request-Id": trace_id})

	# CORS headers
	if hasattr(traquent.local, "conf"):
		set_cors_headers(response)


def set_cors_headers(response):
	if not (
		(allowed_origins := traquent.conf.allow_cors)
		and (request := traquent.local.request)
		and (origin := request.headers.get("Origin"))
	):
		return

	if allowed_origins != "*":
		if not isinstance(allowed_origins, list):
			allowed_origins = [allowed_origins]

		if origin not in allowed_origins:
			return

	cors_headers = {
		"Access-Control-Allow-Credentials": "true",
		"Access-Control-Allow-Origin": origin,
		"Vary": "Origin",
	}

	# only required for preflight requests
	if request.method == "OPTIONS":
		cors_headers["Access-Control-Allow-Methods"] = request.headers.get("Access-Control-Request-Method")

		if allowed_headers := request.headers.get("Access-Control-Request-Headers"):
			cors_headers["Access-Control-Allow-Headers"] = allowed_headers

		# allow browsers to cache preflight requests for upto a day
		if not traquent.conf.developer_mode:
			cors_headers["Access-Control-Max-Age"] = "86400"

	response.headers.extend(cors_headers)


def make_form_dict(request: Request):
	import json

	request_data = request.get_data(as_text=True)
	if request_data and request.is_json:
		args = json.loads(request_data)
	else:
		args = {}
		args.update(request.args or {})
		args.update(request.form or {})

	if isinstance(args, dict):
		traquent.local.form_dict = traquent._dict(args)
		# _ is passed by $.ajax so that the request is not cached by the browser. So, remove _ from form_dict
		traquent.local.form_dict.pop("_", None)
	elif isinstance(args, list):
		traquent.local.form_dict["data"] = args
	else:
		traquent.throw(_("Invalid request arguments"))


def handle_exception(e):
	response = None
	http_status_code = getattr(e, "http_status_code", 500)
	return_as_message = False
	accept_header = traquent.get_request_header("Accept") or ""
	respond_as_json = (
		traquent.get_request_header("Accept")
		and (traquent.local.is_ajax or "application/json" in accept_header)
		or (traquent.local.request.path.startswith("/api/") and not accept_header.startswith("text"))
	)

	allow_traceback = traquent.get_system_settings("allow_error_traceback") if traquent.db else False

	if not traquent.session.user:
		# If session creation fails then user won't be unset. This causes a lot of code that
		# assumes presence of this to fail. Session creation fails => guest or expired login
		# usually.
		traquent.session.user = "Guest"

	if respond_as_json:
		# handle ajax responses first
		# if the request is ajax, send back the trace or error message
		response = traquent.utils.response.report_error(http_status_code)

	elif isinstance(e, traquent.SessionStopped):
		response = traquent.utils.response.handle_session_stopped()

	elif (
		http_status_code == 500
		and (traquent.db and isinstance(e, traquent.db.InternalError))
		and (traquent.db and (traquent.db.is_deadlocked(e) or traquent.db.is_timedout(e)))
	):
		http_status_code = 508

	elif http_status_code == 401:
		traquent.respond_as_web_page(
			_("Session Expired"),
			_("Your session has expired, please login again to continue."),
			http_status_code=http_status_code,
			indicator_color="red",
		)
		return_as_message = True

	elif http_status_code == 403:
		traquent.respond_as_web_page(
			_("Not Permitted"),
			_("You do not have enough permissions to complete the action"),
			http_status_code=http_status_code,
			indicator_color="red",
		)
		return_as_message = True

	elif http_status_code == 404:
		traquent.respond_as_web_page(
			_("Not Found"),
			_("The resource you are looking for is not available"),
			http_status_code=http_status_code,
			indicator_color="red",
		)
		return_as_message = True

	elif http_status_code == 429:
		response = traquent.rate_limiter.respond()

	else:
		traceback = "<pre>" + escape_html(traquent.get_traceback()) + "</pre>"
		# disable traceback in production if flag is set
		if traquent.local.flags.disable_traceback or not allow_traceback and not traquent.local.dev_server:
			traceback = ""

		traquent.respond_as_web_page(
			"Server Error", traceback, http_status_code=http_status_code, indicator_color="red", width=640
		)
		return_as_message = True

	if e.__class__ == traquent.AuthenticationError:
		if hasattr(traquent.local, "login_manager"):
			traquent.local.login_manager.clear_cookies()

	if http_status_code >= 500:
		log_error_snapshot(e)

	if return_as_message:
		response = get_response("message", http_status_code=http_status_code)

	if traquent.conf.get("developer_mode") and not respond_as_json:
		# don't fail silently for non-json response errors
		print(traquent.get_traceback())

	return response


def sync_database(rollback: bool) -> bool:
	# if HTTP method would change server state, commit if necessary
	if traquent.db and (traquent.local.flags.commit or traquent.local.request.method in UNSAFE_HTTP_METHODS):
		traquent.db.commit()
		rollback = False
	elif traquent.db:
		traquent.db.rollback()
		rollback = False

	# update session
	if session := getattr(traquent.local, "session_obj", None):
		if session.update():
			rollback = False

	return rollback


# Always initialize sentry SDK if the DSN is sent
if sentry_dsn := os.getenv("traquent_SENTRY_DSN"):
	import sentry_sdk
	from sentry_sdk.integrations.argv import ArgvIntegration
	from sentry_sdk.integrations.atexit import AtexitIntegration
	from sentry_sdk.integrations.dedupe import DedupeIntegration
	from sentry_sdk.integrations.excepthook import ExcepthookIntegration
	from sentry_sdk.integrations.modules import ModulesIntegration
	from sentry_sdk.integrations.wsgi import SentryWsgiMiddleware

	from traquent.utils.sentry import traquentIntegration, before_send

	integrations = [
		AtexitIntegration(),
		ExcepthookIntegration(),
		DedupeIntegration(),
		ModulesIntegration(),
		ArgvIntegration(),
	]

	experiments = {}
	kwargs = {}

	if os.getenv("ENABLE_SENTRY_DB_MONITORING"):
		integrations.append(traquentIntegration())
		experiments["record_sql_params"] = True

	if tracing_sample_rate := os.getenv("SENTRY_TRACING_SAMPLE_RATE"):
		kwargs["traces_sample_rate"] = float(tracing_sample_rate)
		application = SentryWsgiMiddleware(application)

	sentry_sdk.init(
		dsn=sentry_dsn,
		before_send=before_send,
		attach_stacktrace=True,
		release=traquent.__version__,
		auto_enabling_integrations=False,
		default_integrations=False,
		integrations=integrations,
		_experiments=experiments,
		**kwargs,
	)


def serve(
	port=8000,
	profile=False,
	no_reload=False,
	no_threading=False,
	site=None,
	sites_path=".",
	proxy=False,
):
	global application, _site, _sites_path
	_site = site
	_sites_path = sites_path

	from werkzeug.serving import run_simple

	if profile or os.environ.get("USE_PROFILER"):
		application = ProfilerMiddleware(application, sort_by=("cumtime", "calls"))

	if not os.environ.get("NO_STATICS"):
		application = application_with_statics()

	if proxy or os.environ.get("USE_PROXY"):
		application = ProxyFix(application, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

	application.debug = True
	application.config = {"SERVER_NAME": "127.0.0.1:8000"}

	log = logging.getLogger("werkzeug")
	log.propagate = False

	in_test_env = os.environ.get("CI")
	if in_test_env:
		log.setLevel(logging.ERROR)

	run_simple(
		"0.0.0.0",
		int(port),
		application,
		exclude_patterns=["test_*"],
		use_reloader=False if in_test_env else not no_reload,
		use_debugger=not in_test_env,
		use_evalex=not in_test_env,
		threaded=not no_threading,
	)


def application_with_statics():
	global application, _sites_path

	application = SharedDataMiddleware(application, {"/assets": str(os.path.join(_sites_path, "assets"))})

	application = StaticDataMiddleware(application, {"/files": str(os.path.abspath(_sites_path))})

	return application


# Remove references to pattern that are pre-compiled and loaded to global scopes.
re.purge()

# Both Gunicorn and RQ use forking to spawn workers. In an ideal world, the fork should be sharing
# most of the memory if there are no writes made to data because of Copy on Write, however,
# python's GC is not CoW friendly and writes to data even if user-code doesn't. Specifically, the
# generational GC which stores and mutates every python object: `PyGC_Head`
#
# Calling gc.freeze() moves all the objects imported so far into permanant generation and hence
# doesn't mutate `PyGC_Head`
#
# Refer to issue for more info: https://github.com/traquent/traquent/issues/18927
if traquent._tune_gc:
	gc.collect()  # clean up any garbage created so far before freeze
	gc.freeze()
