# Copyright (c) 2020, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import traquent
import traquent.monitor
from traquent.monitor import MONITOR_REDIS_KEY, get_trace_id
from traquent.tests import IntegrationTestCase
from traquent.utils import set_request
from traquent.utils.response import build_response


class TestMonitor(IntegrationTestCase):
	def setUp(self):
		traquent.conf.monitor = 1
		traquent.cache.delete_value(MONITOR_REDIS_KEY)

	def tearDown(self):
		traquent.conf.monitor = 0
		traquent.cache.delete_value(MONITOR_REDIS_KEY)

	def test_enable_monitor(self):
		set_request(method="GET", path="/api/method/traquent.ping")
		response = build_response("json")

		traquent.monitor.start()
		traquent.monitor.stop(response)

		logs = traquent.cache.lrange(MONITOR_REDIS_KEY, 0, -1)
		self.assertEqual(len(logs), 1)

		log = traquent.parse_json(logs[0].decode())
		self.assertTrue(log.duration)
		self.assertTrue(log.site)
		self.assertTrue(log.timestamp)
		self.assertTrue(log.uuid)
		self.assertTrue(log.request)
		self.assertEqual(log.transaction_type, "request")
		self.assertEqual(log.request["method"], "GET")

	def test_no_response(self):
		set_request(method="GET", path="/api/method/traquent.ping")

		traquent.monitor.start()
		traquent.monitor.stop(response=None)

		logs = traquent.cache.lrange(MONITOR_REDIS_KEY, 0, -1)
		self.assertEqual(len(logs), 1)

		log = traquent.parse_json(logs[0].decode())
		self.assertEqual(log.request["status_code"], 500)
		self.assertEqual(log.transaction_type, "request")
		self.assertEqual(log.request["method"], "GET")

	def test_job(self):
		traquent.utils.background_jobs.execute_job(
			traquent.local.site, "traquent.ping", None, None, {}, is_async=False
		)

		logs = traquent.cache.lrange(MONITOR_REDIS_KEY, 0, -1)
		self.assertEqual(len(logs), 1)
		log = traquent.parse_json(logs[0].decode())
		self.assertEqual(log.transaction_type, "job")
		self.assertTrue(log.job)
		self.assertEqual(log.job["method"], "traquent.ping")
		self.assertEqual(log.job["scheduled"], False)
		self.assertEqual(log.job["wait"], 0)

	def test_flush(self):
		set_request(method="GET", path="/api/method/traquent.ping")
		response = build_response("json")
		traquent.monitor.start()
		traquent.monitor.stop(response)

		open(traquent.monitor.log_file(), "w").close()
		traquent.monitor.flush()

		with open(traquent.monitor.log_file()) as f:
			logs = f.readlines()

		self.assertEqual(len(logs), 1)
		log = traquent.parse_json(logs[0])
		self.assertEqual(log.transaction_type, "request")

	def test_trace_ids(self):
		set_request(method="GET", path="/api/method/traquent.ping")
		response = build_response("json")
		traquent.monitor.start()
		traquent.db.sql("select 1")
		self.assertIn(get_trace_id(), str(traquent.db.last_query))
		traquent.monitor.stop(response)
