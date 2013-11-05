from gi.repository import Gtk
from gi.repository import AppIndicator3 as appindicator
import os
import signal
import sys

from birdback import controller

class BirdbackView(object):
	def __init__(self):
		self.pidfile = os.path.expanduser("~/.birdback.pid")
		self.check_pid()
		self.controller = controller.Controller()
		try:
			self.indicator = Indicator(self, controller)
		except Exception as e:
			print(e)
			print("Critical error. Exiting.")
			self.exit(1)

	def signal_exit(self, signum, frame):
		print('Recieved signal: ', signum)
		print('Quitting...')
		self.exit()
	
	def exit(self, code=0):
		self.controller.stop()
		os.unlink(self.pidfile)
		Gtk.main_quit()
		sys.exit(code)

	def check_pid(self):
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
	
	def __del__(self):
		self.exit()
	
	def run(self):
		Gtk.main() # run Gtk run!

class Indicator(object):
	def __init__(self, view, controller):
		# See http://developer.ubuntu.com/api/devel/ubuntu-13.10/python/AppIndicator3-0.1.html
		self.indicator = appindicator.Indicator.new(
		  "birdback-indicator",
		  "birdback",
		  appindicator.IndicatorCategory.APPLICATION_STATUS)
		self.view = view
		self.controller = controller
		self.setup_indicator()

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
		self.view.exit()

if __name__ == '__main__':
	try:
		view = BirdbackView()
		signal.signal(signal.SIGTERM, view.signal_exit)
		view.run()
	except KeyboardInterrupt:
		view.exit()
