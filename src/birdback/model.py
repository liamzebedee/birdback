class BackupMedium(object):
	def __init__(self, path):
		self.path = path
		self.name = path.split('/').pop()
