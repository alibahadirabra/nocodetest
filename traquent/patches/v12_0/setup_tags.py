import traquent


def execute():
	traquent.delete_doc_if_exists("DocType", "Tag Category")
	traquent.delete_doc_if_exists("DocType", "Tag Doc Category")

	traquent.reload_doc("desk", "doctype", "tag")
	traquent.reload_doc("desk", "doctype", "tag_link")

	tag_list = []
	tag_links = []
	time = traquent.utils.get_datetime()

	for doctype in traquent.get_list("DocType", filters={"istable": 0, "issingle": 0, "is_virtual": 0}):
		if not traquent.db.count(doctype.name) or not traquent.db.has_column(doctype.name, "_user_tags"):
			continue

		for _user_tags in traquent.db.sql(
			f"select `name`, `_user_tags` from `tab{doctype.name}`", as_dict=True
		):
			if not _user_tags.get("_user_tags"):
				continue

			for tag in _user_tags.get("_user_tags").split(",") if _user_tags.get("_user_tags") else []:
				if not tag:
					continue

				tag_list.append((tag.strip(), time, time, "Administrator"))

				tag_link_name = traquent.generate_hash(length=10)
				tag_links.append(
					(tag_link_name, doctype.name, _user_tags.name, tag.strip(), time, time, "Administrator")
				)

	traquent.db.bulk_insert(
		"Tag",
		fields=["name", "creation", "modified", "modified_by"],
		values=set(tag_list),
		ignore_duplicates=True,
	)
	traquent.db.bulk_insert(
		"Tag Link",
		fields=["name", "document_type", "document_name", "tag", "creation", "modified", "modified_by"],
		values=set(tag_links),
		ignore_duplicates=True,
	)
