import traquent
import traquent.share


def execute():
	for user in traquent.STANDARD_USERS:
		traquent.share.remove("User", user, user)
