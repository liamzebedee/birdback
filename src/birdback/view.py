from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify
import logging

class View(object):
	INACTIVE_ICON = '/usr/local/share/icons/hicolor/scalable/apps/birdback.svg'
	ATTENTION_ICON = '/usr/local/share/icons/hicolor/scalable/apps/birdback-active.svg'
	
	def __init__(self, controller):
		self.controller = controller
		# See http://developer.ubuntu.com/api/devel/ubuntu-13.10/python/AppIndicator3-0.1.html
		self.indicator = appindicator.Indicator.new(
		  "birdback-indicator",
		  "birdback",
		  appindicator.IndicatorCategory.APPLICATION_STATUS)
		self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
		self.indicator.set_icon(View.INACTIVE_ICON)
		self.indicator.set_attention_icon(View.ATTENTION_ICON)
		self.indicate_inactivity()
		# Menu
		self.menu = Menu(self.quit, self.open_preferences)
		# Preferences dialog
		self.preferences_dialog = PreferencesDialog(View.ATTENTION_ICON)
		self.preferences_dialog.connect("delete-event", self.preferences_dialog.hide2)
		
		self.indicator.set_menu(self.menu.gtk_menu)
		Notify.init('birdback')
		self.backup_controls = {}
	
	
	def indicate_activity(self):
		self.indicator.set_status(appindicator.IndicatorStatus.ATTENTION)
		self.update_view()
	
	
	def indicate_inactivity(self):
		self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
		self.update_view()


	# This is to fire the event loop
	def update_view(self):
		while Gtk.events_pending():
			Gtk.main_iteration_do(False)
	
	
	def show_notification(self, message):
		n = Notify.Notification.new('BirdBack', message, None)
		n.show()
	
	
	def drive_inserted(self, backup_medium):
		# Create a menu item for the backup medium
		default_backup_label = "Backup " + backup_medium.name
		
		# Called when backup control is clicked
		def backup(_0):
			print("Starting backup of " + backup_medium.path)
			backup_control = self.backup_controls[backup_medium.path]
			backup_control.set_sensitive(False) # disabled
			self.indicate_activity()
			
			def backup_progress_callback(progress):
				# Adds text below the menu item
				backup_control.get_children()[0].set_markup("Backing up {0} \n{1}".format(backup_medium.name, progress))
				print("backup " + backup_medium.name + ": " + progress)
				self.update_view()
			
			try:
				# Start backup with callback for progress updates
				self.controller.backup(backup_medium, backup_progress_callback)
				self.show_notification("Backup complete for " + backup_medium.name)
			except Exception as exception:
				notice = "Backup of {0} failed: {1}".format(backup_medium.name, exception)
				print(notice)
				self.show_notification(notice)
			finally:
				# Revert to default
				backup_control.set_sensitive(True) # enabled
				backup_control.set_label(default_backup_label)
				self.indicate_inactivity()
		self.backup_controls[backup_medium.path] = self.menu.add_menu_item(default_backup_label, backup)
		#self.backup_controls[backup_medium.path].sensitive = False

	
	
	def drive_removed(self, backup_medium):
		if backup_medium.path in self.backup_controls:
			item = self.backup_controls[backup_medium.path]
			item.hide()
			self.menu.gtk_menu.remove(item)
	
	def open_preferences(self, _0):
		self.preferences_dialog.show()
	
	def quit(self, _):
		Notify.uninit()
		self.controller.quit()


# TODO make this inherit from Gtk.Menu, simplify things
class Menu(object):
	def __init__(self, quit_handler, preferences_handler):
		self.gtk_menu = Gtk.Menu()
		self.gtk_menu.show_all()
		
		self.add_image_menu_item('Quit', quit_handler, 'gtk-stop')
		self.add_image_menu_item('Preferences', preferences_handler, 'gtk-preferences')
	
	def add_menu_item(self, label, handler, event="activate", MenuItem=Gtk.MenuItem, show=True):
		item = MenuItem(label)
		item.connect(event, handler)
		self.gtk_menu.append(item)
		if show:
			item.show()
		return item
	
	def add_image_menu_item(self, label, handler, img_name, event="activate", show=True):
		img = Gtk.Image()
		img.set_from_stock(img_name, Gtk.IconSize.BUTTON)
		item = Gtk.ImageMenuItem(label)
		item.set_image(img)
		item.connect(event, handler)
		self.gtk_menu.append(item)
		item.show()

class PreferencesDialog(Gtk.Window):
	def __init__(self, icon_path):
		Gtk.Window.__init__(self, title="Birdback - Preferences")
		self.set_icon_from_file(icon_path)
		self.set_border_width(10)
		self.set_default_size(500, 400)
		
		self.excludes_list = Gtk.ListStore(str)
		tree = Gtk.TreeView(self.excludes_list)
		column = Gtk.TreeViewColumn("Folders to ignore", Gtk.CellRendererText(), text=0)
		tree.append_column(column)
		scroll = Gtk.ScrolledWindow()
		scroll.hscrollbar_policy = Gtk.PolicyType.AUTOMATIC
		scroll.vscrollbar_policy = Gtk.PolicyType.AUTOMATIC
		scroll.shadow_type = Gtk.ShadowType.IN
		scroll.add(tree)
		
		
		toolbar = Gtk.Toolbar();
		toolbar.set_style(Gtk.ToolbarStyle.ICONS)
		toolbar.set_icon_size(Gtk.IconSize.SMALL_TOOLBAR)
		toolbar.set_show_arrow(False)
		scroll.get_style_context().set_junction_sides(Gtk.JunctionSides.BOTTOM)
		toolbar.get_style_context().add_class(Gtk.STYLE_CLASS_INLINE_TOOLBAR)
		toolbar.get_style_context().set_junction_sides(Gtk.JunctionSides.TOP)
		
		add_button = Gtk.ToolButton("Add")
		add_button.set_icon_name("list-add-symbolic")
		add_button.connect("clicked", self.add_path)
		toolbar.insert(add_button, -1)
		
		remove_button = Gtk.ToolButton("Remove")
		remove_button.set_icon_name("list-remove-symbolic")
		remove_button.connect("clicked", self.remove_path)
		toolbar.insert(remove_button, -1)
		
		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
		vbox.set_homogeneous(False)
		self.add(vbox)
		vbox.pack_start(scroll, True, True, 0)
		vbox.pack_start(toolbar, False, True, 0)
		
		selection = tree.get_selection()
		selection.set_mode(Gtk.SelectionMode.MULTIPLE)
		self.excludes_list.clear()
		self.excludes_list.append(["/home/work/Random/moreshit/asdsadsad/aswd3f"])
		
		self.show_all()
		
	def add_path(self, button):
		file_chooser = Gtk.FileChooserDialog("Choose folder", self, Gtk.FileChooserAction.SELECT_FOLDER, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
		file_chooser.set_select_multiple(True)
		
		response = file_chooser.run()
		if response == Gtk.ResponseType.OK:
			files = file_chooser.get_filenames()
			print(str(files))
			# add files
		
		file_chooser.destroy()
	
	def remove_path(self, button):
		return
	
	def hide2(self, widget):
		self.hide()
