import traquent

traquent_CLOUD_DOMAINS = ("traquent.cloud", "traquent.com", "traquenthr.com")


def on_traquentcloud() -> bool:
	"""Returns true if running on traquent Cloud.


	Useful for modifying few features for better UX."""
	return traquent.local.site.endswith(traquent_CLOUD_DOMAINS)
