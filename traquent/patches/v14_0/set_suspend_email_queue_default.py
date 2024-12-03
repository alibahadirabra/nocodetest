import traquent
from traquent.cache_manager import clear_defaults_cache


def execute():
	traquent.db.set_default(
		"suspend_email_queue",
		traquent.db.get_default("hold_queue", "Administrator") or 0,
		parent="__default",
	)

	traquent.db.delete("DefaultValue", {"defkey": "hold_queue"})
	clear_defaults_cache()
