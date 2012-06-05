#!/usr/bin/env python

import sys
import urllib
import urllib2
import time
import gui
import os
import download
import simplejson
import log


helptext = """
(C) 2012, Kunal Mehta, under the MIT License

Syntax: subdown2 subreddit[,subreddit] pages [--force]

 - You can add as many subreddits as you wish, just split them with a comma (no spaces).
 - If an integer for pages is not set (or is not understood) it will be set to 1.
 - The force option will re-download all images and overwrite them. Default option is not to do so.
"""



logger = log.Logger()




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
    logger.debug('Starting %s' %(self.r))
    self.dl = download.Downloader(self.name, self.force, logger)
    try:
      os.mkdir(self.name)
    except OSError:
      pass
    
  def parse(self, page):
    logger.debug('Grabbing page %s of %s from %s' %(page, self.pages, self.r))
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
      logger.error('simplejson.decoder.JSONDecodeError')
      logger.error(text)
      sys.exit(1)
    try:
      self.after = data['data']['after']
      items = data['data']['children']
    except KeyError:
      try:
        if data['error'] == 429:
          logger.error('Too many requests on the reddit API, taking a break for a minute')
          time.sleep(60)
          self.parse(page)
          return
      except KeyError:
        logger.error(data)    
        sys.exit(1)
    for item in items:
      item2 = item['data']
      #print item2
      self.dl.setTime(item2['created'])
      self.dl.setTitle(item2['title'])
      try:
        self.process_url(item2)
      except KeyboardInterrupt:
        logger.error('Signal recieved')
        sys.exit(1)
      except urllib2.HTTPError:
        logger.error('HTTP Error on %s.' %(item2['url']))
      except:
        logger.error('Error-on %s.' %(item2['url']))

  def process_url(self, object):
    domain = object['domain']
    url = object['url']
    if domain == 'imgur.com':
      self.dl.Imgur(url)
    elif domain == 'i.imgur.com':
      self.dl.Raw(url)
    elif domain == 'twitter.com':
      try:
        self.dl.Twitter(url)
      except:
        logger.error('Skipping %s since it is not supported yet' %(url))
    elif domain == 'yfrog.com':
      self.dl.yfrog(url)
    elif domain == 'pagebin.com':
      self.dl.Pagebin(url)
    elif 'media.tumblr.com' in domain:
      self.dl.Raw(url)
    elif 'reddit.com' in domain:
      print 'Skipping self/reddit post: "%s"' %(item2['title'])
    elif (domain == 'quickmeme.com') or (domain == 'qkme.me'):
      self.dl.qkme(url)
    elif domain == 'bo.lt':
      self.dl.bolt(url)
    else: #Download all the images on the page
      self.dl.All(url)
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
    force = False
    top = False
    pg = 1
    for arg in sys.argv:
      if arg == '--force':
        force = True
      if arg == '--top':
        top = True
      if arg.startswith('--pages:'):
        pg = arg.split(':')[-1]
    
        
    for subreddit in subreddits.split(','):
      app = Client(subreddit,pg, force, top)
      app.run()
  except IndexError: #no arguments provided
    logger.error(helptext)
    #gui.main()
  finally:
    cleanup()
    




if __name__ == "__main__":
  try:
    main()
  finally:
    logger.save()
