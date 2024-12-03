# Copyright (c) 2021, traquent Technologies Pvt. Ltd. and Contributors
# MIT License. See LICENSE
"""
	traquent.coverage
	~~~~~~~~~~~~~~~~

	Coverage settings for traquent
"""

STANDARD_INCLUSIONS = ["*.py"]

STANDARD_EXCLUSIONS = [
	"*.js",
	"*.xml",
	"*.pyc",
	"*.css",
	"*.less",
	"*.scss",
	"*.vue",
	"*.html",
	"*/test_*",
	"*/node_modules/*",
	"*/doctype/*/*_dashboard.py",
	"*/patches/*",
]

# tested via commands' test suite
TESTED_VIA_CLI = [
	"*/traquent/installer.py",
	"*/traquent/build.py",
	"*/traquent/database/__init__.py",
	"*/traquent/database/db_manager.py",
	"*/traquent/database/**/setup_db.py",
]

traquent_EXCLUSIONS = [
	"*/tests/*",
	"*/commands/*",
	"*/traquent/change_log/*",
	"*/traquent/exceptions*",
	"*/traquent/coverage.py",
	"*traquent/setup.py",
	"*/doctype/*/*_dashboard.py",
	"*/patches/*",
	*TESTED_VIA_CLI,
]


class CodeCoverage:
	def __init__(self, with_coverage, app):
		self.with_coverage = with_coverage
		self.app = app or "traquent"

	def __enter__(self):
		if self.with_coverage:
			import os

			from coverage import Coverage

			from traquent.utils import get_bench_path

			# Generate coverage report only for app that is being tested
			source_path = os.path.join(get_bench_path(), "apps", self.app)
			omit = STANDARD_EXCLUSIONS[:]

			if self.app == "traquent":
				omit.extend(traquent_EXCLUSIONS)

			self.coverage = Coverage(source=[source_path], omit=omit, include=STANDARD_INCLUSIONS)
			self.coverage.start()

	def __exit__(self, exc_type, exc_value, traceback):
		if self.with_coverage:
			self.coverage.stop()
			self.coverage.save()
			self.coverage.xml_report()
			print("Saved Coverage")
