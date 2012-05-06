#!/usr/bin/python

import sys
import urllib
import urllib2
import re
import time
try:
  import simplejson
except ImportError:
  import json as simplejson #No speedups :(
import os

"""
(C) 2012, Kunal Mehta, under the MIT License

Syntax: python subdown.py subreddit pages

"""

blacklist = ['youtube.com','hollywoodreporter.com','news.stylecaster.com']

class Downloader:
  """
  Custom downloaders for different websites.
  Right now all traffic is directed through "Raw" which simply downloads the raw image file.
  """
  
  def __init__(self, reddit):
    self.help = "Sorry, %s doesn't work yet :("
    self.reddit = reddit
  def Imgur(self, link):
    if '.' in link.split('/')[-1]: #raw link but no i. prefix
      self.Raw(link)
      return
    obj = urllib.urlopen(link)
    html = obj.read()
    obj.close()
    x = re.findall('<link rel="image_src" href="http://i.imgur.com/(.*?)" />', html)
    try:
      ilink = 'http://i.imgur.com/%s' %(x[0])
    except IndexError:
      print link
      return
    self.Raw(ilink)
  def Tumblr(self, link):
    print self.help %(link)
  def Raw(self, link):
    print 'Downloading %s' %(link)
    link = link.split('?')[0]
    filename = link.split('/')[-1]
    if filename == '':
      filename = 'lol.txt'
    obj = urllib.urlopen(link)
    img = obj.read()
    obj.close()
    f = open(self.reddit +'/'+ filename, 'w')
    f.write(img)
    f.close()
  def Twitter(self, link):
    print self.help %(link)
  def Pagebin(self, link):
    obj = urllib.urlopen(link)
    html = obj.read()
    obj.close()
    x=re.findall('<img alt="(.*?)" src="(.*?)" style="width: (.*?)px; height: (.*?)px; " />', html)
    try:
      iimgur = x[0][1]
      self.Raw(iimgur)
    except KeyError:
      print "Can't parse pagebin.com HTML page :("
      print "Report %s a bug please!" %(link)
  def bolt(self, link):
    obj = urllib.urlopen(link)
    html = obj.read()
    obj.close()
    x = re.findall('<img src="(.*?)"', html)
    try:
      imglink = x[0]
    except IndexError:
      print link
      return
    self.Raw(imglink)



class Subreddit:

  def __init__(self, name, pages,blacklist=[]):
    self.name = name
    self.blacklist = blacklist
    self.headers = {
      'User-agent': 'subdown2.py by /u/legoktm'
    }
    self.pages = pages
    self.r = 'r/%s' %(self.name)
    print 'Starting %s' %(self.r)
    self.dl = Downloader(self.name)
    try:
      os.mkdir(self.name.lower())
    except OSError:
      pass
    
  def parse(self, page):
    print 'Grabbing page %s of %s from %s' %(page, self.pages, self.r)
    if page != 1:
      url = 'http://reddit.com/%s/.json?after=%s' %(self.r, self.after)
    else:
      url = 'http://reddit.com/%s/.json' %(self.r)
    req = urllib2.Request(url, headers=self.headers)
    obj = urllib2.urlopen(req)
    text = obj.read()
    obj.close()
    data = simplejson.loads(text)
    try:
      self.after = data['data']['after']
      items = data['data']['children']
    except KeyError:
      try:
        if data['error'] == 429:
          print 'Too many requests on the reddit API, taking a break for a minute'
          time.sleep(60)
      except KeyError:
        print data    
        sys.exit(1)
    for item in items:
      item2 = item['data']
      #print item2
      if item2['domain'] == 'imgur.com':
        self.dl.Imgur(item2['url'])
      elif item2['domain'] == 'i.imgur.com':
        self.dl.Raw(item2['url'])
      elif item2['domain'] == 'twitter.com':
        self.dl.Twitter(item2['url'])
      elif item2['domain'] == 'pagebin.com':
        self.dl.Pagebin(item2['url'])
      elif 'tumblr.com' in item2['domain']:
        self.dl.Raw(item2['url'])
      elif item2['domain'] == 's-ak.buzzfed.com':
        self.dl.Raw(item2['url'])
      elif item2['domain'] in self.blacklist:
        print 'Skipping %s since it is in the blacklist' %(item2['url'])    
      elif item2['domain'] == 'self.EmmaWatson':
        print 'Skipping self post: "%s"' %(item2['title'])
      else: #Download as a raw image
        self.dl.Raw(item2['url'])    
  def run(self):
    for pg in range(1,self.pages+1):
      self.parse(pg)
    

if __name__ == "__main__":
  sub = sys.argv[1]
  if len(sys.argv) == 3:
    pg = int(sys.argv[2])
  else:
    pg = 1
  app = Subreddit(sub,pg,blacklist)
  app.run()
