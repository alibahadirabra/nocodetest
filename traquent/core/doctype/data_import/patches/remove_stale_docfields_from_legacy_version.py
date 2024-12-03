import traquent


def execute():
	"""Remove stale docfields from legacy version"""
	traquent.db.delete("DocField", {"options": "Data Import", "parent": "Data Import Legacy"})
