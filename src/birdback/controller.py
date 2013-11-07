import view
import model

import scandir
import time
import os
import sys
import shelve
import asyncore
import getpass

import pyinotify

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
		watch = pyinotify.WatchManager()
		watchedEvents = pyinotify.IN_DELETE | pyinotify.IN_CREATE

		class BackupMediaDetector(pyinotify.ProcessEvent):
			def process_IN_CREATE(self, event):
				pass

			def process_IN_DELETE(self, event):
				pass
		
		notifier = pyinotify.AsyncNotifier(watch, BackupMediaDetector())
		backupMediaWatch = watch.add_watch('/media/' + getpass.getuser(), watchedEvents, rec=True)
	
	def run(self):		
		# Instantiate the view (menu bar)
		# -------------------------------
		self.view = view.View(self)
		
		# Start doing stuff
		# -----------------
		asyncore.loop()
	
	def quit(self, code=0):
		self.preferences.close()
		os.unlink(self.pidfile)
		sys.exit(code)
