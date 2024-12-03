import os
import re

import traquent
from traquent.database.db_manager import DbManager
from traquent.utils import cint


def setup_database():
	root_conn = get_root_connection()
	root_conn.commit()
	root_conn.sql("end")
	root_conn.sql(f'DROP DATABASE IF EXISTS "{traquent.conf.db_name}"')

	# If user exists, just update password
	if root_conn.sql(f"SELECT 1 FROM pg_roles WHERE rolname='{traquent.conf.db_user}'"):
		root_conn.sql(f"ALTER USER \"{traquent.conf.db_user}\" WITH PASSWORD '{traquent.conf.db_password}'")
	else:
		root_conn.sql(f"CREATE USER \"{traquent.conf.db_user}\" WITH PASSWORD '{traquent.conf.db_password}'")
	root_conn.sql(f'CREATE DATABASE "{traquent.conf.db_name}"')
	root_conn.sql(f'GRANT ALL PRIVILEGES ON DATABASE "{traquent.conf.db_name}" TO "{traquent.conf.db_user}"')
	if psql_version := root_conn.sql("SHOW server_version_num", as_dict=True):
		semver_version_num = psql_version[0].get("server_version_num") or "140000"
		if cint(semver_version_num) > 150000:
			root_conn.sql(f'ALTER DATABASE "{traquent.conf.db_name}" OWNER TO "{traquent.conf.db_user}"')
	root_conn.close()


def bootstrap_database(verbose, source_sql=None):
	traquent.connect()
	import_db_from_sql(source_sql, verbose)

	traquent.connect()
	if "tabDefaultValue" not in traquent.db.get_tables():
		import sys

		from click import secho

		secho(
			"Table 'tabDefaultValue' missing in the restored site. "
			"This may be due to incorrect permissions or the result of a restore from a bad backup file. "
			"Database not installed correctly.",
			fg="red",
		)
		sys.exit(1)


def import_db_from_sql(source_sql=None, verbose=False):
	if verbose:
		print("Starting database import...")
	db_name = traquent.conf.db_name
	if not source_sql:
		source_sql = os.path.join(os.path.dirname(__file__), "framework_postgres.sql")
	DbManager(traquent.local.db).restore_database(
		verbose, db_name, source_sql, traquent.conf.db_user, traquent.conf.db_password
	)
	if verbose:
		print("Imported from database %s" % source_sql)


def get_root_connection():
	if not traquent.local.flags.root_connection:
		from getpass import getpass

		if not traquent.flags.root_login:
			traquent.flags.root_login = (
				traquent.conf.get("root_login") or input("Enter postgres super user [postgres]: ") or "postgres"
			)

		if not traquent.flags.root_password:
			traquent.flags.root_password = traquent.conf.get("root_password") or getpass(
				"Postgres super user password: "
			)

		traquent.local.flags.root_connection = traquent.database.get_db(
			socket=traquent.conf.db_socket,
			host=traquent.conf.db_host,
			port=traquent.conf.db_port,
			user=traquent.flags.root_login,
			password=traquent.flags.root_password,
			cur_db_name=traquent.flags.root_login,
		)

	return traquent.local.flags.root_connection


def drop_user_and_database(db_name, db_user):
	root_conn = get_root_connection()
	root_conn.commit()
	root_conn.sql(
		"SELECT pg_terminate_backend (pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = %s",
		(db_name,),
	)
	root_conn.sql("end")
	root_conn.sql(f"DROP DATABASE IF EXISTS {db_name}")
	root_conn.sql(f"DROP USER IF EXISTS {db_user}")
