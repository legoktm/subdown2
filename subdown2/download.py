#!/usr/bin/python

import memegrab
import simplejson
import urllib
import urllib2
import md5
import os
import twitter
from BeautifulSoup import BeautifulSoup


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
  All traffic is directed through "Raw" which simply downloads the raw image file.
  """
  
  def __init__(self, reddit, force, logger):
    self.help = "Sorry, %s doesn't work yet :("
    self.reddit = reddit
    self.bad_imgur = initialize_imgur_checking()
    self.force = force
    self.retry = False
    self.time = False
    self.logger = logger
    self.title = False
  def Raw(self, link):
    link = link.split('?')[0]
    old_filename = link.split('/')[-1]
    extension = old_filename.split('.')[-1]
    link_hash = md5.new(link).hexdigest()
    filename = self.title + '.' + link_hash + '.' + extension #the hash is used to prevent overwriting multiple submissions with the same filename
    if filename == '':
      return
    path = self.reddit+'/'+filename
    if os.path.isfile(path) and (not self.force):
      os.utime(path, (self.time, self.time))
      self.logger.debug('Skipping %s since it already exists' %(link))
      return
    self.logger.debug('Downloading %s' %(link))
    try:
      img = self.page_grab(link)    
    except IOError,e:
      self.logger.error('IOError: %s' %(str(e)))
      return
    except urllib2.HTTPError, e:
      self.logger.error('urllib2.HTTPError: %s' %(str(e)))
      if self.retry:
        self.logger.error('Error occurred twice on %s, now skipping' %(link))
        self.retry = False
        return
      self.retry = True
      self.Raw(link)
      self.retry = False
    if md5.new(img).digest() == self.bad_imgur:
      self.logger.error('%s has been removed from imgur.com' %(link))
      return
    f = open(path, 'w')
    f.write(img)
    f.close()
    #set new filetime
    os.utime(path, (self.time, self.time))
    self.logger.debug('Set time to %s' %(self.time))
  def Imgur(self, link):
    if '.' in link.split('/')[-1]: #raw link but no i. prefix
      self.Raw(link)
      return
    #determine whether it is an album or just one image
    if '/a/' in link:
      #it's an album!
      self.logger.debug('Processing Imgur album: %s' %(link))
      link = link.split('#')[0]
      id = link.split('/a/')[1]
      api = self.page_grab('http://api.imgur.com/2/album/%s.json' %(id))
      try:
        data = simplejson.loads(api)
      except simplejson.decoder.JSONDecodeError:
        self.logger.error( api)
        self.logger.error( link)
        sys.exit()
      for image in data['album']['images']:
        self.Raw(image['links']['original'])
    else:
      #it's a raw image
      id = link.split('/')[-1]
      api = self.page_grab('http://api.imgur.com/2/image/%s.json' %(id))
      data = simplejson.loads(api)
      self.Raw(data['image']['links']['original'])
    
  def Tumblr(self, link):
    self.logger.error( self.help %(link))
  def Twitter(self, link):
    api = twitter.Api()
    try:
      id = int(link.split('/status/')[-1])
    except:
      self.logger.error('Can\'t parse tweet: %s' %(link))
      return
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
      self.logger.error( "Can't parse pagebin.com HTML page :(")
      self.logger.error( "Report %s a bug please!" %(link))
  def bolt(self, link):
    html = self.page_grab(link)
    x = re.findall('<img src="(.*?)"', html)
    try:
      imglink = x[0]
    except IndexError:
      self.logger.error( link)
      return
    self.Raw(imglink)
  def qkme(self, link):
    self.logger.debug('Grabbing %s.' %(link))
    try:
      memegrab.get_image_qm(memegrab.read_url(link), self.reddit+'/')
    except:
      self.logger.error('Error on %s' %(link))
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
    self.logger.debug('Skipping %s since it is an HTML page.' %(link))
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
  def setTime(self, time):
    self.time = time
  def setTitle(self, title):
    self.title = title.replace(' ', '_').replace('/', '_')
  def page_grab(self, link):
    headers = {'User-agent': 'subdown2 (https://github.com/legoktm/subdown2)'}
    req = urllib2.Request(link, headers=headers)
    obj = urllib2.urlopen(req)
    text = obj.read()
    obj.close()
    return text
  
