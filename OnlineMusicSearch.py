# -*- Mode: python; coding: utf-8; tab-width: 8; indent-tabs-mode: t; -*-
import gtk
import gconf
import traceback
import Analyze
import hashlib
import math
from google import GoogleMusic

ONE_PAGE_SIZE = 20
class OnlineMusicSearchDialog (object):
	def __init__(self, source):
		self.search_entry = None
		self.search_btn = None
		self.source = source
		self.onlineMusic = None
		self.has_next = False
		self.count = 0
		self.dialog = self.initDialog()
		self.dialog.connect("delete_event", self.close_dialog)
	
	def get_dialog (self):
		return self.dialog
	
	def initDialog(self):
		dialog = gtk.Dialog(_("Online Music Search"),
						  None,
						  gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, None)
						  
		dialog.set_size_request(500, 600)
		
		vbox = dialog.get_content_area()
		vbox.pack_start(self.get_search_panel(), True)
		vbox.show_all()
		return dialog
	
	def get_search_panel(self):
		#The search result list
		columnNames = ['', _('Title'), _('Album'), _('Artist'), _('Time')]#, 'ID'
		liststore = gtk.ListStore(bool, str, str, str, str, str)
		self.search_tree = gtk.TreeView(liststore)
		self.search_tree.set_headers_clickable(True)
		self.search_tree.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_HORIZONTAL)
		
		tvcolumn = [None] * len(columnNames)
		for n in range(0, len(columnNames)):
			if columnNames[n] != '':
				cell = gtk.CellRendererText()
				tvcolumn[n] = gtk.TreeViewColumn(columnNames[n], cell)
				tvcolumn[n].add_attribute(cell, 'text', n)
				self.search_tree.append_column(tvcolumn[n])
			else:
				cell = gtk.CellRendererToggle()
				cell.set_property('activatable', True);
				cell.connect('toggled', self.select_row, self.search_tree, liststore)
				tvcolumn[n] = gtk.TreeViewColumn(columnNames[n], cell)
				tvcolumn[n].add_attribute(cell, 'active', n)
				self.search_tree.append_column(tvcolumn[n])
		
		tvcolumn[0].set_min_width(20)
		tvcolumn[2].set_min_width(120)
		tvcolumn[3].set_min_width(100)
		tvcolumn[4].set_min_width(40)
		tvcolumn[0].set_max_width(20)
		tvcolumn[1].set_max_width(180)
		tvcolumn[2].set_max_width(130)
		tvcolumn[3].set_max_width(100)
		tvcolumn[4].set_max_width(40)
		tvcolumn[1].set_expand(True)
		self.search_tree.set_reorderable(True)
		scrolled_window = gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
		scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		scrolled_window.add(self.search_tree)
		scrolled_window.set_size_request(490, 500)
	  
		vbox = gtk.VBox(spacing=5)
		
		self.search_entry = gtk.Entry(max=0)
		self.search_btn = gtk.Button(_("Search"))
		self.search_entry.connect("activate", self.search_music, liststore, True)
		self.search_btn.connect("clicked", self.search_music, liststore, True)
		hbox = gtk.HBox(spacing=5)
		hbox.pack_start(self.search_entry, True)
		hbox.pack_start(self.search_btn, False)
		vbox.pack_start(hbox, False)
		
		vbox.pack_start(scrolled_window, True)
		
		hbox = gtk.HBox(spacing=5)
		check_btn = gtk.CheckButton(_("Select/Clear All"))
		next_btn = gtk.Button(_("Next Page"))
		close_btn = gtk.Button(_("Close"))
		add_btn = gtk.Button(_("Add to List"))
		
		next_btn.set_property("width-request", 80)
		close_btn.set_property("width-request", 80)
		add_btn.set_property("width-request", 80)
	
		check_btn.connect("toggled", self.select_all_row, liststore)
		next_btn.connect("clicked", self.search_next, liststore)
		add_btn.connect("clicked", self.add_music, liststore)
		close_btn.connect("clicked", self.hide_dialog)
		
		hbox.pack_start(check_btn, False)
		hbox.pack_start(next_btn, False)
		hbox.pack_end(close_btn, False)
		hbox.pack_end(add_btn, False)
		vbox.pack_start(hbox, False)
		
		return vbox
  
	def select_row(self, renderer, path, treeview, store):
		model = treeview.get_model()
		selection = treeview.get_selection()
		iter = model.get_iter(path)
		select = model.get_value(iter, 0)
		store.set_value(iter, 0, not select)
	
	def search_music(self, btn, store, flag):
		search_key = self.search_entry.get_text().strip()
		if search_key == '':
			return None
		  
		xml_url="http://www.google.cn/music/search?cat=song&q=%s&start=%d&num=%d&cad=player&output=xml" % (search_key, self.count * 20, ONE_PAGE_SIZE)
		song_list = Analyze.getSongList(xml_url, False)
		if not song_list or len(song_list) == 0:
			msgBox = gtk.MessageDialog(parent=self.dialog, flags=gtk.DIALOG_MODAL, type=gtk.MESSAGE_ERROR, 
					buttons=gtk.BUTTONS_CLOSE, message_format=_("No more song!"))
			msgBox.connect("response", lambda a, b: msgBox.hide())
			msgBox.run()
			return None
		  
		if flag:
			store.clear()
		iter = None
		#'', 'Title', 'Album', 'Artist', 'Time', 'ID'
		for song in song_list:
			title = song['name']
			album = song['album']
			artist = song['artist']
			time = song['duration']
			id = song['id']
			iter = store.append([False, title, album, artist, time, id])
		
		if not flag:
			self.search_tree.scroll_to_cell(store.get_path(iter))
		self.count += 1
		if len(song_list) < ONE_PAGE_SIZE:
			self.has_next = False
		else:
			self.has_next = True
	  
	def select_all_row(self, btn, store):
		store.foreach(self.model_foreach_select, btn.get_active())

	def model_foreach_select(self, model, path, iter, flag):
		model.set_value(iter, 0, flag)
	
	def search_next(self, btn, store):
		if self.has_next:
			self.search_music(btn, store, False)
	  
		else:
			msgBox = gtk.MessageDialog(parent=self.dialog, flags=gtk.DIALOG_MODAL, type=gtk.MESSAGE_ERROR, 
					buttons=gtk.BUTTONS_CLOSE, message_format=_("No more song!"))
			msgBox.connect("response", lambda a, b: msgBox.hide())
			msgBox.run()
	
	def add_music(self, btn, store):
		if self.onlineMusic:
			self.onlineMusic.deactivate()
		  
		songs = []
		store.foreach(self.model_foreach_fun, songs)
		if len(songs) == 0:
			return None
		
		self.onlineMusic = None
		self.onlineMusic=GoogleMusic(self.source, songs)
		self.onlineMusic.start()
		
		self.dialog.hide()
  
	def model_foreach_fun(self, model, path, iter, songs):
		select = model.get_value(iter, 0)
		if select:
			title = model.get_value(iter, 1)
			album = model.get_value(iter, 2)
			artist = model.get_value(iter, 3)
			time = model.get_value(iter, 4)
			id = model.get_value(iter, 5)
			hash = hashlib.md5(Analyze.GOOGLE_PLAYER_KEY + id).hexdigest()
			url="http://www.google.cn/music/songstreaming?id=" + id + "&output=xml&sig=" + hash
		  
			durationf=float(time)
			duration=int(math.ceil(durationf))
			song={'name':title,
				'artist':artist,
				'album':album,
				'duration':duration,
				'url':url,
				'genre':None,
				'id':id}
			#print 'name:%s\nartist:%s\nalbum:%s\nduration:%d\nid:%s' % (title, artist, album, duration, id)
			songs.append(song)
	
	def hide_dialog(self, btn):
		self.dialog.hide()
  
	def close_dialog(self, widget, event):
		self.dialog.hide()
		return True
	
if __name__ == '__main__':
	dialog = OnlineMusicSearchDialog().get_dialog()
	dialog.present()
