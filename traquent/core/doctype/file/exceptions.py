import traquent


class MaxFileSizeReachedError(traquent.ValidationError):
	pass


class FolderNotEmpty(traquent.ValidationError):
	pass


class FileTypeNotAllowed(traquent.ValidationError):
	pass


from traquent.exceptions import *
