# -*- Mode: python; coding: utf-8; tab-width: 8; indent-tabs-mode: t; -*-

import gtk
import re
import Analyze
import time
import os
import traceback
import rb, rhythmdb

class ShowLyrics (object):
	def __init__(self, shell):
		self.liststore = None
		self.lyricsList = None
		self.lyrics_container = None
		self.shell = shell
		self.lyrics_is_loaded = False
		self.lyrics_is_txt = True
		self.lyrics_active = False
		self.path = '/media/e/Music/lyrics/'
		self.initPanel()
  
	def delete_thyself(self):
		self.lyricsList.disconnect(self.active_id)
		self.liststore = None
		self.lyricsList = None
		self.lyrics_container = None
		self.shell = None
		self.lyrics_is_loaded = False
		self.lyrics_is_txt = False
		self.lyrics_active = False
		self.path = None
	
	def initPanel(self):
		columnNames = ['content']
		self.liststore = gtk.ListStore(long, str, str)
		self.lyricsList = gtk.TreeView(self.liststore)
		self.lyricsList.set_headers_visible(False)
		
		# create the TreeViewColumn to display the data
		tvcolumn = [None] * len(columnNames)
		for n in range(0, len(columnNames)):
			cell = gtk.CellRendererText()
			cell.set_property('xalign', 0.5)
			cell.set_property('wrap-mode', gtk.WRAP_WORD)
			cell.set_property('wrap-width', 150)
			tvcolumn[n] = gtk.TreeViewColumn(columnNames[n], cell)
			tvcolumn[n].add_attribute(cell, 'text', n + 1)
			self.lyricsList.append_column(tvcolumn[n])
		  
		self.lyrics_container = gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
		self.lyrics_container.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.lyrics_container.set_property('shadow-type', gtk.SHADOW_IN)
		self.lyrics_container.set_property('width-request', 175)
		self.lyrics_container.add(self.lyricsList)
		
		self.active_id = self.lyricsList.connect("row-activated", self.play_song_by_time)
	
	def getPanel(self):
		if self.lyrics_container is None:
			self.initPanel()
		return self.lyrics_container
	
	def play_song_by_time(self, treeview, path, view_column):
		model = treeview.get_model()
		iter = model.get_iter(path)
		time = model.get_value(iter, 0)
		content = model.get_value(iter, 1)
		
		player = self.shell.get_player()
		player.set_playing_time(time / 1000)
		print 'time=%d, content=%s' % (time, content)
	
	def elapsed_nano_changed(self, player, elapsed):
		if not self.lyrics_active: return
		if not self.lyrics_is_loaded or self.lyrics_is_txt: return
		elapsed = elapsed / 1000000
		#elapsed = elapsed * 1000
		model = self.lyricsList.get_model()
		user_data = [elapsed, None, None,]
		model.foreach(self.for_each_func, user_data)
		
		if user_data[1] is None: return
		tree_selection = self.lyricsList.get_selection()
		tree_selection.select_path(user_data[1])
		self.lyricsList.scroll_to_cell(user_data[1], column=None, use_align=True, row_align=0.5, col_align=1.0)
	
	def for_each_func(self, model, path, iter, user_data):
		time = model.get_value(iter, 0)
		elapsed = user_data[0]
		
		if elapsed < time:
			if user_data[1] == None:
				user_data[1] = path
			return True
		else:
			user_data[1] = path
			return False
  
	def find_file(self, title, artist, location):
		filePath = location.replace('.mp3', '.lrc')
		
		if os.path.isfile(filePath):
			return filePath
		  
		fileName = '%s - %s.lrc' % (artist, title)
		filePath = os.path.join(self.path, fileName)
		if os.path.isfile(filePath):
			return filePath
		
		fileName = '%s-%s.lrc' % (artist, title)
		filePath = os.path.join(self.path, fileName)
		if os.path.isfile(filePath):
			return filePath
		  
		fileName = '%s - %s.lrc' % (title, artist)
		filePath = os.path.join(self.path, fileName)
		if os.path.isfile(filePath):
			return filePath
		
		fileName = '%s-%s.lrc' % (title, artist)
		filePath = os.path.join(self.path, fileName)
		if os.path.isfile(filePath):
			return filePath
		
		return None
	
	def load_lyrics(self, title, artist, location, lyrics_url):
		start_time = time.time() * 1000
		
		self.lyrics_is_loaded = False
		self.lyrics_is_txt = True
		self.liststore.clear()
		self.liststore.append([0, _("Loading lyric ......"), '00:00.00'])
		genreRe = re.compile("^S[a-zA-z0-9]{16}")
		#result = genreRe.match(genre)
		
		def loader_cb(data):
			if data is None:
				self.load_default(title, artist, location)
			else:
				self.loadData(data)
				self.lyrics_is_loaded = True
				end_time = time.time() * 1000
				print 'Load lryics spend time %f:' % (end_time - start_time)
				
		if lyrics_url is not None:
			print 'Load lyrics from google: %s' % lyrics_url
			
			#lyrics = Analyze.getLyrics(lyrics_url)
			l = rb.Loader()
			l.get_url (lyrics_url, loader_cb)
			
			return
		
		filePath = self.find_file(title, artist, location)
		if filePath is not None:
			print 'Load lyrics from file: %s' % filePath
			lyrics = Analyze.getLyricsByFile(filePath)
			if lyrics is None:
				self.load_default(title, artist, location)
			else:
				self.loadData(lyrics)
				self.lyrics_is_loaded = True
			end_time = time.time() * 1000
			print 'Load lryics spend time %f:' % (end_time - start_time)
			return
		  
		self.load_default(title, artist, location)
		#看起来没有多大必要设置
		#self.lyrics_is_loaded = True
		
		end_time = time.time() * 1000
		print 'Load lryics spend time %f:' % (end_time - start_time)
	
	def load_default(self, title, artist, location):
		time = 0
		time_str = '00:00.00'
		
		lyric_list = []
		lyric_list.append([time, title, time_str])
		lyric_list.append([time, artist, time_str])
		lyric_list.append([time, '', time_str])
		lyric_list.append([time, _("Can't find the lyric"), time_str])
		
		self.liststore.clear()
		for lyric in lyric_list:
			self.liststore.append(lyric)
		
		self.lyricsList.columns_autosize()
	
	def loadData(self, lyrics):
		titleRe = re.compile('\[(al:|ar:|by:|re:|ti:|ve:)([^\]]*)\]')
		offsetRe = re.compile('\[offset:([+|-]*)([^\]]*)\]')
		timeRe = re.compile('\[(\d{2,}):(\d{2})\.*(\d{0,2})\]')
		
		offset = 0
		
		lines = lyrics.split("\n")
		lyric_list = []
		for line in lines:
			length = len(lyric_list)
			line = line.replace('\r', '').strip()
			
			result = timeRe.findall(line)
			if len(result) > 0:
				for timelist in result:
					minute = timelist[0]
					second = timelist[1]
					milsec = timelist[2]
					if milsec == '':
						milsec = '00'
					time = int(minute) * 60 * 1000 + int(second) * 1000 + int(milsec) * 10 + offset
					time_str = '%s:%s.%s' % (minute, second, milsec)
				  
					#get the lyric content
					start = 0
					iter = timeRe.finditer(line)
					for i in iter:
						start = i.end()
					
					i = length  
					for i in range(length -1, -1, -1):
						lTime = lyric_list[i][0]
						if time >= lTime:
							i += 1
							break;
					self.lyrics_is_txt = False
					lyric_list.insert(i, [time, line[start:], time_str])
				  
				continue
			
			result = titleRe.findall(line)
			if len(result) > 0:
				time = 0
				time_str = '00:00.00'
				if length != 0:
					time = lyric_list[length - 1][0]
					time_str = lyric_list[length - 1][2]
				  
				lyric_list.append([time, result[0][1], time_str])
				continue
			
			result = offsetRe.findall(line)
			if len(result) > 0:
				op = result[0][0]
				if op == '' or op == '+':
					offset += int(result[0][1])
				else:
					offset -= int(result[0][1])
				continue
		
			#get the lyric line time
			time = 0
			time_str = '00:00.00'
			if length != 0:
				time = lyric_list[length - 1][0]
				time_str = lyric_list[length - 1][2]
		  
			lyric_list.append([time, line, time_str])
			continue
		self.liststore.clear()  
		for lyric in lyric_list:
			self.liststore.append(lyric)
			
		self.lyricsList.columns_autosize()
			
	def show_lyrics_toggled(self, action, shell, db):
		try:
			if action.get_active():
				shell.add_widget (self.lyrics_container, rb.SHELL_UI_LOCATION_RIGHT_SIDEBAR, True, True)
				self.lyrics_container.show_all()
				#shell.notebook_set_page(self.lyrics_container)
				self.lyrics_active = True
				player = shell.get_player()
				self.playing_song_changed(player, player.get_playing_entry(), db)
			else:
				if self.lyrics_active:
					shell.remove_widget (self.lyrics_container, rb.SHELL_UI_LOCATION_RIGHT_SIDEBAR)
				self.lyrics_active = False
		except Exception, e:
			traceback.print_exc()
  
	def notify_selected_source(self, shell, a, action_group):
		if self.lyrics_active:
			action = action_group.get_action("ShowLyrics")
			action.set_active(False)
			print 'Disabe lyrics panel'
	
	def playing_song_changed(self, player, entry, db):
		if entry is None: return
		  
		if not self.lyrics_active: 
			self.liststore.clear()
			self.lyrics_is_loaded = False
			return
		
		lryics_url = None
		if entry.get_entry_type() == db.entry_type_get_by_name("OnlineMusicType"):
			comment = db.entry_get(entry, rhythmdb.PROP_COMMENT)
			lryics_url = comment.split('\n')[2].replace('lyrics=', '')
			
			if lryics_url == '':
				lryics_url = None
		
		title = db.entry_get(entry, rhythmdb.PROP_TITLE)
		artist = db.entry_get(entry, rhythmdb.PROP_ARTIST)
		location = db.entry_get(entry, rhythmdb.PROP_LOCATION)
		self.load_lyrics(title, artist, location, lryics_url)

