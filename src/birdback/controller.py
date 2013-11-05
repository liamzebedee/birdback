import view
import model

import scandir
import time
import os
import sys
import shelve
	
class Controller(object):
	def __init__(self):
		self.pidfile = os.path.expanduser("~/.birdback.pid")
		
		# Check that birdback isn't already running
		# -----------------------------------------
		pid = os.getpid()
		
		running = False # Innocent...
		if os.path.isfile(self.pidfile):
			try:
				oldpid = int(open(self.pidfile).readline().rstrip())
				try:
					os.kill(oldpid, 0)
					running = True # ...until proven guilty
				except OSError as err:
					if err.errno == os.errno.ESRCH:
						# OSError: [Errno 3] No such process
						print("stale pidfile, old pid: ", oldpid)
			except ValueError:
				# Corrupt pidfile, empty or not an int on first line
				pass
		if running:
			print("birdback is already running, exiting")
			sys.exit()
		else:
			open(self.pidfile, 'w').write("%d\n" % pid)
		
		# Load preferences from disk
		# --------------------------
		preferencePath = os.path.expanduser("~") + os.sep + ".local" + os.sep + "share" + os.sep + 'birdback'
		self.preferences = shelve.open(preferencePath)
		
		# Instantiate file system watchers
		# --------------------------------
		
		# Instantiate the view (menu bar)
		# -------------------------------
		self.view = view.View(self)
	
	def quit(self, code=0):
		self.preferences.close()
		os.unlink(self.pidfile)
		sys.exit(code)
