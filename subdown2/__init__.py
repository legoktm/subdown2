#!/usr/bin/python

import sys
import urllib
import urllib2
import re
import time
import memegrab
import gui
import twitter
import md5
import os
try:
  import simplejson
except ImportError:
  import json as simplejson #No speedups :(
  print 'WARNING: You should install simplejson for faster parsing'
import os
from BeautifulSoup import BeautifulSoup

helptext = """
(C) 2012, Kunal Mehta, under the MIT License

Syntax: subdown2 subreddit[,subreddit] pages [--force]

 - You can add as many subreddits as you wish, just split them with a comma (no spaces).
 - If an integer for pages is not set (or is not understood) it will be set to 1.
 - The force option will re-download all images and overwrite them. Default option is not to do so.
"""

def initialize_imgur_checking():
  if not os.path.isfile('bad_imgur.jpg'):
    obj = urllib.urlopen('http://i.imgur.com/sdlfkjdkfh.jpg')
    text = obj.read()
    obj.close()
    f = open('bad_imgur.jpg', 'w')
    f.write(text)
    f.close()
  else:
    f = open('bad_imgur.jpg', 'r')
    text = f.read()
    f.close()
  digest = md5.new(text).digest()
  return digest



class Downloader:
  """
  Custom downloaders for different websites.
  Right now all traffic is directed through "Raw" which simply downloads the raw image file.
  """
  
  def __init__(self, reddit, force):
    self.help = "Sorry, %s doesn't work yet :("
    self.reddit = reddit
    self.bad_imgur = initialize_imgur_checking()
    self.force = force
  def Imgur(self, link):
    if '.' in link.split('/')[-1]: #raw link but no i. prefix
      self.Raw(link)
      return
    html = self.page_grab(link)
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
    link = link.split('?')[0]
    filename = link.split('/')[-1]
    if filename == '':
      return
    if os.path.isfile(self.reddit+'/'+filename) and (not self.force):
      print 'Skipping %s since it already exists' %(link)
      return
    print 'Downloading %s' %(link)
    try:
      img = self.page_grab(link)    
    except IOError,e:
      print 'IOError: %s' %(str(e))
      return
    if md5.new(img).digest() == self.bad_imgur:
      print '%s has been removed from imgur.com' %(link)
      return
    f = open(self.reddit +'/'+ filename, 'w')
    f.write(img)
    f.close()
  def Twitter(self, link):
    api = twitter.Api()
    try:
      id = int(link.split('/status/')[-1])
    except:
      print 'Can\'t parse tweet: %s' %(link)
    stat = api.GetStatus(id)
    text = stat.text
    parsed = text[text.find("http://"):text.find("http://")+21]
    if len(parsed) == 1: #means it didnt find it
      parsed = text[text.find("https://"):text.find("https://")+22]
      did_it_work = len(parsed) != 1
      if not did_it_work:
        raise
    #expand the url so we can send it through other sets of regular expressions
    ret = self.page_grab('http://expandurl.appspot.com/expand', urllib.urlencode({'url':parsed}))
    print ret
    jsond = simplejson.loads(ret)
    if jsond['status'].lower() == 'ok':
      final_url = jsond['end_url']
    else:
      raise
    if 'yfrog.com' in final_url:
      self.yfrog(final_url)
    else:
      self.All(final_url)
  def yfrog(self, link):
    text = self.page_grab(link)
    image_url = text[text.find('<div class="label">Direct:&nbsp;&nbsp;<a href="')+47:text.find('" target="_blank"><img src="/images/external.png" alt="Direct"/>')]
    self.Raw(image_url)
  def Pagebin(self, link):
    html = self.page_grab(link)
    x=re.findall('<img alt="(.*?)" src="(.*?)" style="width: (.*?)px; height: (.*?)px; " />', html)
    try:
      iimgur = x[0][1]
      self.Raw(iimgur)
    except KeyError:
      print "Can't parse pagebin.com HTML page :("
      print "Report %s a bug please!" %(link)
  def bolt(self, link):
    html = self.page_grab(link)
    x = re.findall('<img src="(.*?)"', html)
    try:
      imglink = x[0]
    except IndexError:
      print link
      return
    self.Raw(imglink)
  def qkme(self, link):
    memegrab.get_image_qm(memegrab.read_url(link), self.reddit+'/')
  def All(self, link):
    #verify it is an html page, not a raw image.
    open = urllib2.urlopen(link)
    headers = open.info().headers
    open.close()
    for header in headers:
      if header.lower().startswith('content-type'):
        #right header
        is_html = 'text/html' in header
    if not is_html: #means it is most likely an image
      self.Raw(link)
      return
    print 'Skipping %s since it is an HTML page.' %(link)
    return #Don't download html pages
    ### THIS FUNCTION IS NOT READY YET
    html = self.page_grab(link)
    soup = BeautifulSoup(html)
    imgs = soup.findAll('img')
    for img in imgs:
      try:
        url = img['src']
        self.Raw(url)
      except:
        pass
    
  def page_grab(self, link):
    headers = {'User-agent': 'subdown2 (http://pypi.python.org/subdown2)'}
    req = urllib2.Request(link, headers=headers)
    obj = urllib2.urlopen(req)
    text = obj.read()
    obj.close()
    return text
  



class Client:

  def __init__(self, name, pages, force):
    self.name = name
    self.headers = {
      'User-agent': 'subdown2 by /u/legoktm -- https://github.com/legoktm/subdown2'
    }
    self.pages = pages
    self.force = force
    self.r = 'r/%s' %(self.name)
    print 'Starting %s' %(self.r)
    self.dl = Downloader(self.name, self.force)
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
    try:
      data = simplejson.loads(text)
    except simplejson.decoder.JSONDecodeError:
      print text
      sys.exit(1)
    try:
      self.after = data['data']['after']
      items = data['data']['children']
    except KeyError:
      try:
        if data['error'] == 429:
          print 'Too many requests on the reddit API, taking a break for a minute'
          time.sleep(60)
          self.parse(page)
          return
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
        try:
          self.dl.Twitter(item2['url'])
        except:
          print 'Skipping %s since it is not supported yet' %(item2['url'])
      elif item2['domain'] == 'pagebin.com':
        self.dl.Pagebin(item2['url'])
      elif 'media.tumblr.com' in item2['domain']:
        self.dl.Raw(item2['url'])
      elif 'self.' in item2['domain']:
        print 'Skipping self post: "%s"' %(item2['title'])
      elif (item2['domain'] == 'quickmeme.com') or (item2['domain'] == 'qkme.me'):
        self.dl.qkme(item2['url'])
      elif item2['domain'] == 'bo.lt':
        self.dl.bolt(item2['url'])
      else: #Download all the images on the page
        try:
          self.dl.All(item2['url'])
        except:
          print 'Error-on %s' %(item2['url'])
  def run(self):
    for pg in range(1,self.pages+1):
      self.parse(pg)

def cleanup():
  try:
    os.remove('bad_imgur.jpg')
  except OSError:
    pass


def main():
  try:
    subreddits = sys.argv[1]
    if len(sys.argv) >= 3:
      pg = int(sys.argv[2])
    else:
      pg = 1
    force = False
    for arg in sys.argv:
      if arg == '--force':
        force = True
        
    for subreddit in subreddits.split(','):
      app = Client(subreddit,pg, force)
      app.run()
  except IndexError: #no arguments provided
    print helptext
    #gui.main()
  finally:
    cleanup()
    




if __name__ == "__main__":
  main()
