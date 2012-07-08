#!/usr/bin/env python

import logging

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)


def log(text, thread_name=False, error=False):
  if not thread_name:
    thread_name = 'Main Thread'
  msg = '%s: %s' % (thread_name, text)
  if not error:
    logging.info(msg)
  else:
    logging.error(msg)
