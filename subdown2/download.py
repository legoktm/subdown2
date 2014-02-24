#!/usr/bin/env python

import memegrab
import re
import requests
import md5
import os
import twitter
import datetime
import threading
import Queue
import log

IMAGE_Q = Queue.Queue()


def initialize_imgur_checking():
    if not os.path.isfile('.bad_imgur.jpg'):
        obj = requests.get('http://i.imgur.com/sdlfkjdkfh.jpg', stream=True)
        with open('.bad_imgur.jpg', 'wb') as f:
            for chunk in obj.iter_content(1024):
                f.write(chunk)

    f = open('.bad_imgur.jpg', 'r')
    text = f.read()
    f.close()
    digest = md5.new(text).digest()
    return digest


class Download_Thread(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.bad_imgur = initialize_imgur_checking()
    
    def output(self, text,error=False):
        log.log(text, thread_name=self.getName(), error=error)
    def process_link(self, link, filename, time):
        headers = {'User-agent': 'subdown2 (https://github.com/legoktm/subdown2)'}
        req = requests.get(link, headers=headers)
        if not req.ok:
            return
        text = req.text
        if md5.new(text).digest() == self.bad_imgur:
            self.output('%s has been removed from imgur.com' %link, error=True)
            return
        f = open(filename, 'w')
        f.write(text)
        f.close()
        os.utime(filename, (time, time))
        self.output('Setting time to %s' %(time))
    
    
    def run(self):
        while True:
            link, filename, time = self.queue.get()
            self.process_link(link, filename, time)
            self.queue.task_done()
    



#spawn threads
for i in range(10):
    t = Download_Thread(IMAGE_Q)
    t.setDaemon(True)
    t.start()



class Downloader:
    """
    Custom downloaders for different websites.
    All traffic is directed through "Raw" which simply downloads the raw image file.
    """
    
    def __init__(self, reddit, force):
        self.help = "Sorry, %s doesn't work yet :("
        self.reddit = reddit
        self.bad_imgur = initialize_imgur_checking()
        self.force = force
        self.retry = False
        self.time = False
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
            self.output('Skipping %s since it already exists' %(link))
            return
        #download the image, so add it to the queue
        self.output('Adding %s to queue.' % link)
        IMAGE_Q.put((link, path, self.time))

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
            api = self.page_grab(api_link, json=True)
            for image in api['album']['images']:
                self.Raw(image['links']['original'])
            self.output('Finished Imgur album: %s' %(link))
        else:
            #it's a raw image
            id = link.split('/')[-1]
            api = self.page_grab('http://api.imgur.com/2/image/%s.json' %id, json=True)
            self.Raw(api['image']['links']['original'])
        
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
        ret = self.page_grab('http://expandurl.appspot.com/expand', data={'url':parsed},json=True)
        if ret['status'].lower() == 'ok':
            final_url = ret['end_url']
        else:
            raise
        #if 'yfrog.com' in final_url:
        #    self.yfrog(final_url)
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
            header = header.lower()
            if header.startswith('content-type'):
                #right header
                is_image = 'image' in header
                break
        if is_image: #means it is most likely an image
            self.Raw(link)
            return
        self.output('Skipping %s since it is not an image.' %(link))
        return
    def setTime(self, time):
        self.time = time
    def setTitle(self, title):
        self.title = title.replace(' ', '_').replace('/', '_')
    def setThreadInfo(self, name):
        self.thread_name = name
    def output(self, text, error = False):
        log.log(text, thread_name = self.thread_name, error=error)
    

    def page_grab(self, link, want_headers=False, data=None,json=False):
        headers = {'User-agent': 'subdown2 (https://github.com/legoktm/subdown2)'}
        r = requests.get(link,headers=headers,params=data)
        if want_headers:
            return r.headers
        else:
            if json:
                return r.json()
            return r.text

