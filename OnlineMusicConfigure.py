# -*- Mode: python; coding: utf-8; tab-width: 8; indent-tabs-mode: t; -*- 
import pygtk
import gtk
import gconf
import os
import traceback
from xml.dom.minidom import parse, parseString
import Analyze
import rb

ONE_PAGE_SIZE = 20
class OnlineMusicConfigureDialog (object):
	def __init__(self, plugin, source):
		self.plugin = plugin
		self.source = source
		self.preference = Preference()
		self.chartFileName = 'chartlist.xml'
		self.topicFileName = 'topiclist.xml'
		self.load_label = None
		self.dialog = self.initDialog()
		self.dialog.connect("response", self.dialog_response)
		self.dialog.connect("delete_event", self.hide_dialog)
		
	
	def dialog_response(self, dialog, response):
		selections = {
			  0 : lambda : self.chartTree.get_selection(),
			  1 : lambda : self.topicTree.get_selection()
		}
		page = self.notebook.get_current_page()
		if response == gtk.RESPONSE_OK:
			selection = selections.get(page, lambda : self.chartTree.get_selection())()
			(model, iter) = selection.get_selected()
			if iter:
				listName = model.get_value(iter, 0)
				listId = model.get_value(iter, 1)
				listType = model.get_value(iter, 2)
				if listType == 'song' or listType == 'topic':
					self.preference.set_values(listType, listId, listName)
					self.dialog.hide()
					self.source.load_music()
				else:
					msgBox = gtk.MessageDialog(parent=self.dialog, flags=gtk.DIALOG_MODAL, type=gtk.MESSAGE_ERROR, 
							buttons=gtk.BUTTONS_CLOSE, message_format=_("Select the row that type column is 'song'!"))
					msgBox.connect("response", lambda a, b: msgBox.hide())
					msgBox.run()
		  
		elif response == gtk.RESPONSE_CANCEL or response == gtk.RESPONSE_DELETE_EVENT:
			self.dialog.hide()
			return True
		else:
			print "unexpected response type"
	
	def hide_dialog(self, widget, event):
		self.dialog.hide()
		return True
	
	def get_dialog (self):
		return self.dialog
	
	def initDialog(self):
		dialog = gtk.Dialog(_("Online Music Preference"),
						  None,
						  gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
						  (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
						  gtk.STOCK_OK, gtk.RESPONSE_OK))
						  
		dialog.set_size_request(500, 600)
		
		self.notebook = gtk.Notebook()
		self.notebook.append_page(self.initChartTree(), gtk.Label(_('Chart List')))
		self.notebook.append_page(self.initTopicTree(), gtk.Label(_('Topic List')))

		vbox = dialog.get_content_area()
		vbox.pack_start(self.notebook, True)
		vbox.show_all()
		return dialog
  
	def initChartTree(self):
		treestore = gtk.TreeStore(str, str, str)
		self.loadChartData(treestore)
		self.chartTree = gtk.TreeView(treestore)
		self.chartTree.set_headers_clickable(True)
		self.chartTree.set_enable_tree_lines(True)
		tvcolumn = gtk.TreeViewColumn(_('Name'))
		tvcolumn2 = gtk.TreeViewColumn(_('Id'))
		tvcolumn3 = gtk.TreeViewColumn(_('Type'))
		self.chartTree.append_column(tvcolumn)
		self.chartTree.append_column(tvcolumn2)
		self.chartTree.append_column(tvcolumn3)
		cell = gtk.CellRendererText()
		tvcolumn.pack_start(cell, True)
		tvcolumn2.pack_start(cell, True)
		tvcolumn3.pack_start(cell, True)
		tvcolumn.add_attribute(cell, 'text', 0)
		tvcolumn2.add_attribute(cell, 'text', 1)
		tvcolumn3.add_attribute(cell, 'text', 2)
		
		self.chartTree.set_reorderable(True)
		scrolled_window = gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
		scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		scrolled_window.add(self.chartTree)
		
		return scrolled_window
	
	def loadChartData(self, store):
		filePath = self.plugin.find_file(self.chartFileName)
		infile = open(filePath, 'r')
		xmlData = ''
		for line in infile:
			xmlData += line
		dom1 = parseString(xmlData)
		
		chartLists = dom1.getElementsByTagName('chartList')
		for chartList in chartLists:
			listId = chartList.getElementsByTagName('listId')[0].childNodes[0].nodeValue
			listName = chartList.getElementsByTagName('listName')[0].childNodes[0].nodeValue
			piter = store.append(None, (listName, listId, ''))
		  
			charts = chartList.getElementsByTagName('chart')
			for chart in charts:
				chartId = chart.getElementsByTagName('id')[0].childNodes[0].nodeValue
				chartName = chart.getElementsByTagName('name')[0].childNodes[0].nodeValue
				chartType = chart.getElementsByTagName('type')[0].childNodes[0].nodeValue
				store.append(piter, (chartName, chartId, chartType))
		return True	

	def initTopicTree(self):
		columnNames = [_('TopicName'), _('Desc')]#, 'PicURL', 'Desc', 'Time'
		liststore = gtk.ListStore(str, str, str, str, str)
		#self.loadTopicData(liststore)
		self.topicTree = gtk.TreeView(liststore)
		self.topicTree.set_headers_clickable(True)
		self.topicTree.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_HORIZONTAL)
		tvcolumn = [None] * len(columnNames)
		cell = gtk.CellRendererText()
		tvcolumn[0] = gtk.TreeViewColumn(columnNames[0], cell)
		tvcolumn[0].add_attribute(cell, 'text', 0)
		self.topicTree.append_column(tvcolumn[0])
		
		cell = gtk.CellRendererText()
		cell.set_property('wrap-mode', gtk.WRAP_WORD)
		cell.set_property('wrap-width', 250)
		tvcolumn[1] = gtk.TreeViewColumn(columnNames[1], cell)
		tvcolumn[1].add_attribute(cell, 'text', 4)
		self.topicTree.append_column(tvcolumn[1])
		
		tvcolumn[0].set_min_width(210)
		tvcolumn[1].set_min_width(250)
		tvcolumn[0].set_max_width(210)
		tvcolumn[1].set_max_width(250)
		
		self.topicTree.set_reorderable(True)
		scrolled_window = gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
		scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		scrolled_window.add(self.topicTree)
		scrolled_window.set_size_request(490, 500)
		vbox = gtk.VBox(spacing=5)
		vbox.pack_start(scrolled_window, True)
		vbox.pack_start(gtk.HSeparator(), False)
		
		self.search_spin = gtk.SpinButton(digits=0)
		self.search_spin.set_range(1, 200)
		self.search_spin.set_increments(1, 2)
		self.search_spin.set_numeric(True)
		search_btn = gtk.Button(_("Go"))
		search_btn.set_property("width-request", 80)
		self.search_spin.connect("activate", self.search_topic_list, liststore, True)
		search_btn.connect("clicked", self.search_topic_list, liststore, True)
		
		self.load_label = gtk.Label(_("Loading..."))
		self.load_label.set_justify(gtk.JUSTIFY_RIGHT)
		hbox = gtk.HBox(spacing=5)
		hbox.pack_start(self.search_spin, False)
		hbox.pack_start(search_btn, False)
		hbox.pack_start(self.load_label, True)
		
		vbox.pack_start(hbox, False)
		self.search_topic_list(self.search_spin, liststore, True)
		return vbox
	
	def search_topic_list(self, btn, store, flag):
		page = self.search_spin.get_value()
		start = (page - 1) * ONE_PAGE_SIZE
		url = 'http://www.google.cn/music/topiclistingdir?cat=song&start=%d&num=%d' % (start, ONE_PAGE_SIZE)
		
		def loader_cb(data):
			topic_list = Analyze.getTopicList(data)
			if topic_list is not None:
				store.clear()
				for topic in topic_list:
					chartName = topic['name'].encode("utf-8")
					chartId = topic['id']
					chartType = topic['type']
					chartPicURL = topic['picURL']
					chartDesc = topic['desc'].encode("utf-8")
					store.append([chartName, chartId, chartType, chartPicURL, chartDesc])
				self.load_label.set_label(_("Loaded"))
			else:
				msgBox = gtk.MessageDialog(parent=self.dialog, flags=gtk.DIALOG_MODAL, type=gtk.MESSAGE_ERROR, 
							buttons=gtk.BUTTONS_CLOSE, message_format=_("No more topic list!"))
				msgBox.connect("response", lambda a, b: msgBox.hide())
				msgBox.run()
				self.load_label.set_label(_("Loaded"))
					
		l = rb.Loader()
		l.get_url (url, loader_cb)
		self.load_label.set_label(_("Loading..."))
		print url
		return True
	
gconf_keys = {  'listType' : '/apps/rhythmbox/plugins/onlinemusic/listType',
		'listId': '/apps/rhythmbox/plugins/onlinemusic/listId',
		'listName': '/apps/rhythmbox/plugins/onlinemusic/listName'
		}
class Preference(object):
	def __init__(self):
		self.gconf_keys = gconf_keys
		self.client = gconf.client_get_default()
		
	def set_values(self, listType, listId, listName):
		print listName
		self.client.set_string(self.gconf_keys['listType'], listType)
		self.client.set_string(self.gconf_keys['listId'], listId)
		self.client.set_string(self.gconf_keys['listName'], listName)
		return True
	
	def get_prefs (self):
		listType = self.client.get_string(self.gconf_keys['listType'])
		listId = self.client.get_string(self.gconf_keys['listId'])
		listName = self.client.get_string(self.gconf_keys['listName'])
	
		return (listType, listId, listName)
