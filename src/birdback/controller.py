import view
import model

import scandir
import time
import os
import os.path
import sys
import shelve
import getpass
import subprocess
import locale

import pyinotify
from gi.repository import Gtk
from gi.repository import GObject

GObject.threads_init()

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
			print("pidfile updated")
			
		# Load preferences from disk
		# --------------------------
		preferencePath = os.path.expanduser("~") + os.sep + ".local" + os.sep + "share" + os.sep + 'birdback'
		self.preferences = shelve.open(preferencePath)
		print("Preferences loaded")
		
		# Instantiate file system watchers
		# --------------------------------
		watchManager = pyinotify.WatchManager()
		watchedEvents = pyinotify.IN_DELETE | pyinotify.IN_CREATE
		
		class BackupMediaDetector(pyinotify.ProcessEvent):
			def __init__(self, controller):
				self.controller = controller
			
			@staticmethod
			def getMediaPath(path):
				encoding = locale.getdefaultlocale()[1]
				
				# Example:
				# /dev/sdb1 on /media/liamzebedee/B42D-AB95 type vfat (foo,foo)
				devicePath = os.path.realpath("/dev/disk/by-id/"+os.readlink(path))
				
				for line in subprocess.check_output(['mount', '-l']).decode(encoding).split('\n'):
					parts = line.split(' ')
					# I hardcode a rule that the mount path must be under /media/xxx because 
					# that's the only path I'm sure that a USB would be mounted on
					if parts[0] == devicePath and parts[2].startswith('/media'):
						return parts[2]
				
				return None
			
			def process_IN_CREATE(self, event):
				if event.pathname.startswith('/dev/disk/by-id/usb'):
					import time
					time.sleep(1)
					# We have to wait for the USB to be mounted
					# XXX HACK replace with something better
					devDir = self.getMediaPath(event.pathname)
					if devDir is None: return
					print('USB detected at: ' + devDir)
				elif event.pathname.startswith('/dev/disk/by-label'):
					print('HDD detected at: ' + event.pathname)
					self.controller.view.driveInserted(event)

			def process_IN_DELETE(self, event):
				if event.pathname.startswith('/dev/disk/by-id/usb'):
					print('USB removed at: ' + event.pathname)
				elif event.pathname.startswith('/dev/disk/by-label'):
					print('HDD removed at: ' + event.pathname)				
		
		self.backupMediaWatcher = pyinotify.ThreadedNotifier(watchManager, BackupMediaDetector(self))
		self.backupMediaWatcher.start()
		watchManager.add_watch('/dev/disk/by-label/', watchedEvents, rec=True)
		watchManager.add_watch('/dev/disk/by-id/', watchedEvents, rec=True)
		print("Added watch for USB/HDDs")
	
	def run(self):		
		# Instantiate the view (menu bar)
		# -------------------------------
		self.view = view.View(self)
		print("View instantiated")
		
		# Start doing stuff
		# -----------------
		print("Running main loop")
		Gtk.main()
	
	def quit(self, code=0):
		print("Quitting...")
		try:
			self.backupMediaWatcher.stop()
			Gtk.main_quit()
			self.preferences.close()
		except Exception as e:
			print("Exception while quitting:")
			print(e)
		
		# DO NOT CHANGE THE ORDER OF CALLS BELOW
		try:
			os.remove(self.pidfile)
		except OSError:
			pass
