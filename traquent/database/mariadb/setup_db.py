import os
import sys

import click

import traquent
from traquent.database.db_manager import DbManager


def get_mariadb_variables():
	return traquent._dict(traquent.db.sql("show variables"))


def get_mariadb_version(version_string: str = ""):
	# MariaDB classifies their versions as Major (1st and 2nd number), and Minor (3rd number)
	# Example: Version 10.3.13 is Major Version = 10.3, Minor Version = 13
	version_string = version_string or get_mariadb_variables().get("version")
	version = version_string.split("-", 1)[0]
	return version.rsplit(".", 1)


def setup_database(force, verbose, mariadb_user_host_login_scope=None):
	traquent.local.session = traquent._dict({"user": "Administrator"})

	db_user = traquent.conf.db_user
	db_name = traquent.local.conf.db_name
	root_conn = get_root_connection()
	dbman = DbManager(root_conn)
	dbman_kwargs = {}

	if mariadb_user_host_login_scope is not None:
		dbman_kwargs["host"] = mariadb_user_host_login_scope

	dbman.create_user(db_user, traquent.conf.db_password, **dbman_kwargs)
	if verbose:
		print(f"Created or updated user {db_user}")

	if force or (db_name not in dbman.get_database_list()):
		dbman.drop_database(db_name)
	else:
		print(f"Database {db_name} already exists, please drop it manually or pass `--force`.")
		sys.exit(1)

	dbman.create_database(db_name)
	if verbose:
		print("Created database %s" % db_name)

	dbman.grant_all_privileges(db_name, db_user, **dbman_kwargs)
	dbman.flush_privileges()
	if verbose:
		print(f"Granted privileges to user {db_user} and database {db_name}")

	# close root connection
	root_conn.close()


def drop_user_and_database(
	db_name,
	db_user,
):
	traquent.local.db = get_root_connection()
	dbman = DbManager(traquent.local.db)
	dbman.drop_database(db_name)
	dbman.delete_user(db_user, host="%")
	dbman.delete_user(db_user)


def bootstrap_database(verbose, source_sql=None):
	import sys

	traquent.connect()
	check_compatible_versions()

	import_db_from_sql(source_sql, verbose)

	traquent.connect()
	if "tabDefaultValue" not in traquent.db.get_tables(cached=False):
		from click import secho

		secho(
			"Table 'tabDefaultValue' missing in the restored site. "
			"Database not installed correctly, this can due to lack of "
			"permission, or that the database name exists. Check your mysql"
			" root password, validity of the backup file or use --force to"
			" reinstall",
			fg="red",
		)
		sys.exit(1)


def import_db_from_sql(source_sql=None, verbose=False):
	if verbose:
		print("Starting database import...")
	db_name = traquent.conf.db_name
	if not source_sql:
		source_sql = os.path.join(os.path.dirname(__file__), "framework_mariadb.sql")
	DbManager(traquent.local.db).restore_database(
		verbose, db_name, source_sql, traquent.conf.db_user, traquent.conf.db_password
	)
	if verbose:
		print("Imported from database %s" % source_sql)


def check_compatible_versions():
	try:
		version = get_mariadb_version()
		version_tuple = tuple(int(v) for v in version[0].split("."))

		if version_tuple < (10, 6):
			click.secho(
				f"Warning: MariaDB version {version} is less than 10.6 which is not supported by traquent",
				fg="yellow",
			)
		elif version_tuple >= (10, 9):
			click.secho(
				f"Warning: MariaDB version {version} is more than 10.8 which is not yet tested with traquent Framework.",
				fg="yellow",
			)
	except Exception:
		click.secho(
			"MariaDB version compatibility checks failed, make sure you're running a supported version.",
			fg="yellow",
		)


def get_root_connection():
	if not traquent.local.flags.root_connection:
		from getpass import getpass

		if not traquent.flags.root_login:
			traquent.flags.root_login = (
				traquent.conf.get("root_login") or input("Enter mysql super user [root]: ") or "root"
			)

		if not traquent.flags.root_password:
			traquent.flags.root_password = traquent.conf.get("root_password") or getpass("MySQL root password: ")

		traquent.local.flags.root_connection = traquent.database.get_db(
			socket=traquent.conf.db_socket,
			host=traquent.conf.db_host,
			port=traquent.conf.db_port,
			user=traquent.flags.root_login,
			password=traquent.flags.root_password,
			cur_db_name=None,
		)

	return traquent.local.flags.root_connection
