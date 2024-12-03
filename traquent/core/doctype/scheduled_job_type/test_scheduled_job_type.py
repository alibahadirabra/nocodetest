# Copyright (c) 2019, traquent Technologies and Contributors
# License: MIT. See LICENSE
from datetime import timedelta

import traquent
from traquent.core.doctype.scheduled_job_type.scheduled_job_type import sync_jobs
from traquent.tests import IntegrationTestCase, UnitTestCase
from traquent.utils import get_datetime
from traquent.utils.data import now_datetime


class UnitTestScheduledJobType(UnitTestCase):
	"""
	Unit tests for ScheduledJobType.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestScheduledJobType(IntegrationTestCase):
	def setUp(self):
		traquent.db.rollback()
		traquent.db.truncate("Scheduled Job Type")
		sync_jobs()
		traquent.db.commit()

	def test_throws_on_duplicate_job(self):
		job_config = dict(
			doctype="Scheduled Job Type",
			method="traquent.desk.notifications.clear_notifications",
			frequency="Weekly",
		)
		traquent.get_doc(job_config).insert()

		duplicate_job = traquent.get_doc(job_config)

		self.assertRaises(Exception, duplicate_job.insert)
		traquent.db.rollback()

	def test_throws_on_duplicate_job_with_cron_format(self):
		job_config = dict(
			doctype="Scheduled Job Type",
			method="traquent.desk.notifications.clear_notifications",
			frequency="Cron",
			cron_format="*/1 * * * *",
		)
		traquent.get_doc(job_config).insert()

		duplicate_job = traquent.get_doc(job_config)

		self.assertRaises(Exception, duplicate_job.insert)
		traquent.db.rollback()

	def test_sync_jobs(self):
		all_job = traquent.get_doc("Scheduled Job Type", dict(method="traquent.email.queue.flush"))
		self.assertEqual(all_job.frequency, "All")

		daily_job = traquent.get_doc(
			"Scheduled Job Type", dict(method="traquent.desk.notifications.clear_notifications")
		)
		self.assertEqual(daily_job.frequency, "Daily")

		# check if cron jobs are synced
		cron_job = traquent.get_doc("Scheduled Job Type", dict(method="traquent.oauth.delete_oauth2_data"))
		self.assertEqual(cron_job.frequency, "Cron")
		self.assertEqual(cron_job.cron_format, "0/15 * * * *")

		# check if jobs are synced after change in hooks
		updated_scheduler_events = {"hourly": ["traquent.email.queue.flush"]}
		sync_jobs(updated_scheduler_events)
		updated_scheduled_job = traquent.get_doc("Scheduled Job Type", {"method": "traquent.email.queue.flush"})
		self.assertEqual(updated_scheduled_job.frequency, "Hourly")

	def test_daily_job(self):
		job = traquent.get_doc(
			"Scheduled Job Type", dict(method="traquent.desk.notifications.clear_notifications")
		)
		job.db_set("last_execution", "2019-01-01 00:00:00")
		self.assertTrue(job.is_event_due(get_datetime("2019-01-02 00:00:06")))
		self.assertFalse(job.is_event_due(get_datetime("2019-01-01 00:00:06")))
		self.assertFalse(job.is_event_due(get_datetime("2019-01-01 23:59:59")))

	def test_weekly_job(self):
		job = traquent.get_doc(
			"Scheduled Job Type",
			dict(method="traquent.social.doctype.energy_point_log.energy_point_log.send_weekly_summary"),
		)
		job.db_set("last_execution", "2019-01-01 00:00:00")
		self.assertTrue(job.is_event_due(get_datetime("2019-01-06 00:10:01")))  # +10 min because of jitter
		self.assertFalse(job.is_event_due(get_datetime("2019-01-02 00:00:06")))
		self.assertFalse(job.is_event_due(get_datetime("2019-01-05 23:59:59")))

	def test_monthly_job(self):
		job = traquent.get_doc(
			"Scheduled Job Type",
			dict(method="traquent.email.doctype.auto_email_report.auto_email_report.send_monthly"),
		)
		job.db_set("last_execution", "2019-01-01 00:00:00")
		self.assertTrue(job.is_event_due(get_datetime("2019-02-01 00:00:01")))
		self.assertFalse(job.is_event_due(get_datetime("2019-01-15 00:00:06")))
		self.assertFalse(job.is_event_due(get_datetime("2019-01-31 23:59:59")))

	def test_cron_job(self):
		# runs every 15 mins
		job = traquent.get_doc("Scheduled Job Type", dict(method="traquent.oauth.delete_oauth2_data"))
		job.db_set("last_execution", "2019-01-01 00:00:00")
		self.assertEqual(job.next_execution, get_datetime("2019-01-01 00:15:00"))
		self.assertTrue(job.is_event_due(get_datetime("2019-01-01 00:15:01")))
		self.assertFalse(job.is_event_due(get_datetime("2019-01-01 00:05:06")))
		self.assertFalse(job.is_event_due(get_datetime("2019-01-01 00:14:59")))

	def test_cold_start(self):
		now = now_datetime()
		just_before_12_am = now.replace(hour=11, minute=59, second=30)
		just_after_12_am = now.replace(hour=0, minute=0, second=30) + timedelta(days=1)

		job = traquent.new_doc("Scheduled Job Type")
		job.frequency = "Daily"
		job.set_user_and_timestamp()

		with self.freeze_time(just_before_12_am):
			self.assertFalse(job.is_event_due())

		with self.freeze_time(just_after_12_am):
			self.assertTrue(job.is_event_due())
