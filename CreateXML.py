# -*- Mode: python; coding: utf-8; tab-width: 8; indent-tabs-mode: t; -*-
import re
from urllib2 import Request, urlopen, URLError
import urllib2
from xml.dom.minidom import parse, parseString
import os
import traceback

class CreateXML(object):
	def __init__(self):
		self.path = os.getenv('HOME')
		self.result = {
		  "&quot;" : lambda x : x,
		  "&amp;" : lambda x : x,
		  "&lt;" : lambda x : x,
		  "&gt;" : lambda x : x,
		  "&nbsp;" : lambda x : " ",
		  "&ldquo;" : lambda x : u"\u201C",
		  "&rdquo;" : lambda x : u"\u201D",
		  "&hellip;" : lambda x : u"\u2026",
		  "&mdash;" : lambda x : u"\u2014",
		  "&middot;" : lambda x : u"\u00B7",
		  "&lsquo;" : lambda x : u"\u2018",
		  "&rsquo;" : lambda x : u"\u2019",
		  "&sbquo;" : lambda x : u"\u201A",
		  "&bull;" : lambda x : u"\u2022"
		}
		
	def decode(self, html):
		codeReg=re.compile('&#[\d]+;')
		ite=codeReg.finditer(html)
		res=""
		n=0
		for e in ite:
			res+=html[n:e.start()]
			n=e.end()
			words=e.group()
			res+=unichr(int(words[2:len(words)-1]))
		res+=html[n:]
		return res
	
	def replaceSymbol(self, text):
		codeReg=re.compile('&[a-zA-Z1-9]+;')
		ite=codeReg.finditer(text)
		res=""
		n=0
		for e in ite:
			res+=text[n:e.start()]
			n=e.end()
			words=e.group()
			res += self.result.get(words, lambda x: x)(words)
		res+=text[n:]
		return res
  
	def pareseHTML(self):pass
	def createFile(self, groups, charts):
		filePath = os.path.join(self.path, self.fileName)
		infile = open(filePath, 'w')
		infile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
		infile.write('<result>\n')
		for group in groups:
			infile.write('	<chartList>\n')
			infile.write('		<listId>' + group['id'] + '</listId>\n')
			infile.write('		<listName>' + group['name'].encode("utf-8") + '</listName>\n')
		  
			for chart in charts:
				if chart['group'] == group['id']:
					infile.write('		<chart>\n')
					for child in self.chartChild:
						infile.write('			<' + child + '>' + chart[child].encode("utf-8") + '</' + child + '>\n')
					infile.write('		</chart>\n')
		  
			infile.write('	</chartList>\n')
		infile.write('</result>')
		infile.close()

class CreateChartXML(CreateXML):
	def __init__(self):
		CreateXML.__init__(self)
		self.url = 'http://www.google.cn/music/chartlisting?q=chinese_new_songs_cn&cat=song'
		self.fileName = 'chartlist.xml'
		self.chartChild = ['id', 'name', 'type']
		
	def pareseHTML(self):
		try:
			req = Request(self.url)
			response = urlopen(req)
			html = response.read()
			groupRe = re.compile("<a id=\"grouping_title_(?P<id>[^\"]*)\"[^>]*>(?P<name>[^<]*)")
			chartRe1 = re.compile("<a class=\"navigation_panel_chart_item[^>]*>[^<]*")
			chartRe2 = re.compile("<a class=\"navigation_panel_chart_item[^D]*D(?P<id>[^%]*)\%[^D]*D(?P<type>[^%]*)[^D]*D(?P<group>[^&]*)&[^>]*>(?P<name>[^<]*)");
		  
			groupStrList = groupRe.findall(html)
			chartStrList = chartRe1.findall(html)
		  
			groups = []
			for groupStr in groupStrList:
				groupId, groupName = groupStr
				group = {'id' : groupId, 'name' : self.decode(groupName)}
				groups.append(group)
		  
			charts = []
			chart = {'id' : 'chinese_new_songs_cn', 'name' : u'华语新歌', 'type' : 'song', 'group' : 'new-release_music'}
			charts.append(chart)
			#print len(chartStrList)
			for chartStr in chartStrList:
				#print chartStr
				m = chartRe2.match(chartStr)
				if m:
				  chartId = m.group('id')
				  chartName = m.group('name')
				  chartType = m.group('type')
				  chartGroup = m.group('group')
				  chart = {'id' : chartId, 'name' : self.decode(chartName), 'type' : chartType, 'group' : chartGroup}
				  charts.append(chart)
			  
			return (groups, charts)
		except Exception, e:
			traceback.print_exc()
			return ([], [])

class CreateTopicXML(CreateXML):
	def __init__(self):
		CreateXML.__init__(self)
		self.url = 'http://www.google.cn/music/topiclistingdir?cat=song&start=%d'
		self.fileName = 'topiclist.xml'
		self.chartChild = ['id', 'name', 'type', 'picURL', 'desc', 'time']
	def pareseHTML(self):
		try:
			groups = []
			charts = []
			group = {'id' : 'topic', 'name' : u'专题'}
			groups.append(group)
		  
			for i in range(0, 3):
				url = self.url % (i * 14)
				print url
				chart = self.paresePage(url)
				if chart is not None:
					charts.append(chart)
				#print charts
			return (groups, charts)
		except Exception, e:
			traceback.print_exc()
			return ([], [])
	  
	def paresePage(self, url):
		try:
			req = Request(url)
			response = urlopen(req)
			html = response.read()
		  
			picRe = re.compile("<td class=\"td-thumb-big\"><a href=\"/music/url\?q=/music/topiclisting[^<]*<img \nalt=\"\"\n src=\"(?P<picURL>[^\"]*)\"")
			titleRe = re.compile("<a class=\"topic_title\"[^D]*D(?P<id>[^%]*)%[^>]*>(?P<title>[^<]*)")
			descRe = re.compile("<td class=\"topic_description\"><div title=\"(?P<desc>[^\"]*)\">[^\(]*\((?P<time>[^\)]*)")
		  
			picList = picRe.findall(html)
			titleList = titleRe.findall(html)
			descList = descRe.findall(html)
		  
			length = len(picList)
			for i in range(0, length):
				chartPicURL = picList[i]
				chartId, chartTitle = titleList[i]
				chartDesc, chartTime = descList[i]
				print 'url:%s\nid:%s\ntitle:%s\ndesc:%s\ntime:%s' % (chartPicURL, chartId, chartTitle, chartDesc, chartTime)
				chart = {
					  'id' : chartId,
					  'name' : self.replaceSymbol(self.decode(chartTitle)),
					  'picURL' : chartPicURL,
					  'desc' : self.replaceSymbol(self.decode(chartDesc)),
					  'time' : self.decode(chartTime),
					  'type' : 'topic',
					  'group' : 'topic'
				}
			return chart
		except Exception, e:
			traceback.print_exc()
			return None
  
if __name__ == '__main__':
	createChartXML = CreateChartXML()
	groups, charts = createChartXML.pareseHTML()
	createChartXML.createFile(groups, charts)


	createTopicXML = CreateTopicXML()
	groups, charts = createTopicXML.pareseHTML()
	createTopicXML.createFile(groups, charts)
