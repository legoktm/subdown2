#!/usr/bin/env python

import sys
import time
import gui
import os
import download
import datetime
import log
import threading
import Queue
import requests

helptext = """
(C) 2012, Kunal Mehta, under the MIT License

Syntax: subdown2 subreddit[,subreddit] pages [--force]

 - You can add as many subreddits as you wish, just split them with a comma (no spaces).
 - If an integer for pages is not set (or is not understood) it will be set to 1.
 - The force option will re-download all images and overwrite them. Default option is not to do so.
"""



queue = Queue.Queue()

#set some global configuration values
SFW_MODE = False
for arg in sys.argv:
    if arg == '--sfw':
        SFW_MODE = True

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
        log.log('Fetching %s' %(self.r))
        try:
            os.mkdir(self.name)
        except OSError:
            pass
        
    def parse(self, page):
        log.log('Queuing page %s of %s from %s' %(page, self.pages, self.r))
        params = {}
        if self.top:
            url = 'http://reddit.com/%s/top/.json' %(self.r)
            params['t'] = 'all'
        else:
            url = 'http://reddit.com/%s/.json' %(self.r)
        
        if page != 1:
            params['after'] = self.after
        r = requests.get(url, params=params, headers=self.headers)
        data = r.json()
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
    
    def output(self, text, error = False):
        newtext = '%s-%s: %s' % (datetime.datetime.now(), self.getName(), text)
        if error:
            logger.error(text)
        else:
            logger.debug(text)
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
        nsfw = False
        if SFW_MODE:
                if ('nsfw' in object['title'].lower()):
                        nsfw = True
                elif object['over_18']:
                        nsfw = True
        if nsfw:
                self.output('%s is NSFW, skipping.' % url, True)
                return

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
            self.output('Skipping self/reddit post: "%s"' %(item2['title']))
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


def main():
    for i in range(10):
        t = DownloadThread(queue)
        t.setDaemon(True)
        t.start()
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
        download.IMAGE_Q.join()
    except IndexError: #no arguments provided
        log.log(helptext,error=True)
        #gui.main()
    except KeyboardInterrupt:
        log.log('KeyboardInterrupt recieved.',error=True)
        sys.exit(1)
        




if __name__ == "__main__":
    main()
