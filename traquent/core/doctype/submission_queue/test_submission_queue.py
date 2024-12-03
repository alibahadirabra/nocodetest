# Copyright (c) 2022, traquent Technologies and Contributors
# See license.txt

import time
import typing

import traquent
from traquent.tests import IntegrationTestCase, UnitTestCase, timeout
from traquent.utils.background_jobs import get_queue

if typing.TYPE_CHECKING:
	from rq.job import Job


class UnitTestSubmissionQueue(UnitTestCase):
	"""
	Unit tests for SubmissionQueue.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestSubmissionQueue(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		cls.queue = get_queue(qtype="default")

	@timeout(seconds=20)
	def check_status(self, job: "Job", status, wait=True):
		if wait:
			while True:
				if job.is_queued or job.is_started:
					time.sleep(0.2)
				else:
					break
		self.assertEqual(traquent.get_doc("RQ Job", job.id).status, status)

	def test_queue_operation(self):
		from traquent.core.doctype.doctype.test_doctype import new_doctype
		from traquent.core.doctype.submission_queue.submission_queue import queue_submission

		if not traquent.db.table_exists("Test Submission Queue", cached=False):
			doc = new_doctype("Test Submission Queue", is_submittable=True, queue_in_background=True)
			doc.insert()

		d = traquent.new_doc("Test Submission Queue")
		d.update({"some_fieldname": "Random"})
		d.insert()

		traquent.db.commit()
		queue_submission(d, "submit")
		traquent.db.commit()

		# Waiting for execution
		time.sleep(4)
		submission_queue = traquent.get_last_doc("Submission Queue")

		# Test queueing / starting
		job = self.queue.fetch_job(submission_queue.job_id)
		# Test completion
		self.check_status(job, status="finished")
