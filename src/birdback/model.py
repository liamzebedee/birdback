import shelve

class BackupMedium(object):
	def __init__(self, path):
		self.path = path
		self.name = path.split('/').pop()

class Preferences(object):
	def __init__(self, path):
		self.shelf = shelve.open(path, writeback=True)
		
	def close(self):
		self.shelf.close()
