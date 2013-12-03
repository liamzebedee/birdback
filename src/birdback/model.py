class BackupMedium(object):
	def __init__(self, path):
		self.path = path
		self.name = path.split('/media/').pop()

class Preferences(object):
	def __init__(self):
		pass
