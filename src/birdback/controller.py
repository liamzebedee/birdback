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
import glob

import pyinotify
from gi.repository import Gtk
from gi.repository import GObject

GObject.threads_init()

class Controller(object):
	def __init__(self):
		self.backupMediums = {}
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
		
		class BackupMediaDetector(pyinotify.ProcessEvent):
			def __init__(self, controller):
				self.controller = controller
			
			def process_IN_CREATE(self, event):
				path = event.pathname
				if path.startswith('/dev/disk/by-id/usb'):
					# Try to automatically mount it
					devicePath = os.path.realpath("/dev/disk/by-id/"+os.readlink(path))
					try:
						subprocess.check_output(['udisks', '--mount', devicePath])
					except:
						print('Error while mounting path: '+path)
					return
				else:
					# /media/disk is mounted erronously when I run udisks on a bad path
					# The easiest thing to do is ignore /media/disk
					if path == '/media/disk': return
					print('HDD/USB inserted at: ' + path)
					if path not in self.controller.backupMediums:
						self.controller.backupMediums[path] = model.BackupMedium(path)
					self.controller.view.drive_inserted(self.controller.backupMediums[path])

			def process_IN_DELETE(self, event):
				path = event.pathname
				if path == '/media/disk': return
				print('HDD/USB removed at: ' + path)
				if path in self.controller.backupMediums:
					self.controller.view.drive_removed(self.controller.backupMediums[path])
					del self.controller.backupMediums[path]
		
		self.backupMediaWatcher = pyinotify.ThreadedNotifier(watchManager, BackupMediaDetector(self))
		self.backupMediaWatcher.start()
		
		watchManager.add_watch('/media/', pyinotify.IN_DELETE | pyinotify.IN_CREATE, rec=False)
		watchManager.add_watch('/dev/disk/by-id/', pyinotify.IN_CREATE, rec=False)
		print("Added watch for USB/HDDs")
	
	def run(self):		
		# Instantiate the view (menu bar)
		# -------------------------------
		self.view = view.View(self)
		print("View instantiated")
		
		# Detect existing HDDs/USBs
		# -------------------------
		os.chdir("/dev/disk/by-id")
		try:
			for path in glob.glob("usb*"):
				# Try to automatically mount it
				devicePath = os.path.realpath("/dev/disk/by-id/"+os.readlink(path))
				mounts = open("/proc/mounts")
				for line in mounts:
					parts = line.split(' ')
					if parts[0] == devicePath and parts[1].startswith('/media'):
						path = parts[1]
						self.backupMediums[path] = model.BackupMedium(path)
						self.view.drive_inserted(self.backupMediums[path])
				mounts.close()
		except:
			print('Error while detecting existing HDDs/USBs: '+path)
	
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
	
	def backup(self, backupMedium, progress_callback):
		progress_callback("scanning changed files")
		filesToBackup = []
		progress_callback("scanning changed documents")
		filesToBackup.extend(self.home_files_to_backup(backupMedium))
		#progress_callback("scanning changed configuration")
		#filesToBackup.append(self.etc_files_to_backup(backupMedium))
	
	def home_files_to_backup(self, backupMedium):
		BACKUP_PATH = os.path.expanduser("~")
		EXCLUDES = [
			'.cache',
			'.ccache',
			'Downloads',
			'tmp'
		]
		
		filesToBackup = []
		
		for root, dirs, files in scandir.walk(BACKUP_PATH, topdown=True):
			# Common excludes
			dirs = [d for d in dirs if d not in EXCLUDES]
			
			# Special excludes
			if root == (os.path.join(BACKUP_PATH + '.local/share')):
				if 'Trash' in dirs: dirs.remove('Trash')
			
			if not os.path.exists(os.path.join(backupMedium.path, root[1:])):
				for f in files:
					filesToBackup.append(os.path.join(root, f))
			else:
				for f in files:
					absolute_file = os.path.join(root, f)
					try:
						if os.path.getmtime(absolute_file) > os.path.getmtime(os.path.join(backupMedium.path, absolute_file[1:])):
							filesToBackup.append(f)
					except OSError as e:
						print(e)
			
		return filesToBackup
		
	def etc_files_to_backup(self, backupMedium):
		BACKUP_PATH = '/etc'
		filesToBackup = []
		
		for root, dirs, files in scandir.walk(BACKUP_PATH, topdown=False):
			for f in files:
				if os.path.getmtime(f) > backupMedium.getmtime(f):
						filesToBackup.append(f)
		
		return filesToBackup
