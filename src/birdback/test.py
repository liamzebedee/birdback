import gobject
import gtk
import appindicator
import os
import signal

class BirdbackGUI(object):
	def __init__(self):
		self.pidfile = os.path.expanduser("~/.birdback.pid")
		self.check_pid()
		try:
			self.indicator = Indicator()
		except Exception as e:
			print e
			print "Critical error. Exiting."
			self.exit(1)

	def signal_exit(self, signum, frame):
		print 'Recieved signal: ', signum
		print 'Quitting...'
		self.exit()
	
   	def exit(self, code=0):
		try:
			print('stopping')
			#self.xflux_controller.stop()
		except MethodUnavailableError:
			pass
		os.unlink(self.pidfile)
		gtk.main_quit()
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
					if err.errno == errno.ESRCH:
						# OSError: [Errno 3] No such process
						print "stale pidfile, old pid: ", oldpid
			except ValueError:
				# Corrupt pidfile, empty or not an int on first line
				pass
		if running:
			print "birdback is already running, exiting"
			sys.exit()
		else:
			file(self.pidfile, 'w').write("%d\n" % pid)
	
	def __del__(self):
		self.exit()
	
	def run(self):
		gtk.main() # run gtk run!

class Indicator(object):
	def __init__(self):
		# See http://developer.ubuntu.com/api/devel/ubuntu-13.10/python/AppIndicator3-0.1.html
		self.indicator = appindicator.Indicator(
		  "birdback-indicator",
		  "birdback",
		  appindicator.CATEGORY_APPLICATION_STATUS)

		self.setup_indicator()

	def setup_indicator(self):
		self.indicator.set_status(appindicator.STATUS_ACTIVE)
		self.indicator.set_icon('birdback')
		self.indicator.set_menu(self.create_menu())

	def create_menu(self):
		menu = gtk.Menu()

		self.add_menu_item("_Pause f.lux", self._toggle_pause,
				menu, MenuItem=gtk.CheckMenuItem)
		self.add_menu_item("_Preferences", self._open_preferences, menu)
		self.add_menu_separator(menu)
		self.add_menu_item("Quit", self._quit, menu)

		return menu

	def add_menu_item(self, label, handler, menu, event="activate", MenuItem=gtk.MenuItem, show=True):
		item = MenuItem(label)
		item.connect(event, handler)
		menu.append(item)
		if show:
			item.show()
		return item

	def add_menu_separator(self, menu, show=True):
		item = gtk.SeparatorMenuItem()
		menu.append(item)
		if show:
			item.show()

	def _toggle_pause(self, item):
		self.xflux_controller.toggle_pause()

	def _open_preferences(self, item):
		self.fluxgui.open_preferences()

	def _quit(self, item):
		self.fluxgui.exit()

if __name__ == '__main__':
	try:
		app = BirdbackGUI()
		signal.signal(signal.SIGTERM, app.signal_exit)
		app.run()
	except KeyboardInterrupt:
		app.exit()
