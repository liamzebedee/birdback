import shelve

class BackupMedium(object):
	def __init__(self, path):
		self.path = path
		self.name = path.split('/').pop()

class Preferences(object):
	def __init__(self, path):
		self.shelve = shelve.open(path, writeback=True)
		if 'excluded_files' not in self.shelve or self.shelve['excluded_files'] is None:
			self.shelve['excluded_files'] = []
		self.excluded_files = self.shelve["excluded_files"]
	
	def sync(self):
		self.shelve["excluded_files"] = self.excluded_files
		self.shelve.sync()
	
	def close(self):
		self.shelve.close()
