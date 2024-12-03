import traquent


def execute():
	traquent.reload_doctype("Comment")

	if traquent.db.count("Feedback") > 20000:
		traquent.db.auto_commit_on_many_writes = True

	for feedback in traquent.get_all("Feedback", fields=["*"]):
		if feedback.like:
			new_comment = traquent.new_doc("Comment")
			new_comment.comment_type = "Like"
			new_comment.comment_email = feedback.owner
			new_comment.content = "Liked by: " + feedback.owner
			new_comment.reference_doctype = feedback.reference_doctype
			new_comment.reference_name = feedback.reference_name
			new_comment.creation = feedback.creation
			new_comment.modified = feedback.modified
			new_comment.owner = feedback.owner
			new_comment.modified_by = feedback.modified_by
			new_comment.ip_address = feedback.ip_address
			new_comment.db_insert()

	if traquent.db.auto_commit_on_many_writes:
		traquent.db.auto_commit_on_many_writes = False

	# clean up
	traquent.db.delete("Feedback")
	traquent.db.commit()

	traquent.delete_doc("DocType", "Feedback")
