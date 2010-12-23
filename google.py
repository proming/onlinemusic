# -*- Mode: python; coding: utf-8; tab-width: 8; indent-tabs-mode: t; -*-
import rhythmdb
import rb
import traceback
from OnlineMusicConfigure import Preference
import Analyze
import threading
import time
import gobject

class OnlineMusic(threading.Thread):
	def run(self):pass
	def __init__(self, source, songs):
		threading.Thread.__init__(self) 
		self.set_stop = False
		self.is_run = False
		self.source = source
		self.songs = songs
		self.db = source.db
		self.entry_type = source.entry_type
		self.preference = Preference()
		self.listType, self.listId, self.album = self.preference.get_prefs()
	
	def deactivate(self):
		while self.is_run:
			self.set_stop = True
		  
		self.db = None
		self.entry_type = None
		self.source = None
		self.preference = None
  
	def add_song(self,song):
		try:
			aSong = Analyze.getSongByURL(song['url'])
			if not aSong: 
				return
			entry = self.db.entry_new(self.entry_type, aSong['url'])
			print song
			print aSong
			self.db.set(entry, rhythmdb.PROP_TITLE, song['name'])
			self.db.set(entry, rhythmdb.PROP_ARTIST, song['artist'])
			self.db.set(entry, rhythmdb.PROP_ALBUM, song['album'])
			self.db.set(entry, rhythmdb.PROP_DURATION, song['duration'])
			#self.db.set(entry, rhythmdb.PROP_TRACK_NUMBER, song['track_number'])
			self.db.set(entry, rhythmdb.PROP_GENRE, self.n2str(aSong['genre']))
			self.db.set(entry, rhythmdb.PROP_COMMENT, 
				'id=%s\nimage=%s\nlyrics=%s' % 
				(song['id'], self.n2str(aSong['image']), self.n2str(aSong['lyrics'])))
			#self.db.set(entry, rhythmdb.PROP_IMAGE, aSong['image'])
		except Exception, e:
			traceback.print_exc()
			
	def n2str(self, none):
		return none if none else ''

class GoogleMusic(OnlineMusic):
	def __init__(self,source, songs):
		OnlineMusic.__init__(self,source, songs)
   
	def run(self):
		if not self.songs:
			self.listType, self.listId, self.album = self.preference.get_prefs()
			
			#url="http://www.google.cn/music/chartlisting?cat=song&q=chinese_songs_cn&output=xml"
			url="http://www.google.cn/music/album?id=B679efdab97c7afc7&output=xml"
			if self.listType is not None and self.listId is not None:
				if self.listType == 'song':
					url="http://www.google.cn/music/chartlisting?cat=song&q=%s&output=xml" % self.listId
				elif self.listType == 'topic':
					url="http://www.google.cn/music/topiclisting?cat=song&q=%s&output=xml" % self.listId
		  
			print 'Load List from the %s' % url
			self.songs = Analyze.getSongList(url, True)
			if not self.songs:
				return None
			for row in self.source.props.query_model:
				entry = row[0]
				self.db.entry_delete(entry)
		
		self.is_run = True
		load_count = 0
		load_all = len(self.songs)
		gobject.idle_add(self.source.notify_progress, True, load_count, load_all)
		for song in self.songs:
			if not self.set_stop:
				time.sleep(0.2) 
				self.add_song(song)
				load_count += 1
				gobject.idle_add(self.source.notify_progress, True, load_count, load_all)
				self.db.commit()
		self.is_run = False
		gobject.idle_add(self.source.notify_progress, False, 1, 1)
