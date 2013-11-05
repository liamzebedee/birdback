from gi.repository import Gtk
from gi.repository import AppIndicator3 as appindicator

class View(object):
	def __init__(self, controller):
		# See http://developer.ubuntu.com/api/devel/ubuntu-13.10/python/AppIndicator3-0.1.html
		self.indicator = appindicator.Indicator.new(
		  "birdback-indicator",
		  "birdback",
		  appindicator.IndicatorCategory.APPLICATION_STATUS)
		self.controller = controller
		self.setup_indicator()
		
		Gtk.main() # run Gtk run!

	def setup_indicator(self):
		self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
		self.indicator.set_icon('birdback')
		self.indicator.set_menu(self.create_menu())

	def create_menu(self):
		menu = Gtk.Menu()
		self.add_menu_item("Quit", self.quit, menu)
		return menu

	def add_menu_item(self, label, handler, menu, event="activate", MenuItem=Gtk.MenuItem, show=True):
		item = MenuItem(label)
		item.connect(event, handler)
		menu.append(item)
		if show:
			item.show()
		return item

	def add_menu_separator(self, menu, show=True):
		item = Gtk.SeparatorMenuItem()
		menu.append(item)
		if show:
			item.show()

	def quit(self, item):
		Gtk.main_quit()
		self.controller.quit()
