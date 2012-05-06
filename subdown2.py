#!/usr/bin/python

import sys
import urllib
import re
import simplejson

"""
(C) 2012, Kunal Mehta, under the MIT License

Syntax: python subdown.py subreddit pages

"""



class Downloader:
  """
  Custom downloaders for different websites.
  Right now all traffic is directed through "Raw" which simply downloads the raw image file.
  """
  
  def __init__(self):
    self.help = "Sorry, doesn't work yet :("
  def Imgur(self, link):
    obj = urllib.urlopen(link)
    html = obj.read()
    obj.close()
      
  def Tumblr(self, link):
    print self.help
  def Raw(self, link):
    print 'Downloading %s' %(link)
    filename = filename.split('?')[0]
    filename = link.split('/')[-1]
    if filename == '':
      filename = 'lol.txt'
    obj = urllib.urlopen(link)
    img = obj.read()
    obj.close()
    f = open(filename, 'w')
    f.write(img)
    f.close()
  def Twitter(self, link):
    print self.help
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



class Subreddit:

  def __init__(self, name, pages):
    self.name = name
    self.pages = pages
    self.r = 'r/%s' %(self.name)
    print 'Starting %s' %(self.r)
    self.dl = Downloader()
    
  def parse(self, page):
    print 'Grabbing %s of %s' %(page, self.r)
    url = 'http://reddit.com/%s/.json' %(self.r)
    print url
    obj = urllib.urlopen(url)
    text = obj.read()
    obj.close()
    data = simplejson.loads(text)
    items = data['data']['children']
    for item in items:
      item2 = item['data']
      print item2
      if item2['domain'] == 'imgur.com':
        self.dl.Imgur(item2['url'])
      elif item2['domain'] == 'i.imgur.com':
        self.dl.Raw(item2['url'])
      elif item2['domain'] == 'twitter.com':
        self.dl.Twitter(item2['url'])
      elif item2['domain'] == 'pagebin.com':
        self.dl.Pagebin(item2['url'])
      else: #Hope that it's a raw link?
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
  app = Subreddit(sub,pg)
  app.run()
