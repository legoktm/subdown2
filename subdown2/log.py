#!/usr/bin/python

import os

class Logger:
  
  def __init__(self):
    self.error_t = '-------------\n'
    self.debug_t = '-------------\n'
    self.e_path = 'errors.log'
    self.d_path = 'debug.log'
  
  def error(self, text):
    if type(text) == type(''):
      text = 'ERROR: ' + text
    print text
    self.error_t += text + '\n'
    self.debug_t += text + '\n'
  
  def debug(self, text, p=True):
    if p:
      print text
    self.debug_t += text + '\n'
  
  def save(self, e=True, d=False):
    if e:
      self.save_error()
    if d:
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