"""
Run this after updating country_info.json and or
"""
import traquent


def execute():
	for col in ("field", "doctype"):
		traquent.db.sql_ddl(f"alter table `tabSingles` modify column `{col}` varchar(255)")
