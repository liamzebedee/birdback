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
import shutil
import errno

import logging

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
		preferencePath = os.path.join(os.path.expanduser("~"), ".local", "share", 'birdback')
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
						# We use udisksctl here because it mounts to /media/USERNAME/XXX instead of simply /media/XXX
						subprocess.check_output(['udisksctl', 'mount', '--block-device', devicePath])
					except:
						print('Error while mounting path: '+path)
					return
				else:
					print('HDD/USB inserted at: ' + path)
					if path not in self.controller.backupMediums:
						self.controller.backupMediums[path] = model.BackupMedium(path)
					self.controller.view.drive_inserted(self.controller.backupMediums[path])

			def process_IN_DELETE(self, event):
				path = event.pathname
				print('HDD/USB removed at: ' + path)
				if path in self.controller.backupMediums:
					self.controller.view.drive_removed(self.controller.backupMediums[path])
					del self.controller.backupMediums[path]
		
		self.backupMediaWatcher = pyinotify.ThreadedNotifier(watchManager, BackupMediaDetector(self))
		self.backupMediaWatcher.start()
		
		watchManager.add_watch(os.path.join('/media', getpass.getuser()), pyinotify.IN_DELETE | pyinotify.IN_CREATE, rec=False)
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
					if parts[0] == devicePath and parts[1].startswith(os.path.join('/media', getpass.getuser())):
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
	
	def signal_exit(self, _0, _1):
		self.quit()
	
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
		filesToBackup = []
		
		# progress_callback("x/4 backing up installed programs/packages")
		# dpkg --get-selections > ~/Package.list
		# cp /etc/apt/sources.list ~/sources.list
		# apt-key exportall > ~/Repo.keys
		
		progress_callback("1/3 deleting old files from backup")
		self.deleteOldFiles(backupMedium, progress_callback)
		
		# If backup device was removed while old files were being deleted in deleteOldFiles, then the directory walk just exits, which is why I test here
		if not os.path.exists(backupMedium.path):
			raise Exception("Backup device was removed")
		
		progress_callback("2/3 scanning documents")
		filesToBackup.extend(self.home_files_to_backup(backupMedium, progress_callback))
				
		progress_callback("3/3 backing up")
		for i, src_file in enumerate(filesToBackup):
			progress = float(i / len(filesToBackup))
			progress_callback("3/3 backing up ({0:.1f}%)".format(100*progress), log=False)
			
			dst_dir = os.path.join(backupMedium.path, os.path.dirname(src_file[1:]))
			try:
				os.makedirs(dst_dir, exist_ok=True)
				shutil.copy2(src_file, dst_dir, follow_symlinks=False)
			except OSError as e:
				if e.errno == errno.ENXIO:
					# XXX I have no friggin' idea what this is or means
					# Pops up sometimes for GNOME temp files in .local, I don't really care
					print("ENXIO for "+src_file)
					continue
			except Exception as e:
				if not os.path.exists(backupMedium.path):
					raise Exception("Backup device was removed")
				elif not os.path.exists(src_file):
					print("[{0}]: not backing up because file doesn't exist - {1}".format(backupMedium.name, src_file))
					continue
				else:
					# Something else failed like:
					#  - backup medium has no space left
					#  - we couldn't create the directory on the backup medium
					#  - we couldn't copy the file over
					raise e
		
		progress_callback("backup complete")
		
	
	def home_files_to_backup(self, backupMedium, progress_callback):
		BACKUP_PATH = os.path.expanduser("~")
		EXCLUDES = [
			'.cache',
			'.ccache',
			'Downloads',
			'tmp'
		]
		
		filesToBackup = []
		filesProcessed = 0
		
		for root, dirs, files in scandir.walk(BACKUP_PATH, topdown=True):
			if not os.path.exists(backupMedium.path):
				raise Exception("Backup device was removed")
			
			# Common excludes
			if root == BACKUP_PATH:
				dirs[:] = [d for d in dirs if d not in EXCLUDES]
			
			# Special excludes
			if root == (os.path.join(BACKUP_PATH, '.local/share')):
				if 'Trash' in dirs: dirs.remove('Trash')
			
			if not os.path.exists(os.path.join(backupMedium.path, root[1:])):
				for f in files:
					filesProcessed += 1
					progress_callback("2/3 scanning documents ({0} processed)".format(filesProcessed), log=False)
					filesToBackup.append(os.path.join(root, f))
			else:
				for f in files:
					filesProcessed += 1
					progress_callback("2/3 scanning documents ({0} processed)".format(filesProcessed), log=False)
										
					absolute_file = os.path.join(root, f)
					remote_mtime = -1
					try: 
						remote_mtime = os.path.getmtime(os.path.join(backupMedium.path, absolute_file[1:]))
					except:
						pass
					try:
						if os.path.getmtime(absolute_file) > remote_mtime:
							filesToBackup.append(absolute_file)
					except OSError as e:
						pass
			
		return filesToBackup
	
	def deleteOldFiles(self, backupMedium, progress_callback):
		filesProcessed = 0		
		
		PATH = os.path.expanduser("~")
		for root, dirs, files in scandir.walk(os.path.join(backupMedium.path, PATH[1:]), topdown=True):
			for d in dirs:
				absolute_path = os.path.join(root, d)
				if not os.path.exists('/'+os.path.relpath(absolute_path,backupMedium.path)):
					try:
						shutil.rmtree(absolute_path)
					except:
						pass
			
			for f in files:
				filesProcessed += 1
				progress_callback("1/3 deleting old files from backup ({0} processed)".format(filesProcessed), log=False)
				
				absolute_file = os.path.join(root, f)
				
				if not os.path.exists('/'+os.path.relpath(absolute_file, backupMedium.path)):
					try:
						os.remove(absolute_file)
					except:
						pass








