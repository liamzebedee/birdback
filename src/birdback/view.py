from gi.repository import Gtk
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify

class View(object):
	def __init__(self, controller):
		self.controller = controller
		# See http://developer.ubuntu.com/api/devel/ubuntu-13.10/python/AppIndicator3-0.1.html
		self.indicator = appindicator.Indicator.new(
		  "birdback-indicator",
		  "birdback",
		  appindicator.IndicatorCategory.APPLICATION_STATUS)
		self.indicate_bliss()
		self.menu = self.create_menu()
		self.indicator.set_menu(self.menu)
		Notify.init('birdback')
		self.backupControls = {}
	
	def indicate_activity(self):
		self.indicator.set_status(appindicator.IndicatorStatus.ATTENTION)
		self.indicator.set_icon('birdback-active')
	
	def indicate_bliss(self):
		self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
		self.indicator.set_icon('birdback')
	
	def add_menu_item(self, label, handler, event="activate", MenuItem=Gtk.MenuItem, show=True):
		item = MenuItem(label)
		item.connect(event, handler)
		self.menu.append(item)
		if show:
			item.show()
		return item
	
	def create_menu(self):
		self.menu = Gtk.Menu()
		self.menu.show_all()
		
		self.add_menu_item("Quit", self.quit)
		return self.menu

	def drive_inserted(self, backupMedium):
		n = Notify.Notification.new('BirdBack', "Drive inserted: "+backupMedium.path, None)
		n.show()
		def backup():
			self.controller.backup(backupMedium)
		self.backupControls[backupMedium.path] = self.add_menu_item("Backup "+backupMedium.name, backup)
	
	def drive_removed(self, backupMedium):
		if backupMedium.path in self.backupControls:
			self.menu.remove(self.backupControls[backupMedium.path])
	
	def quit(self, _):
		Notify.uninit()
		self.controller.quit()
