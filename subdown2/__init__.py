#!/usr/bin/env python

import sys
import urllib
import urllib2
import time
import gui
import os
import download
import simplejson
import memegrab
import md5
import datetime
import log
import threading
import Queue

helptext = """
(C) 2012, Kunal Mehta, under the MIT License

Syntax: subdown2 subreddit[,subreddit] pages [--force]

 - You can add as many subreddits as you wish, just split them with a comma (no spaces).
 - If an integer for pages is not set (or is not understood) it will be set to 1.
 - The force option will re-download all images and overwrite them. Default option is not to do so.
"""



queue = Queue.Queue()
IMAGE_Q = Queue.Queue()

class Client:

  def __init__(self, name, pages, force, top):
    self.name = name
    self.headers = {
      'User-agent': 'subdown2 by /u/legoktm -- https://github.com/legoktm/subdown2'
    }
    self.pages = pages
    self.force = force
    self.top = top
    self.r = 'r/%s' %(self.name)
    log.log('Starting %s' %(self.r))
    try:
      os.mkdir(self.name)
    except OSError:
      pass
    
  def parse(self, page):
    log.log('Grabbing page %s of %s from %s' %(page, self.pages, self.r))
    params = {}
    if self.top:
      url = 'http://reddit.com/%s/top/.json' %(self.r)
      params['t'] = 'all'
    else:
      url = 'http://reddit.com/%s/.json' %(self.r)
    
    if page != 1:
      params['after'] = self.after
    encoded = '?' + urllib.urlencode(params)
    url += encoded
    req = urllib2.Request(url, headers=self.headers)
    obj = urllib2.urlopen(req)
    text = obj.read()
    obj.close()
    try:
      data = simplejson.loads(text)
    except simplejson.decoder.JSONDecodeError:
      log.log('simplejson.decoder.JSONDecodeError',error=True)
      log.log(text, error=True)
      sys.exit(1)
    try:
      self.after = data['data']['after']
      items = data['data']['children']
    except KeyError:
      try:
        if data['error'] == 429:
          log.log('Too many requests on the reddit API, taking a break for a minute', error=True)
          time.sleep(60)
          self.parse(page)
          return
      except KeyError:
        log.log(data, error=True)    
        sys.exit(1)
    for item in items:
      item2 = item['data']
      #print item2
      new_dl = download.Downloader(self.name, self.force)
      queue.put((item2,new_dl))
    
    
  def run(self):
    for pg in range(1,self.pages+1):
      self.parse(pg)

def cleanup():
  try:
    os.remove('bad_imgur.jpg')
  except OSError:
    pass

class DownloadThread(threading.Thread):
  def __init__(self, queue):
    threading.Thread.__init__(self)
    self.queue = queue
  
  def process_url(self, object, dl_obj):
    try:
      self.__process_url(object, dl_obj)
    except Exception, e:
      log.log('Error %s on %s, skipping' % (str(e), object['url']), thread_name=self.getName(), error=True)
  
  def __process_url(self, object, dl_obj):
    domain = object['domain']
    url = object['url']
    dl_obj.setTime(object['created'])
    dl_obj.setTitle(object['title'])
    dl_obj.setThreadInfo(self.getName())

    if domain == 'imgur.com':
      dl_obj.Imgur(url)
    elif domain == 'i.imgur.com':
      dl_obj.Raw(url)
    elif domain == 'twitter.com':
      try:
        dl_obj.Twitter(url)
      except:
        log.log('Skipping %s since it is not supported yet' %(url), thread_name=self.getName(), error=True)
    elif domain == 'yfrog.com':
      dl_obj.yfrog(url)
    elif domain == 'pagebin.com':
      dl_obj.Pagebin(url)
    elif 'media.tumblr.com' in domain:
      dl_obj.Raw(url)
    elif 'reddit.com' in domain:
      print 'Skipping self/reddit post: "%s"' %(item2['title'])
    elif (domain == 'quickmeme.com') or (domain == 'qkme.me'):
      dl_obj.qkme(url)
    elif domain == 'bo.lt':
      dl_obj.bolt(url)
    else: #Download all the images on the page
      dl_obj.All(url)


  def run(self):
    while True:
      object, dl_obj = self.queue.get()
      self.process_url(object, dl_obj)
      self.queue.task_done()


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
    try:
      self.__raw(link)
    except urllib2.URLError,e:
      self.output('urllib2.URLError %s on %s' % (str(e), link), True)
    except httplib.BadStatusLine,e:
      self.output('httplib.BadStatusLine %s on %s' % (str(e), link), True)
    except urllib2.HTTPError,e:
      self.output('urllib2.HTTPError %s on %s' % (str(e), link), True)
    except:
      self.output('General error on %s' % link, True)
  def __raw(self, link):
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
      self.output('Skipping %s since it already exists' %(link))
      return
    #download the image, so add it to the queue
    IMAGE_Q.put((link, path, self.time))
    print 'Added to queue'

  def Imgur(self, link):
    if '.' in link.split('/')[-1]: #raw link but no i. prefix
      self.Raw(link)
      return
    #determine whether it is an album or just one image
    if '/a/' in link:
      #it's an album!
      self.output('Processing Imgur album: %s' %(link))
      link = link.split('#')[0]
      id = link.split('/a/')[1]
      api_link = 'http://api.imgur.com/2/album/%s.json' %(id)
      api = self.page_grab(api_link)
      try:
        data = simplejson.loads(api)
      except simplejson.decoder.JSONDecodeError:
        self.output(api, True)
        self.output(link, True)
        sys.exit()
      except TypeError:
        self.output(api, True)
        self.output(api_link, True)
        self.output(link, True)
        sys.exit()      
      for image in data['album']['images']:
        self.Raw(image['links']['original'])
      self.output('Finished Imgur album: %s' %(link))
    else:
      #it's a raw image
      id = link.split('/')[-1]
      api = self.page_grab('http://api.imgur.com/2/image/%s.json' %(id))
      data = simplejson.loads(api)
      self.Raw(data['image']['links']['original'])
    
  def Tumblr(self, link):
    self.output(self.help %(link), True)
  def Twitter(self, link):
    api = twitter.Api()
    try:
      id = int(link.split('/status/')[-1])
    except:
      self.output('Can\'t parse tweet: %s' %(link), True)
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
    #if 'yfrog.com' in final_url:
    #  self.yfrog(final_url)
    #else:
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
      self.output("Can't parse pagebin.com HTML page :(", True)
      self.output("Report %s a bug please!" %(link), True)
  def bolt(self, link):
    html = self.page_grab(link)
    x = re.findall('<img src="(.*?)"', html)
    try:
      imglink = x[0]
    except IndexError:
      self.output( link, True)
      return
    self.Raw(imglink)
  def qkme(self, link):
    self.output('Grabbing %s.' %(link))
    try:
      memegrab.get_image_qm(memegrab.read_url(link), self.reddit+'/')
    except:
      self.output('Error on %s' %(link), True)
  def All(self, link):
    #verify it is an html page, not a raw image.
    headers = self.page_grab(link, want_headers=True)
    for header in headers:
      if header.lower().startswith('content-type'):
        #right header
        is_image = header.startswith('image')
    if is_image: #means it is most likely an image
      self.Raw(link)
      return
    self.logger.debug('Skipping %s since it is not an image.' %(link))
    return
  def setTime(self, time):
    self.time = time
  def setTitle(self, title):
    self.title = title.replace(' ', '_').replace('/', '_')
  def setThreadInfo(self, name):
    self.thread_name = name
  def output(self, text, error = False):
    newtext = '%s-%s: %s' % (datetime.datetime.now(), self.thread_name, text)
    if error:
      self.logger.error(newtext)
    else:
      self.logger.debug(newtext)
  

  def page_grab(self, link, want_headers=False):
    if want_headers:
      open = urllib2.urlopen(link)
      headers = open.info().headers
      open.close()
      return headers
    headers = {'User-agent': 'subdown2 (https://github.com/legoktm/subdown2)'}
    req = urllib2.Request(link, headers=headers)
    obj = urllib2.urlopen(req)
    text = obj.read()
    obj.close()
    return text
  

def initialize_imgur_checking():
  if not os.path.isfile('.bad_imgur.jpg'):
    obj = urllib.urlopen('http://i.imgur.com/sdlfkjdkfh.jpg')
    text = obj.read()
    obj.close()
    f = open('.bad_imgur.jpg', 'w')
    f.write(text)
    f.close()
  else:
    f = open('.bad_imgur.jpg', 'r')
    text = f.read()
    f.close()
  digest = md5.new(text).digest()
  return digest


class Image_Grab_Thread(threading.Thread):
  def __init__(self, queue):
    threading.Thread.__init__(self)
    self.queue = queue
    self.bad_imgur = initialize_imgur_checking()
  
  def process_link(self, link, filename, time):
    headers = {'User-agent': 'subdown2 (https://github.com/legoktm/subdown2)'}
    req = urllib2.Request(link, headers=headers)
    obj = urllib2.urlopen(req)
    text = obj.read()
    obj.close()
    if md5.new(text).digest() == self.bad_imgur:
      print '%s has been removed from imgur.com' %(link)
    f = open(filename, 'w')
    f.write(text)
    f.close()
    os.utime(filename, (time, time))
    print 'Downloaded %s' %(link)
    print 'Set time to %s' %(time)
  
  
  def run(self):
    while True:
      link, filename, time = self.queue.get()
      self.process_link(link, filename, time)
      self.queue.task_done()
  






def main():
  for i in range(10):
    t = DownloadThread(queue)
    t.setDaemon(True)
    t.start()
    x = Image_Grab_Thread(IMAGE_Q)
    x.setDaemon(True)
    x.start()
  try:
    subreddits = sys.argv[1]
    force = False
    top = False
    pg = 1
    for arg in sys.argv:
      if arg == '--force':
        force = True
      if arg == '--top':
        top = True
      if arg.startswith('--pages:'):
        pg = int(arg.split(':')[-1])
    
        
    for subreddit in subreddits.split(','):
      app = Client(subreddit,pg, force, top)
      app.run()
    queue.join()
    IMAGE_Q.join()
  except IndexError: #no arguments provided
    log.log(helptext,error=True)
    #gui.main()
  except KeyboardInterrupt:
    log.log('KeyboardInterrupt recieved.',error=True)
    sys.exit(1)
    




if __name__ == "__main__":
  main()
