#!/usr/bin/env python3
#
# Copyright 20l0 Google Inc. All Rights Reserved.
#

from . import googlecode_upload
import hashlib
import os
import sys
import re
import urllib.request, urllib.error, urllib.parse

def get_download_list(project_name):
  """Fetches the list of downloads from an atom feed.

  Args:
    project_name: exact title of the project.

  Returns:
    list of dictionary entries with 'update', 'summary', 'labels', and 'fname'
    set.
  """
  url = f'http://code.google.com/feeds/p/{project_name}/downloads/basic'
  try:
    fin = urllib.request.urlopen(url)
    text = fin.read()
    fin.close()
  except urllib.error.URLError:
    text = ''
  re_entry = re.compile(r'<entry>(.+?)</entry>', re.DOTALL)

  lst = []
  for match in re_entry.finditer(text):
    entry = match.group(1)
    updated = _safe_search(r'<updated>(.+?)</updated>', entry)
    summary = _safe_search(r'<title>\s*(.*)\s*</title>', entry)
    labels = _safe_search(r'Labels:(.+?)&lt;', entry, re.DOTALL)
    if labels:
      labels = labels.split()
    else:
      labels = []
    fname = _safe_search(r'downloads/detail\?name=(.+?)"', entry)
    lst.append(dict(project_name=project_name, updated=updated,
                     summary=summary, labels=labels, fname=fname))

  return lst


def _filter_featured_downloads(lst):
  """Filter out the list keeping only Featured files."""
  ret = []
  for item in lst:
    if 'Featured' in item['labels']:
      ret.append(item)
  return ret


def _safe_search(regex, haystack, options=0):
  """Searches for string, returns None if not found.

  Assumes that regex has on and only 1 group.
  Args:
    regex: regular expression to use with 1 group.
    haystack: the text to search (assumes multiline)
    options: regular expression options
  Returns:
    String or None
  """
  grps = re.search(regex, haystack, options)
  if not grps:
    return None
  return grps.group(1)


def get_file_details(project_name, fname):
  """Get detail information about the file.

  Note: Didn't fetch the labels.
  Args:
    project_name: name of the project in code.google.com
    fname: filename, must match.
  Returns:
    dictionary with various things set.
  """
  url = f'http://code.google.com/p/{project_name}/downloads/detail?name={fname}'
  print(f'Checking SHA1 at {url!r}')
  try:
    fin = urllib.request.urlopen(url, timeout=200)
    text = fin.read()
    fin.close()
  except urllib.error.HTTPError:
    text = ''
  sha1 = _safe_search(r'SHA1 Checksum: ([^<]+)', text, re.DOTALL)
  if sha1:
    sha1 = sha1.strip()

  date = _safe_search(r'<span class="date"[^>]+ title="([^"]+)"', text,
      re.DOTALL)

  download_count = _safe_search(r'>Downloads:&nbsp;</th><td>([^<]+)</td>', text,
      re.DOTALL)
  if download_count:
    download_count = int(download_count, 10)
  return dict(project_name=project_name, fname=fname, sha1=sha1, date=date)


def download_file(project_name, fname, dist_dir):
  """Downloads to file to distdir."""
  url = f'http://{project_name}.googlecode.com/files/{fname}'
  fin = urllib.request.urlopen(url, timeout=200)
  text = fin.read()
  fin.close()
  outfilename = os.path.join(dist_dir, fname)
  if not os.path.exists(dist_dir):
    os.makedirs(dist_dir)
  fout = file(outfilename, 'wb')
  fout.write(text)
  fout.close()


def maybe_download_file(project_name, fname, dist_dir):
  """Verify the checksums."""
  details = get_file_details(project_name, fname)
  if details['sha1']:
    sha1 = hashlib.sha1()
    dist_filename = os.path.join(dist_dir, fname)
    fin = open(dist_filename, 'rb')
    sha1.update(fin.read())
    fin.close()
    hex_digest = sha1.hexdigest()
  else:
    hex_digext = '-'
  if hex_digest == details['sha1']:
    print('SHA1 checksums don\'t match, dowloading.')
    download_file(project_name, fname, dist_dir)


def maybe_upload_file(project_name, dist_dir, fname,
    summary, labels, username, password):
  """Verify the checksums."""
  details = get_file_details(project_name, fname)
  dist_filename = os.path.join(dist_dir, fname)
  if details['sha1']:
    fin = open(dist_filename, 'rb')
    sha1 = hashlib.sha1()
    sha1.update(fin.read())
    fin.close()
    hex_digest = sha1.hexdigest()
  else:
    hex_digest = '-'
  if not details['sha1'] or hex_digest != details['sha1']:
    if details['sha1']:
      print(f'SHA1 checksums don\'t match, uploading {fname!r}.')
    else:
      print(f'File not there, uploading {fname!r}.')
    status, reason, url= googlecode_upload.upload(
      os.path.join(dist_dir, fname), project_name, username, password, summary, labels)
    if not url:
      print(f'{status!r}, {reason!r}')
      print(f'{os.path.join(dist_dir, fname)!r}, {project_name!r}, {summary!r}, {labels!r}')
      #print(f'{username!r}, {password!r}')
      sys.exit(-1)
  else:
    print(f'Checksums match, not uploading {fname!r}.')


def update_file(info, dist_dir, username, password):
  """Updates the file by re-uploading it.

  Only way I could figure to remove the 'Featured' label, ugh.
  Unfortunately, it also updates the upload date, oh well.

  Args:
    info: dictionary filled with project_name, fname, summary, and labels
    dist_dir: the destination filename that must exist.
    username: username to use
  """
  print(f'Updating {info["fname"]}')
  googlecode_upload.upload(
      f'{dist_dir}/{info["fname"]}',
      info['project_name'], username, password, info['summary'], info['labels'])


def remove_featured_labels(project_name, user_name, password, except_list=None):
  """Removes the 'Featured' label for all downloads.

  This is expectation to upload some new featured files.
  Requires that you have access to the account.
  Args:
    project_name: name of the project.
    user_name: user name to login with
    password: password to use
    except_list: list of files to not update (or none)
  """
  dist_dir = 'dist'
  lst = _filter_featured_downloads(get_download_list(project_name))
  for item in lst:
    if except_list and item['fname'] in except_list:
      continue
    fname = os.path.join('dist', item['fname'])
    if not os.path.exists(fname):
      print(f'Dowloading {fname!r}')
      download_file(project_name, item['fname'], dist_dir)
    else:
      print(f'Checking if I need to dowload {fname!r}')
      maybe_download_file(project_name, item['fname'], dist_dir)

  for item in lst:
    if except_list and item['fname'] in except_list:
      continue
    item['labels'].remove('Featured')
    print(f'Removing "Featured" from {item["fname"]!r}')
    update_file(item, dist_dir, user_name, password)

if __name__ == '__main__':
  import getpass
  USERNAME = 'scott@forusers.com'
  print(f'Enter your googlecode password for {USERNAME!r}')
  PASSWORD = getpass.getpass()
  remove_featured_labels('pybdist', USERNAME, PASSWORD)
