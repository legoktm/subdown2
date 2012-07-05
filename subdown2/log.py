#!/usr/bin/env python

import os
import sys

# Creates error or debug logs based on input
# Has a few options:
# --debug will save a debug.log
# --quiet will prevent any debug's from being printed -- only errors
# --no-save will not save any logs

class Logger:
  
  def __init__(self):
    self.error_t = '-------------\n'
    self.debug_t = '-------------\n'
    self.e_path = 'errors.log'
    self.d_path = 'debug.log'
    #set default options
    self.save_debug_log = False
    self.quiet = False
    self.nosave = False
    #parse args to check user agreements
    for arg in sys.argv:
      if arg == '--debug':
        self.save_debug_log = True
      elif arg == '--quiet':
        self.quiet = True
      elif arg == '--no-logs':
        self.nosave = True
  
  def error(self, text):
    if type(text) == type(''):
      text = 'ERROR: ' + text
    print text
    self.error_t += text + '\n'
    self.debug_t += text + '\n'
  
  def debug(self, text):
    if not self.quiet:
      print text
    self.debug_t += text + '\n'
  
  def save(self):
    if self.nosave:
      return
    self.save_error()      
    if self.save_debug_log:
      self.save_debug()
  
  def save_error(self):
    if os.path.isfile(self.e_path):
      f = open(self.e_path, 'r')
      old = f.read()
      f.close()
      self.error_t = old + self.error_t
    f = open(self.e_path, 'w')
    f.write(self.error_t)
    f.close()
  
  def save_debug(self):
    if os.path.isfile(self.d_path):
      f = open(self.d_path, 'r')
      old = f.read()
      f.close()
      self.debug_t = old + self.debug_t
    f = open(self.d_path, 'w')
    f.write(self.debug_t)
    f.close()
  
