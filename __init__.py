# -*- Mode: python; coding: utf-8; tab-width: 8; indent-tabs-mode: t; -*-

import gobject, gtk
import rb, rhythmdb
import traceback
import math
import Analyze
import google
import gettext, os
from google import GoogleMusic
from OnlineMusicConfigure import OnlineMusicConfigureDialog
from OnlineMusicSearch import OnlineMusicSearchDialog
import ShowLyrics

class OnlineMusicEntryType(rhythmdb.EntryType):
	def __init__(self, db):
		rhythmdb.EntryType.__init__(self, name='OnlineMusicType', category=rhythmdb.ENTRY_NORMAL)

	def can_sync_metadata(self, entry):
		return True

class Plugin(rb.Plugin):
	def __init__(self):
		self.switch = None
		self.search = None
		rb.Plugin.__init__(self)
  
	def activate(self, shell):
		gettext.translation('online_music', self.find_file("locale")).install(True)
		self.db = shell.props.db

		self.entry_type = OnlineMusicEntryType(self.db)
		self.db.register_entry_type(self.entry_type)
	
		self.entry_type.get_playback_uri=self.get_playback_uri
	
		width, height = gtk.icon_size_lookup(gtk.ICON_SIZE_LARGE_TOOLBAR)
		icon = gtk.gdk.pixbuf_new_from_file_at_size(self.find_file("32.png"), width, height)

		self.source = gobject.new (OnlineMusicSource, 
							   shell = shell, 
							   name = _("Online Muisc"),
							   plugin = self, 
							   icon = icon, 
							   entry_type = self.entry_type)
		shell.append_source(self.source, None)
		shell.register_entry_type_for_source(self.source, self.entry_type)
		
		#lyrics init
		self.showLyrics = ShowLyrics.ShowLyrics(shell)
		
		# First lets see if we can add to the context menu
		ui = shell.get_ui_manager()

		# Group and it's actions
		self.action_group = gtk.ActionGroup ('OnlineMusicActions')

		# Create Actions for the plugin
		action = gtk.Action ('ReloadMusic', _('Reload'),
						 _('Reload Music'),
						 'gtk-refresh')
		activate_id = action.connect ('activate', lambda a: self.source.load_music())#self.source.onlineMusic.activate()
		self.action_group.add_action (action)
	
		# Create switch list action
		action = gtk.Action ('SwitchList', _('Switch'),
						 _('Switch List'),
						 'gtk-properties')#gtk-preferences
		activate_id = action.connect ('activate', lambda a: self.switch_list())
		self.action_group.add_action (action)
	
		action = gtk.Action('SearchMusic', _('Search'),
						 _('Search Music'),
						 'gtk-find')#gtk-preferences
		activate_id = action.connect ('activate', lambda a: self.search_music())
		self.action_group.add_action (action)
		
		action = gtk.ToggleAction('ShowLyrics', _('Lyrics'),
					_('Show Lyrics'),
					'gtk-justify-center')#gtk-preferences
		activate_id = action.connect ('toggled', self.showLyrics.show_lyrics_toggled, shell, self.db)
		self.action_group.add_action (action)
		
		ui.insert_action_group(self.action_group, -1)
		
		self.shell_ids = (
			shell.connect("notify::selected-source", self.showLyrics.notify_selected_source, self.action_group),
		)
		
		player = shell.get_player()
		self.player_ids = (
			player.connect("elapsed-nano-changed", self.showLyrics.elapsed_nano_changed),
			player.connect_after("playing-song-changed", self.showLyrics.playing_song_changed, self.db),
		)
	
	def deactivate(self, shell):
		for handler_id in self.shell_ids:
			shell.disconnect(handler_id)

		player = shell.get_player()
		for handler_id in self.player_ids:
			player.disconnect(handler_id)
		
		self.showLyrics.notify_selected_source(None, None, self.action_group)
		self.showLyrics.delete_thyself()
		self.showLyrics = None
		
		ui = shell.get_player().get_property('ui-manager')
		ui.remove_action_group(self.action_group)
		self.action_group = None
	
		for row in self.source.props.query_model:
			entry = row[0]
			self.db.entry_delete(entry)
		self.db.commit()
	
		self.db = None
		self.entry_type = None
		
		self.source.delete_thyself()
		self.source = None
		self.switch = None
		self.search = None
	
	def switch_list(self):
		if not self.switch:
			self.switch = OnlineMusicConfigureDialog(self, self.source).get_dialog()
		self.switch.present()
  
	def search_music(self):
		if not self.search:
			self.search = OnlineMusicSearchDialog(self.source).get_dialog()
		self.search.present()
	
	def get_playback_uri(self, entry):
		if not entry:return None
		url = self.db.entry_get (entry, rhythmdb.PROP_LOCATION)
	
		if not url.endswith('.mp3'):
			print 'Load the google music:%s' % url
			url = Analyze.getSongByURL(url)['url']
			
			if url is not None:
				self.db.set(entry, rhythmdb.PROP_LOCATION, url)
				print 'Get google song url: %s' % url
				return url
			else:
				return None
		else:
			return url
	
class OnlineMusicSource(rb.BrowserSource):
	def __init__(self):
		rb.BrowserSource.__init__(self, name="onlineMusic")
		self.__activated=False
		self.onlineMusic=None
		self.__progressing=False
		self.__loadSong=False
		self.__loadCount=1
		self.__loadAll=1
	
	def do_impl_delete_thyself(self):
		if self.onlineMusic:
			self.onlineMusic.deactivate()
		
		self.onlineMusic = None
		self.entry_type = None
		self.db = None
		self.shell = None
	
		rb.BrowserSource.do_impl_delete_thyself (self)
	
	def do_impl_activate(self):
		if not self.__activated:
			self.__activated=True
			self.shell=self.get_property('shell')
			self.db = self.shell.get_property('db')
			self.entry_type = self.get_property('entry-type')
			#self.load_music()
			self.shell.get_player().connect('playing-song-changed', self.playing_entry_changed)
		rb.BrowserSource.do_impl_activate (self)
  
	def do_impl_deactivate(self):
		rb.BrowserSource.do_impl_deactivate (self)
	
	def do_impl_get_ui_actions(self):
		return ["SwitchList", "SearchMusic", "ShowLyrics"]
	
	def load_music(self):
		if self.onlineMusic:
			self.onlineMusic.deactivate()
		  
		self.onlineMusic = None
		self.onlineMusic=GoogleMusic(self, None)
		self.onlineMusic.start()
  
	def do_impl_get_status(self):
		if self.__progressing:
			return (_('Google music loading...'), "%d / %d" % (self.__loadCount, 
					  self.__loadAll), self.__loadCount/self.__loadAll)
		else:
			return (_("%s: %d songs, %d minutes") % (_('Google music'), 
					  self.get_song_count(),
					  int(math.ceil(self.props.query_model.get_duration() / 60))), 
					None, 1.0)
	  
	def get_song_count(self):
		count = 0
		for row in self.props.query_model:
			count += 1
		return count
	
	def notify_progress(self, progressing, loadCount, loadAll):
		self.__progressing=progressing
		self.__loadCount = loadCount
		self.__loadAll = loadAll
		self.notify_status_changed()
	
	def playing_entry_changed(self, sp, entry):
		if not entry or entry.get_entry_type() != self.db.entry_type_get_by_name("OnlineMusicType"):
			return

		# Retrieve corresponding feed for this entry
		comment = self.db.entry_get(entry, rhythmdb.PROP_COMMENT)
		image_url = comment.split('\n')[1].replace('image=', '')
		
		if image_url != '':
			gobject.idle_add(self.db.emit_entry_extra_metadata_notify, entry, "rb:coverArt-uri", str(image_url))
		
gobject.type_register(OnlineMusicSource)
