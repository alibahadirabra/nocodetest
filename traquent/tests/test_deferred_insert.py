import traquent
from traquent.deferred_insert import deferred_insert, save_to_db
from traquent.tests import IntegrationTestCase


class TestDeferredInsert(IntegrationTestCase):
	def test_deferred_insert(self):
		route_history = {"route": traquent.generate_hash(), "user": "Administrator"}
		deferred_insert("Route History", [route_history])

		save_to_db()
		self.assertTrue(traquent.db.exists("Route History", route_history))

		route_history = {"route": traquent.generate_hash(), "user": "Administrator"}
		deferred_insert("Route History", [route_history])
		traquent.clear_cache()  # deferred_insert cache keys are supposed to be persistent
		save_to_db()
		self.assertTrue(traquent.db.exists("Route History", route_history))
