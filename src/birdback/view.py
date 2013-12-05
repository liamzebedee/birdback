from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify
import os

class View(object):
	QUIT_ICON = '/usr/share/icons/Humanity/actions/128/process-stop.svg'
	ACTIVE_ICON = '/usr/local/share/icons/hicolor/scalable/apps/birdback.svg'
	ATTENTION_ICON = '/usr/local/share/icons/hicolor/scalable/apps/birdback-active.svg'
	DO_BACKUP_ICON = '/usr/share/icons/Humanity/actions/48/forward.svg'
	
	def __init__(self, controller):
		self.controller = controller
		# See http://developer.ubuntu.com/api/devel/ubuntu-13.10/python/AppIndicator3-0.1.html
		self.indicator = appindicator.Indicator.new(
		  "birdback-indicator",
		  "birdback",
		  appindicator.IndicatorCategory.APPLICATION_STATUS)
		self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
		self.indicator.set_icon(View.ACTIVE_ICON)
		self.indicator.set_attention_icon(View.ATTENTION_ICON)
		self.indicate_bliss()
		self.menu = self.create_menu()
		self.indicator.set_menu(self.menu)
		Notify.init('birdback')
		self.backupControls = {}
	
	def indicate_activity(self):
		self.indicator.set_status(appindicator.IndicatorStatus.ATTENTION)
	
	def indicate_bliss(self):
		self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
	
	def add_menu_item(self, label, handler, event="activate", MenuItem=Gtk.MenuItem, show=True):
		item = MenuItem(label)
		item.connect(event, handler)
		self.menu.append(item)
		if show:
			item.show()
		return item
	
	def add_image_menu_item(self, label, handler, imgPath, event="activate", show=True):
		img = Gtk.Image()
		img.set_from_file(imgPath)
		item = Gtk.ImageMenuItem(label)
		item.set_image(img)
		item.connect(event, handler)
		self.menu.append(item)
		item.show()
		return item
	
	def create_menu(self):
		self.menu = Gtk.Menu()
		self.menu.show_all()
		
		self.add_image_menu_item('Quit', self.quit, View.QUIT_ICON)
		
		return self.menu
	
	# I don't know why I have to do this. But it works.
	def update_view(self):
		while Gtk.events_pending():
			Gtk.main_iteration_do(False)
	
	def show_notification(self, message):
		n = Notify.Notification.new('BirdBack', message, None)
		n.show()
	
	def drive_inserted(self, backupMedium):
		self.show_notification("Drive inserted: "+backupMedium.path)
		
		def default_backup_label():
			return "Backup "+backupMedium.name
		def backup(x):
			print("Starting backup of " + backupMedium.path)
			menuItem = self.backupControls[backupMedium.path]
			menuItem.set_sensitive(False)
			self.indicate_activity()
			self.update_view()
			
			def progress_callback(progress):
				menuItem.set_label("Backing up {0} ({1})".format(backupMedium.name, progress))
				print("backup "+backupMedium.name+": "+progress)
				self.update_view()
			try:
				self.controller.backup(backupMedium, progress_callback)
			except Exception as err:
				print("Backup process failed: " + err)
			
			# Finished backup
			menuItem.set_sensitive(True)
			menuItem.set_label(default_backup_label())
			self.indicate_bliss()
			self.show_notification("Backup complete for "+backupMedium.name)
			self.update_view()
			return True
		self.backupControls[backupMedium.path] = self.add_image_menu_item(default_backup_label(), backup, View.DO_BACKUP_ICON)
		self.backupControls[backupMedium.path].sensitive = False
	
	def drive_removed(self, backupMedium):
		if backupMedium.path in self.backupControls:
			self.menu.remove(self.backupControls[backupMedium.path])
	
	def quit(self, _):
		Notify.uninit()
		self.controller.quit()
