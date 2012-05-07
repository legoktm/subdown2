#!/usr/bin/python
#Python2.7.2
#Josh Roppo
#joshroppo@gmail.com

import os, re, sys
import urllib, urllib2, urlparse

#Define home folder
home_folder = os.getenv('HOME') + "/"

def read_url(url):
  """
  Take in a url and return all the HTML of the page.
  """
  try:
    h = urllib2.urlopen(url)
    return h.read()
  except:
    print 'Url error:', URLError

def set_dir(todir):
  try:
    os.chdir(todir)
  except:
    print 'Error setting directory:', OSError

def get_image_qm(url, todir):
  #print url
  """ Given the URL and directory, download the image page's html for parsing.
  Parse the full html to find the important bit concerning the image's actual host location but looking in the 'leftside' content div wrapper.
  Extract the image name and description to be used as the image's name.
  Download the image and save to the given directory!
  """
  try:
    #DOTALL mode must be specified in order to pull html
    good_stuff = re.findall(r'<div id=\"leftside\">.*<div id=\"rightside\"', url, re.DOTALL)
    #print good_stuff 
  
    image = re.findall(r'src=\"(.*\.jpg)\"', good_stuff[0]).pop()
    print 'Grabbing image from:', image
  
    title = re.findall(r'alt="([\w|\-|\s{1|2}]+)', good_stuff[0]).pop()
  
    set_dir(todir)
    urllib.urlretrieve(image, title+'.jpg')
    print title+'.jpg', 'Saved to:',todir
  except:
    print 'Error occured finding image', OSError


def main():  
  args = sys.argv[1:]
  todir = '.'
  if len(args) == 1:
    #this functionality will be removed once more functionality is added.
    try:
      file_ = open(home_folder + '.config/memegrab', 'r')
      todir = file_.read()
      file_.close() 
    except:
      print 'Unable to read save directory, either not setup or missing: file will be saved to current directory.'
      print home_folder
    get_image_qm(read_url(args[0]), todir)
  elif len(args) == 2:
    if args[0] == '--todir':
      file_ = open(home_folder + '.config/memegrab', 'w')
      try:
        os.chdir(args[1])
        file_.write(args[1])
        file_.close()
      except:
        print 'Unable to set:', args[1], 'to be the directory', OSError
    elif args[0] == '--qm':
      #The standard call to download images from quickmeme
      try:
        file_ = open(home_folder + '.config/memegrab', 'r')
        todir = file_.read()
        file_.close() 
      except:
        print 'Unable to read save directory, either not setup or missing: file will be saved to current directory.'
      get_image_qm(read_url(args[1]), todir)
    else:
      print 'Usage: --todir <full path to save directory>'
      
  else:
    print 'Usage: http://qkme.me... OR --todir <full path to save directory> '
    sys.exit(-1)

if __name__ == '__main__':
  main()
  
