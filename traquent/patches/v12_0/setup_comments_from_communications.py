import traquent


def execute():
	traquent.reload_doctype("Comment")

	if traquent.db.count("Communication", filters=dict(communication_type="Comment")) > 20000:
		traquent.db.auto_commit_on_many_writes = True

	for comment in traquent.get_all("Communication", fields=["*"], filters=dict(communication_type="Comment")):
		new_comment = traquent.new_doc("Comment")
		new_comment.comment_type = comment.comment_type
		new_comment.comment_email = comment.sender
		new_comment.comment_by = comment.sender_full_name
		new_comment.subject = comment.subject
		new_comment.content = comment.content or comment.subject
		new_comment.reference_doctype = comment.reference_doctype
		new_comment.reference_name = comment.reference_name
		new_comment.link_doctype = comment.link_doctype
		new_comment.link_name = comment.link_name
		new_comment.creation = comment.creation
		new_comment.modified = comment.modified
		new_comment.owner = comment.owner
		new_comment.modified_by = comment.modified_by
		new_comment.db_insert()

	if traquent.db.auto_commit_on_many_writes:
		traquent.db.auto_commit_on_many_writes = False

	# clean up
	traquent.db.delete("Communication", {"communication_type": "Comment"})
