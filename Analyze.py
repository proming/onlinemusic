# -*- Mode: python; coding: utf-8; tab-width: 8; indent-tabs-mode: t; -*- 
import re
import hashlib
import math
import traceback
from urllib2 import Request, urlopen, URLError
import urllib2
from xml.dom.minidom import parse, parseString

GOOGLE_PLAYER_KEY = "ecb5abdc586962a6521ffb54d9d731a0";
TIMEOUT = 20
def decode(html):
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

def getSongByURL(xmlurl):
	req = Request(xmlurl)
	req.add_header("User-Agent", "Mozilla/5.0")
	req.add_header("Referer", "http://www.google.cn/music/player")
	try:
		response = urlopen(req, timeout=TIMEOUT)
		xmlback = response.read()
		dom1 = parseString(xmlback)
		songUrl = dom1.getElementsByTagName('songUrl')[0].childNodes[0].nodeValue
		
		lyricsUrl = None
		elements = dom1.getElementsByTagName('lyricsUrl')
		if len(elements) > 0:
			childNodes = elements[0].childNodes
			if len(childNodes) > 0:
				lyricsUrl = childNodes[0].nodeValue
	
		imageUrl = None
		elements = dom1.getElementsByTagName('albumThumbnailLink')
		if len(elements) > 0:
			childNodes = elements[0].childNodes
			if len(childNodes) > 0:
				imageUrl = childNodes[0].nodeValue
	
		genre = None
		elements = dom1.getElementsByTagName('genre')
		if len(elements) > 0:
			childNodes = elements[0].childNodes
			if len(childNodes) > 0:
				genre = childNodes[0].nodeValue
	
		song={'url':songUrl,
			'image':imageUrl,
			'lyrics':lyricsUrl,
			'genre':genre}
		return song
	except Exception, e:
		traceback.print_exc()
		print 'Load song url error'
	return None
  
def getSongById(songId):
	hash = hashlib.md5(GOOGLE_PLAYER_KEY + songId).hexdigest()
	xmlurl = "http://www.google.cn/music/songstreaming?id=" + songId + "&output=xml&sig=" + hash
  
	return getSongByURL(xmlurl)

def getLyrics(lyricsURL):
	req = Request(lyricsURL)
	req.add_header("User-Agent", "Mozilla/5.0")
	req.add_header("Referer", "http://www.google.cn/music/player")
	try:
		response = urlopen(req, timeout=TIMEOUT)
		content = response.read()
		return content
	except Exception, e:
		traceback.print_exc()
		print 'Load lyrics error'
	return None

def getLyricsByFile(filePath):
	#filePath = os.path.join(self.path, self.topicFileName)
	infile = open(filePath, 'r')
	xmlData = ''
	for line in infile:
		xmlData += line.decode("gbk")
		#print line.decode("gbk")
  
	infile.close()
	return xmlData
  
def getSongList(xmlurl, flag):
	req = Request(xmlurl)
	req.add_header("User-Agent", "Mozilla/5.0")
	req.add_header("Referer", "http://www.google.cn/music/player")
	try:
		response = urlopen(req, timeout=TIMEOUT)
		xmlback=response.read()
		print xmlurl + '\n' + xmlback
		dom1=parseString(xmlback)
		genre = None
		if flag:
			genre=dom1.getElementsByTagName('info')[0].childNodes[1].childNodes[0].nodeValue
		elements=dom1.getElementsByTagName('song')
		#print len(elements)
		songs = []
		for element in elements:
			id=element.getElementsByTagName('id')[0].childNodes[0].nodeValue
			name=element.getElementsByTagName('name')[0].childNodes[0].nodeValue
			artist = ''
			for artiest_element in element.getElementsByTagName('artist'):
				if artist != '': artist += ','
				artist += artiest_element.childNodes[0].nodeValue
			album=element.getElementsByTagName('album')[0].childNodes[0].nodeValue
			hasFullLyrics=element.getElementsByTagName('hasFullLyrics')[0].childNodes[0].nodeValue
			canBeDownloaded=element.getElementsByTagName('canBeDownloaded')[0].childNodes[0].nodeValue
			durationf=float(element.getElementsByTagName('duration')[0].childNodes[0].nodeValue)
			duration=int(math.ceil(durationf))
	  
			#print 'soundId:',id,"@",'soundName:',name,'artist:',artist
			hash = hashlib.md5(GOOGLE_PLAYER_KEY + id).hexdigest()
			url="http://www.google.cn/music/songstreaming?id=" + id + "&output=xml&sig=" + hash
			song={'name':name,
				'artist':artist,
				'album':album,
				'duration':duration,
				'url':url,
				'genre':genre,
				'id':id}
			songs.append(song)
		return songs
	except Exception, e:
		traceback.print_exc()
		print 'Load song list error'
	return None

def parseSongList(self,html):
	#html=re.sub('<[/]*b>', '', html)#<td class=\"%s[ BottomBorder]*\">[\n]*<a[^>]*>[^<]*
	titleReg= re.compile("<td class=\"Title BottomBorder\"><a[^>]*>[^<]*")
	artistReg= re.compile("<td class=\"Artist BottomBorder\">\n<a[^>]*>[^<]*")
	titles=titleReg.findall(html)
	artists=artistReg.findall(html)
	songs=[]
	for title,artist in zip(titles,artists):
		id=title.split("%3D")[1].split("%")[0]
		name=decode(title.split(">")[2])
		artist=decode(artist.split(">")[2])
		#print 'soundId:',id,"@",'soundName:',name,'artist:',artist
		hash = hashlib.md5(self.GOOGLE_PLAYER_KEY + id).hexdigest()
		url="http://www.google.cn/music/songstreaming?id=" + id + "&output=xml&sig=" + hash
		song={'name':name,'artist':artist,'url':url}
		songs.append(song)
	return songs
	
def getTopicList(data):
	try:
		html = data
	  
		picRe = re.compile("<td class=\"td-thumb-big\"><a href=\"/music/url\?q=/music/topiclisting[^<]*<img \nalt=\"\"\n src=\"(?P<picURL>[^\"]*)\"")
		titleRe = re.compile("<a class=\"topic_title\"[^D]*D(?P<id>[^%]*)%[^>]*>(?P<title>[^<]*)")
		descRe = re.compile("<td class=\"topic_description\"><div title=\"(?P<desc_detail>[^\"]*)\">(?P<desc>[^<]*)<")#>[^\(]*\((?P<time>[^\)]*)
	  
		picList = picRe.findall(html)
		titleList = titleRe.findall(html)
		descList = descRe.findall(html)
	  
		length = len(picList)
		topic_list = []
		for i in range(0, length):
			topicPicURL = picList[i]
			topicId, topicTitle = titleList[i]
			topicDescDetail, topicDesc = descList[i]
			topic = {
				  'id' : topicId,
				  'name' : replaceSymbol(decode(topicTitle)),
				  'picURL' : topicPicURL,
				  'desc' : replaceSymbol(decode(topicDesc)),
				  'type' : 'topic',
				  'group' : 'topic'
			}
			#print topic
			topic_list.append(topic)
		return topic_list
	except Exception, e:
		traceback.print_exc()
		print 'Load topic list error'
	return None
	
result = {
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
		
def decode(html):
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
	
def replaceSymbol(text):
	codeReg=re.compile('&[a-zA-Z1-9]+;')
	ite=codeReg.finditer(text)
	res=""
	n=0
	for e in ite:
		res+=text[n:e.start()]
		n=e.end()
		words=e.group()
		res += result.get(words, lambda x: x)(words)
	res+=text[n:]
	res = res.replace('\n','')
	return res
