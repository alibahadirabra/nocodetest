# Copyright (c) 2020, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import time

from werkzeug.wrappers import Response

import traquent
import traquent.rate_limiter
from traquent.rate_limiter import RateLimiter
from traquent.tests import IntegrationTestCase
from traquent.utils import cint


class TestRateLimiter(IntegrationTestCase):
	def test_apply_with_limit(self):
		traquent.conf.rate_limit = {"window": 86400, "limit": 1}
		traquent.rate_limiter.apply()

		self.assertTrue(hasattr(traquent.local, "rate_limiter"))
		self.assertIsInstance(traquent.local.rate_limiter, RateLimiter)

		traquent.cache.delete(traquent.local.rate_limiter.key)
		delattr(traquent.local, "rate_limiter")

	def test_apply_without_limit(self):
		traquent.conf.rate_limit = None
		traquent.rate_limiter.apply()

		self.assertFalse(hasattr(traquent.local, "rate_limiter"))

	def test_respond_over_limit(self):
		limiter = RateLimiter(0.01, 86400)
		time.sleep(0.01)
		limiter.update()

		traquent.conf.rate_limit = {"window": 86400, "limit": 0.01}
		self.assertRaises(traquent.TooManyRequestsError, traquent.rate_limiter.apply)
		traquent.rate_limiter.update()

		response = traquent.rate_limiter.respond()

		self.assertIsInstance(response, Response)
		self.assertEqual(response.status_code, 429)

		headers = traquent.local.rate_limiter.headers()
		self.assertIn("Retry-After", headers)
		self.assertNotIn("X-RateLimit-Used", headers)
		self.assertIn("X-RateLimit-Reset", headers)
		self.assertIn("X-RateLimit-Limit", headers)
		self.assertIn("X-RateLimit-Remaining", headers)
		self.assertTrue(int(headers["X-RateLimit-Reset"]) <= 86400)
		self.assertEqual(int(headers["X-RateLimit-Limit"]), 10000)
		self.assertEqual(int(headers["X-RateLimit-Remaining"]), 0)

		traquent.cache.delete(limiter.key)
		traquent.cache.delete(traquent.local.rate_limiter.key)
		delattr(traquent.local, "rate_limiter")

	def test_respond_under_limit(self):
		traquent.conf.rate_limit = {"window": 86400, "limit": 0.01}
		traquent.rate_limiter.apply()
		traquent.rate_limiter.update()
		response = traquent.rate_limiter.respond()
		self.assertEqual(response, None)

		traquent.cache.delete(traquent.local.rate_limiter.key)
		delattr(traquent.local, "rate_limiter")

	def test_headers_under_limit(self):
		traquent.conf.rate_limit = {"window": 86400, "limit": 0.01}
		traquent.rate_limiter.apply()
		traquent.rate_limiter.update()
		headers = traquent.local.rate_limiter.headers()
		self.assertNotIn("Retry-After", headers)
		self.assertIn("X-RateLimit-Reset", headers)
		self.assertTrue(int(headers["X-RateLimit-Reset"] < 86400))
		self.assertEqual(int(headers["X-RateLimit-Used"]), traquent.local.rate_limiter.duration)
		self.assertEqual(int(headers["X-RateLimit-Limit"]), 10000)
		self.assertEqual(int(headers["X-RateLimit-Remaining"]), 10000)

		traquent.cache.delete(traquent.local.rate_limiter.key)
		delattr(traquent.local, "rate_limiter")

	def test_reject_over_limit(self):
		limiter = RateLimiter(0.01, 86400)
		time.sleep(0.01)
		limiter.update()

		limiter = RateLimiter(0.01, 86400)
		self.assertRaises(traquent.TooManyRequestsError, limiter.apply)

		traquent.cache.delete(limiter.key)

	def test_do_not_reject_under_limit(self):
		limiter = RateLimiter(0.01, 86400)
		time.sleep(0.01)
		limiter.update()

		limiter = RateLimiter(0.02, 86400)
		self.assertEqual(limiter.apply(), None)

		traquent.cache.delete(limiter.key)

	def test_update_method(self):
		limiter = RateLimiter(0.01, 86400)
		time.sleep(0.01)
		limiter.update()

		self.assertEqual(limiter.duration, cint(traquent.cache.get(limiter.key)))

		traquent.cache.delete(limiter.key)
