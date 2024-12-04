# Copyright (c) 2021, traquent Technologies Pvt. Ltd. and Contributors
# MIT License. See LICENSE
import base64
import binascii
from urllib.parse import quote, urlencode, urlparse

from werkzeug.wrappers import Response

import traquent
import traquent.database
import traquent.utils
import traquent.utils.user
from traquent import _
from traquent.apps import get_default_path
from traquent.core.doctype.activity_log.activity_log import add_authentication_log
from traquent.sessions import Session, clear_sessions, delete_session, get_expiry_in_seconds
from traquent.translate import get_language
from traquent.twofactor import (
	authenticate_for_2factor,
	confirm_otp_token,
	get_cached_user_pass,
	should_run_2fa,
)
from traquent.utils import cint, date_diff, datetime, get_datetime, today
from traquent.utils.password import check_password, get_decrypted_password
from traquent.website.utils import get_home_page

SAFE_HTTP_METHODS = frozenset(("GET", "HEAD", "OPTIONS"))
UNSAFE_HTTP_METHODS = frozenset(("POST", "PUT", "DELETE", "PATCH"))
MAX_PASSWORD_SIZE = 512


class HTTPRequest:
	def __init__(self):
		# set traquent.local.request_ip
		self.set_request_ip()

		# load cookies
		self.set_cookies()

		# login and start/resume user session
		self.set_session()

		# set request language
		self.set_lang()

		# match csrf token from current session
		self.validate_csrf_token()

		# write out latest cookies
		traquent.local.cookie_manager.init_cookies()

	@property
	def domain(self):
		if not getattr(self, "_domain", None):
			self._domain = traquent.request.host
			if self._domain and self._domain.startswith("www."):
				self._domain = self._domain[4:]

		return self._domain

	def set_request_ip(self):
		if traquent.get_request_header("X-Forwarded-For"):
			traquent.local.request_ip = (traquent.get_request_header("X-Forwarded-For").split(",", 1)[0]).strip()

		elif traquent.get_request_header("REMOTE_ADDR"):
			traquent.local.request_ip = traquent.get_request_header("REMOTE_ADDR")

		else:
			traquent.local.request_ip = "127.0.0.1"

	def set_cookies(self):
		traquent.local.cookie_manager = CookieManager()

	def set_session(self):
		traquent.local.login_manager = LoginManager()

	def validate_csrf_token(self):
		if (
			not traquent.request
			or traquent.request.method not in UNSAFE_HTTP_METHODS
			or traquent.conf.ignore_csrf
			or not traquent.session
			or not (saved_token := traquent.session.data.csrf_token)
			or (
				(traquent.get_request_header("X-traquent-CSRF-Token") or traquent.form_dict.pop("csrf_token", None))
				== saved_token
			)
		):
			return

		traquent.flags.disable_traceback = True
		traquent.throw(_("Invalid Request"), traquent.CSRFTokenError)

	def set_lang(self):
		traquent.local.lang = get_language()


class LoginManager:
	__slots__ = ("user", "info", "full_name", "user_type", "user_lang", "resume")

	def __init__(self):
		self.user = None
		self.info = None
		self.full_name = None
		self.user_type = None

		if traquent.local.form_dict.get("cmd") == "login" or traquent.local.request.path == "/api/method/login":
			if self.login() is False:
				return
			self.resume = False

			# run login triggers
			self.run_trigger("on_session_creation")
		else:
			try:
				self.resume = True
				self.make_session(resume=True)
				self.get_user_info()
				self.set_user_info(resume=True)
			except AttributeError:
				self.user = "Guest"
				self.get_user_info()
				self.make_session()
				self.set_user_info()

	def login(self):
		self.run_trigger("before_login")

		if traquent.get_system_settings("disable_user_pass_login"):
			traquent.throw(_("Login with username and password is not allowed."), traquent.AuthenticationError)

		# clear cache
		traquent.clear_cache(user=traquent.form_dict.get("usr"))
		user, pwd = get_cached_user_pass()
		self.authenticate(user=user, pwd=pwd)
		if self.force_user_to_reset_password():
			doc = traquent.get_doc("User", self.user)
			traquent.local.response["redirect_to"] = doc.reset_password(send_email=False, password_expired=True)
			traquent.local.response["message"] = "Password Reset"
			return False

		if should_run_2fa(self.user):
			authenticate_for_2factor(self.user)
			if not confirm_otp_token(self):
				return False
		traquent.form_dict.pop("pwd", None)
		self.post_login()

	def post_login(self):
		self.run_trigger("on_login")
		validate_ip_address(self.user)
		self.validate_hour()
		self.get_user_info()
		self.make_session()
		self.setup_boot_cache()
		self.set_user_info()

	def get_user_info(self):
		self.info = traquent.get_cached_value(
			"User", self.user, ["user_type", "first_name", "last_name", "user_image"], as_dict=1
		)
		self.user_lang = traquent.translate.get_user_lang()
		self.user_type = self.info.user_type

	def setup_boot_cache(self):
		traquent.cache_manager.build_table_count_cache()
		traquent.cache_manager.build_domain_restriced_doctype_cache()
		traquent.cache_manager.build_domain_restriced_page_cache()

	def set_user_info(self, resume=False):
		# set sid again
		traquent.local.cookie_manager.init_cookies()

		self.full_name = " ".join(filter(None, [self.info.first_name, self.info.last_name]))

		if self.info.user_type == "Website User":
			traquent.local.cookie_manager.set_cookie("system_user", "no")
			if not resume:
				traquent.local.response["message"] = "No App"
				traquent.local.response["home_page"] = get_default_path() or "/" + get_home_page()
		else:
			traquent.local.cookie_manager.set_cookie("system_user", "yes")
			if not resume:
				traquent.local.response["message"] = "Logged In"
				traquent.local.response["home_page"] = get_default_path() or "/app"

		if not resume:
			traquent.response["full_name"] = self.full_name

		# redirect information
		redirect_to = traquent.cache.hget("redirect_after_login", self.user)
		if redirect_to:
			traquent.local.response["redirect_to"] = redirect_to
			traquent.cache.hdel("redirect_after_login", self.user)

		traquent.local.cookie_manager.set_cookie("full_name", self.full_name)
		traquent.local.cookie_manager.set_cookie("user_id", self.user)
		traquent.local.cookie_manager.set_cookie("user_image", self.info.user_image or "")
		# cache control: round trip the effectively delivered language
		traquent.local.cookie_manager.set_cookie("user_lang", self.user_lang)

	def clear_preferred_language(self):
		traquent.local.cookie_manager.delete_cookie("preferred_language")

	def make_session(self, resume=False):
		# start session
		traquent.local.session_obj = Session(
			user=self.user, resume=resume, full_name=self.full_name, user_type=self.user_type
		)

		# reset user if changed to Guest
		self.user = traquent.local.session_obj.user
		traquent.local.session = traquent.local.session_obj.data
		self.clear_active_sessions()

	def clear_active_sessions(self):
		"""Clear other sessions of the current user if `deny_multiple_sessions` is not set"""
		if traquent.session.user == "Guest":
			return

		if not (
			cint(traquent.conf.get("deny_multiple_sessions"))
			or cint(traquent.db.get_system_setting("deny_multiple_sessions"))
		):
			return

		clear_sessions(traquent.session.user, keep_current=True)

	def authenticate(self, user: str | None = None, pwd: str | None = None):
		from traquent.core.doctype.user.user import User

		if not (user and pwd):
			user, pwd = traquent.form_dict.get("usr"), traquent.form_dict.get("pwd")
		if not (user and pwd):
			self.fail(_("Incomplete login details"), user=user)

		if len(pwd) > MAX_PASSWORD_SIZE:
			self.fail(_("Password size exceeded the maximum allowed size"), user=user)

		_raw_user_name = user
		user = User.find_by_credentials(user, pwd)

		ip_tracker = get_login_attempt_tracker(traquent.local.request_ip)
		if not user:
			ip_tracker and ip_tracker.add_failure_attempt()
			self.fail("Invalid login credentials", user=_raw_user_name)

		# Current login flow uses cached credentials for authentication while checking OTP.
		# Incase of OTP check, tracker for auth needs to be disabled(If not, it can remove tracker history as it is going to succeed anyway)
		# Tracker is activated for 2FA incase of OTP.
		ignore_tracker = should_run_2fa(user.name) and ("otp" in traquent.form_dict)
		user_tracker = None if ignore_tracker else get_login_attempt_tracker(user.name)

		if not user.is_authenticated:
			user_tracker and user_tracker.add_failure_attempt()
			ip_tracker and ip_tracker.add_failure_attempt()
			self.fail("Invalid login credentials", user=user.name)
		elif not (user.name == "Administrator" or user.enabled):
			user_tracker and user_tracker.add_failure_attempt()
			ip_tracker and ip_tracker.add_failure_attempt()
			self.fail("User disabled or missing", user=user.name)
		else:
			user_tracker and user_tracker.add_success_attempt()
			ip_tracker and ip_tracker.add_success_attempt()
		self.user = user.name

	def force_user_to_reset_password(self):
		if not self.user:
			return

		if self.user in traquent.STANDARD_USERS:
			return False

		reset_pwd_after_days = cint(traquent.get_system_settings("force_user_to_reset_password"))

		if reset_pwd_after_days:
			last_password_reset_date = (
				traquent.db.get_value("User", self.user, "last_password_reset_date") or today()
			)

			last_pwd_reset_days = date_diff(today(), last_password_reset_date)

			if last_pwd_reset_days > reset_pwd_after_days:
				return True

	def check_password(self, user, pwd):
		"""check password"""
		try:
			# return user in correct case
			return check_password(user, pwd)
		except traquent.AuthenticationError:
			self.fail("Incorrect password", user=user)

	def fail(self, message, user=None):
		if not user:
			user = _("Unknown User")
		traquent.local.response["message"] = message
		add_authentication_log(message, user, status="Failed")
		traquent.db.commit()
		raise traquent.AuthenticationError

	def run_trigger(self, event="on_login"):
		for method in traquent.get_hooks().get(event, []):
			traquent.call(traquent.get_attr(method), login_manager=self)

	def validate_hour(self):
		"""check if user is logging in during restricted hours"""
		login_before = cint(traquent.db.get_value("User", self.user, "login_before", ignore=True))
		login_after = cint(traquent.db.get_value("User", self.user, "login_after", ignore=True))

		if not (login_before or login_after):
			return

		from traquent.utils import now_datetime

		current_hour = int(now_datetime().strftime("%H"))

		if login_before and current_hour >= login_before:
			traquent.throw(_("Login not allowed at this time"), traquent.AuthenticationError)

		if login_after and current_hour < login_after:
			traquent.throw(_("Login not allowed at this time"), traquent.AuthenticationError)

	def login_as_guest(self):
		"""login as guest"""
		self.login_as("Guest")

	def login_as(self, user):
		self.user = user
		self.post_login()

	def impersonate(self, user):
		current_user = traquent.session.user
		self.login_as(user)
		# Flag this session as impersonated session, so other code can log this.
		traquent.local.session_obj.set_impersonsated(current_user)

	def logout(self, arg="", user=None):
		if not user:
			user = traquent.session.user
		self.run_trigger("on_logout")

		if user == traquent.session.user:
			delete_session(traquent.session.sid, user=user, reason="User Manually Logged Out")
			self.clear_cookies()
			if traquent.request:
				self.login_as_guest()
		else:
			clear_sessions(user)

	def clear_cookies(self):
		clear_cookies()


class CookieManager:
	def __init__(self):
		self.cookies = {}
		self.to_delete = []

	def init_cookies(self):
		if not traquent.local.session.get("sid"):
			return

		if traquent.session.sid:
			self.set_cookie("sid", traquent.session.sid, max_age=get_expiry_in_seconds(), httponly=True)

	def set_cookie(
		self,
		key,
		value,
		expires=None,
		secure=False,
		httponly=False,
		samesite="Lax",
		max_age=None,
	):
		if not secure and hasattr(traquent.local, "request"):
			secure = traquent.local.request.scheme == "https"

		self.cookies[key] = {
			"value": value,
			"expires": expires,
			"secure": secure,
			"httponly": httponly,
			"samesite": samesite,
			"max_age": max_age,
		}

	def delete_cookie(self, to_delete):
		if not isinstance(to_delete, list | tuple):
			to_delete = [to_delete]

		self.to_delete.extend(to_delete)

	def flush_cookies(self, response: Response):
		for key, opts in self.cookies.items():
			response.set_cookie(
				key,
				quote((opts.get("value") or "").encode("utf-8")),
				expires=opts.get("expires"),
				secure=opts.get("secure"),
				httponly=opts.get("httponly"),
				samesite=opts.get("samesite"),
				max_age=opts.get("max_age"),
			)

		# expires yesterday!
		expires = datetime.datetime.now() + datetime.timedelta(days=-1)
		for key in set(self.to_delete):
			response.set_cookie(key, "", expires=expires)


frappe.whitelist()
def get_logged_user():
	return traquent.session.user


def clear_cookies():
	if hasattr(traquent.local, "session"):
		traquent.session.sid = ""
	traquent.local.cookie_manager.delete_cookie(
		["full_name", "user_id", "sid", "user_image", "user_lang", "system_user"]
	)


def validate_ip_address(user):
	"""
	Method to check if the user has IP restrictions enabled, and if so is the IP address they are
	connecting from allowlisted.

	Certain methods called from our socketio backend need direct access, and so the IP is not
	checked for those
	"""
	if hasattr(traquent.local, "request") and traquent.local.request.path.startswith(
		"/api/method/traquent.realtime."
	):
		return True

	from traquent.core.doctype.user.user import get_restricted_ip_list

	# Only fetch required fields - for perf
	user_fields = ["restrict_ip", "bypass_restrict_ip_check_if_2fa_enabled"]
	user_info = (
		traquent.get_cached_value("User", user, user_fields, as_dict=True)
		if not traquent.flags.in_test
		else traquent.db.get_value("User", user, user_fields, as_dict=True)
	)
	ip_list = get_restricted_ip_list(user_info)
	if not ip_list:
		return

	system_settings = (
		traquent.get_cached_doc("System Settings")
		if not traquent.flags.in_test
		else traquent.get_single("System Settings")
	)
	# check if bypass restrict ip is enabled for all users
	bypass_restrict_ip_check = system_settings.bypass_restrict_ip_check_if_2fa_enabled

	# check if two factor auth is enabled
	if system_settings.enable_two_factor_auth and not bypass_restrict_ip_check:
		# check if bypass restrict ip is enabled for login user
		bypass_restrict_ip_check = user_info.bypass_restrict_ip_check_if_2fa_enabled

	for ip in ip_list:
		if traquent.local.request_ip.startswith(ip) or bypass_restrict_ip_check:
			return

	traquent.throw(_("Access not allowed from this IP Address"), traquent.AuthenticationError)


def get_login_attempt_tracker(key: str, raise_locked_exception: bool = True):
	"""Get login attempt tracker instance.

	:param user_name: Name of the loggedin user
	:param raise_locked_exception: If set, raises an exception incase of user not allowed to login
	"""
	sys_settings = traquent.get_doc("System Settings")
	track_login_attempts = sys_settings.allow_consecutive_login_attempts > 0
	tracker_kwargs = {}

	if track_login_attempts:
		tracker_kwargs["lock_interval"] = sys_settings.allow_login_after_fail
		tracker_kwargs["max_consecutive_login_attempts"] = sys_settings.allow_consecutive_login_attempts

	tracker = LoginAttemptTracker(key, **tracker_kwargs)

	if raise_locked_exception and track_login_attempts and not tracker.is_user_allowed():
		traquent.throw(
			_("Your account has been locked and will resume after {0} seconds").format(
				sys_settings.allow_login_after_fail
			),
			traquent.SecurityException,
		)
	return tracker


class LoginAttemptTracker:
	"""Track login attemts of a user.

	Lock the account for s number of seconds if there have been n consecutive unsuccessful attempts to log in.
	"""

	def __init__(
		self,
		key: str,
		max_consecutive_login_attempts: int = 3,
		lock_interval: int = 5 * 60,
		*,
		user_name: str | None = None,
	):
		"""Initialize the tracker.

		:param user_name: Name of the loggedin user
		:param max_consecutive_login_attempts: Maximum allowed consecutive failed login attempts
		:param lock_interval: Locking interval incase of maximum failed attempts
		"""
		if user_name:
			from traquent.deprecation_dumpster import deprecation_warning

			deprecation_warning("unknown", "v17", "`username` parameter is deprecated, use `key` instead.")
		self.key = key or user_name
		self.lock_interval = datetime.timedelta(seconds=lock_interval)
		self.max_failed_logins = max_consecutive_login_attempts

	@property
	def login_failed_count(self):
		return traquent.cache.hget("login_failed_count", self.key)

	@login_failed_count.setter
	def login_failed_count(self, count):
		traquent.cache.hset("login_failed_count", self.key, count)

	@login_failed_count.deleter
	def login_failed_count(self):
		traquent.cache.hdel("login_failed_count", self.key)

	@property
	def login_failed_time(self):
		"""First failed login attempt time within lock interval.

		For every user we track only First failed login attempt time within lock interval of time.
		"""
		return traquent.cache.hget("login_failed_time", self.key)

	@login_failed_time.setter
	def login_failed_time(self, timestamp):
		traquent.cache.hset("login_failed_time", self.key, timestamp)

	@login_failed_time.deleter
	def login_failed_time(self):
		traquent.cache.hdel("login_failed_time", self.key)

	def add_failure_attempt(self):
		"""Log user failure attempts into the system.

		Increase the failure count if new failure is with in current lock interval time period, if not reset the login failure count.
		"""
		login_failed_time = self.login_failed_time
		login_failed_count = self.login_failed_count  # Consecutive login failure count
		current_time = get_datetime()

		if not (login_failed_time and login_failed_count):
			login_failed_time, login_failed_count = current_time, 0

		if login_failed_time + self.lock_interval > current_time:
			login_failed_count += 1
		else:
			login_failed_time, login_failed_count = current_time, 1

		self.login_failed_time = login_failed_time
		self.login_failed_count = login_failed_count

	def add_success_attempt(self):
		"""Reset login failures."""
		del self.login_failed_count
		del self.login_failed_time

	def is_user_allowed(self) -> bool:
		"""Is user allowed to login

		User is not allowed to login if login failures are greater than threshold within in lock interval from first login failure.
		"""
		login_failed_time = self.login_failed_time
		login_failed_count = self.login_failed_count or 0
		current_time = get_datetime()

		if (
			login_failed_time
			and login_failed_time + self.lock_interval > current_time
			and login_failed_count > self.max_failed_logins
		):
			return False
		return True


def validate_auth():
	"""
	Authenticate and sets user for the request.
	"""
	authorization_header = traquent.get_request_header("Authorization", "").split(" ")

	if len(authorization_header) == 2:
		validate_oauth(authorization_header)
		validate_auth_via_api_keys(authorization_header)

	validate_auth_via_hooks()

	# If login via bearer, basic or keypair didn't work then authentication failed and we
	# should terminate here.
	if len(authorization_header) == 2 and traquent.session.user in ("", "Guest"):
		raise traquent.AuthenticationError


def validate_oauth(authorization_header):
	"""
	Authenticate request using OAuth and set session user

	Args:
	        authorization_header (list of str): The 'Authorization' header containing the prefix and token
	"""

	from traquent.integrations.oauth2 import get_oauth_server
	from traquent.oauth import get_url_delimiter

	if authorization_header[0].lower() != "bearer":
		return

	form_dict = traquent.local.form_dict
	token = authorization_header[1]
	req = traquent.request
	parsed_url = urlparse(req.url)
	access_token = {"access_token": token}
	uri = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path + "?" + urlencode(access_token)
	http_method = req.method
	headers = req.headers
	body = req.get_data()
	if req.content_type and "multipart/form-data" in req.content_type:
		body = None

	try:
		required_scopes = traquent.db.get_value("OAuth Bearer Token", token, "scopes").split(
			get_url_delimiter()
		)
		valid, oauthlib_request = get_oauth_server().verify_request(
			uri, http_method, body, headers, required_scopes
		)
		if valid:
			traquent.set_user(traquent.db.get_value("OAuth Bearer Token", token, "user"))
			traquent.local.form_dict = form_dict
	except AttributeError:
		pass


def validate_auth_via_api_keys(authorization_header):
	"""
	Authenticate request using API keys and set session user

	Args:
	        authorization_header (list of str): The 'Authorization' header containing the prefix and token
	"""

	try:
		auth_type, auth_token = authorization_header
		authorization_source = traquent.get_request_header("traquent-Authorization-Source")
		if auth_type.lower() == "basic":
			api_key, api_secret = traquent.safe_decode(base64.b64decode(auth_token)).split(":")
			validate_api_key_secret(api_key, api_secret, authorization_source)
		elif auth_type.lower() == "token":
			api_key, api_secret = auth_token.split(":")
			validate_api_key_secret(api_key, api_secret, authorization_source)
	except binascii.Error:
		traquent.throw(
			_("Failed to decode token, please provide a valid base64-encoded token."),
			traquent.InvalidAuthorizationToken,
		)
	except (AttributeError, TypeError, ValueError):
		pass


def validate_api_key_secret(api_key, api_secret, traquent_authorization_source=None):
	"""traquent_authorization_source to provide api key and secret for a doctype apart from User"""
	doctype = traquent_authorization_source or "User"
	doc = traquent.db.get_value(doctype=doctype, filters={"api_key": api_key}, fieldname=["name"])
	if not doc:
		raise traquent.AuthenticationError
	form_dict = traquent.local.form_dict
	doc_secret = get_decrypted_password(doctype, doc, fieldname="api_secret")
	if api_secret == doc_secret:
		if doctype == "User":
			user = traquent.db.get_value(doctype="User", filters={"api_key": api_key}, fieldname=["name"])
		else:
			user = traquent.db.get_value(doctype, doc, "user")
		if traquent.local.login_manager.user in ("", "Guest"):
			traquent.set_user(user)
		traquent.local.form_dict = form_dict
	else:
		raise traquent.AuthenticationError


def validate_auth_via_hooks():
	for auth_hook in traquent.get_hooks("auth_hooks", []):
		traquent.get_attr(auth_hook)()
