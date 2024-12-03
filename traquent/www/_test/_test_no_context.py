import traquent


# no context object is accepted
def get_context():
	context = traquent._dict()
	context.body = "Custom Content"
	return context
