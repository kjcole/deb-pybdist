#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Output some standard documents.

Creates files based on your setup.py that requires a few variables set:
NAME ex. NAME = 'pybdist'
SETUP ex. SETUP = { 'name': 'pybdist, ... }

Optional:
LANGS ex. LANGS = ['pt_BR', 'fr']
DEPENDS ex. DEPENDS = ['python-twitter']
"""

__author__ = 'Scott Kirkwood (scott+pybdist@forusers.com)'

import apt
import gettext
import logging
import os
import re
import textwrap
import time
import urllib.request, urllib.error, urllib.parse
from . import util

gettext.install('pybdist')
logging.basicConfig()
LOG = logging.getLogger('pybdist')

LICENSES = {
  'Apache': (
     #'http://www.apache.org/licenses/LICENSE-2.0.txt',
     'apache.rot13',
     r'\[yyyy\]', r'\[name of copyright owner\]'),
  'Artistic': (
      'http://www.perlfoundation.org/attachment/legal/artistic-2_0.txt',
      '2000-2006', 'The Perl Foundation'),
  'GPL.*2': (
      'http://www.gnu.org/licenses/gpl-2.0.txt',
      'END OF TERMS.+', ''),
  'GPL.*3': (
      'http://www.gnu.org/licenses/gpl-3.0.txt',
      'END OF TERMS.+', ''),
  'LGPL': (
      'http://www.gnu.org/licenses/lgpl.txt',
      '', ''),
  'MIT': (
      'mit-license.rot13',
      '<year>', '<copyright holders>'),
  'Mozilla': (
      'http://www.mozilla.org/MPL/MPL-1.1.txt',
      '', ''),
  'BSD': (
      'new-bsd-license.rot13',
      '<YEAR>', '<OWNER>'),
}

class DocumentsException(Exception):
  pass


def _find_license():
  """Return the name of the license file or an empty string."""
  re_licensefilename = re.compile('license', re.IGNORECASE)
  for fname in os.listdir('.'):
    if re_licensefilename.search(fname):
      return os.path.abspath(os.path.join('.', fname))

  return ''

def _title(word, char='='):
  return [char * len(word), word, char * len(word)]

def _underline(word, char='-'):
  return [word, char * len(word)]

def _fill_depends(setup):
  lines = []
  apt_cache = apt.Cache()
  longest = 0
  for req in setup.DEPENDS:
    length = len(req)
    if length > longest:
      longest = length
  for req in setup.DEPENDS:
    if req in apt_cache:
      lines.append('* %-*s - %s' % (longest, req, apt_cache[req].summary))
      homepage = apt_cache[req].homepage
      if homepage:
        lines.append('  %-*s   (%s)' % (longest, ' ', homepage))
    else:
      lines.append(' * %s' % req)
  return lines

def _readme_lines(setup):
  lines = _title(setup.NAME.capitalize())
  lines.append('')
  lines += textwrap.wrap(setup.SETUP['description'], 80)
  lines.append('')
  lines += textwrap.wrap(setup.SETUP['long_description'], 80)
  lines.append('')
  lines += _underline(_('Home Page'))
  lines.append('')
  lines.append(_('You can find %s hosted at:') % setup.NAME)
  url = setup.SETUP['url']
  lines.append('  %s' % url)
  if 'code.google.com/' in url:
    LOG.info('Adding code.google.com links')
    lines.append('')
    lines.append(_('You can file bugs at:'))
    lines.append('  %s/issues/list' % url)
    lines.append('')
    lines.append(_('Latest downloads can be found at:'))
    lines.append('  %s/downloads/list' % url)

  if hasattr(setup, 'DEPENDS'):
    lines.append('')
    lines += _underline(_('Requirements'))
    lines.append('')
    lines.append(_('This program requires other libraries which you may or may not have installed.'))
    lines.append('')
    lines += _fill_depends(setup)

  lines.append('')
  lines += _underline(_('License'))
  lines.append('')
  lines.append(setup.SETUP['license'])
  license_file = _find_license()
  if not license_file:
    license_file = 'LICENSE-2.0.txt'
  lines.append(_('You can find it in the %s file.') % license_file)
  lines.append('')
  lines.append(_('-- file generated by %s.') % util.MAGIC_NAME)
  return lines

def _langs(setup):
  if hasattr(setup, 'LANGS'):
    LOG.info('Will output %d README language files.', len(setup.LANGS))
    return [''] + setup.LANGS
  else:
    return ['']

def _set_locale(setup, lang):
  """Set the locale.
  Args:
    setup: setup info
    lang: language to change to ex. 'en'
  Returns:
    dot_language if any
  """
  global _
  if lang:
    dot_lang = '.%s' % lang
    locale = lang
  else:
    dot_lang = ''
    locale = ''
  locale_dir = os.path.join(setup.DIR, 'locale')
  locale_dir = os.path.abspath(locale_dir)
  gtext = gettext.translation(setup.NAME, locale_dir, languages=[locale],
    fallback=True)
  gtext.install(str=True)
  _ = gtext.ugettext
  return dot_lang

def out_readme(setup):
  langs = _langs(setup)
  eng_desc = setup.SETUP['description']
  eng_long_desc = setup.SETUP['long_description']
  for lang in langs:
    dot_lang = _set_locale(setup, lang)
    fname = 'README%s.rst' % dot_lang
    func = _
    setup.SETUP['description'] = func(eng_desc)
    setup.SETUP['long_description'] = func(eng_long_desc)
    util._safe_overwrite(_readme_lines(setup), fname)
  _set_locale(setup, '')
  setup.SETUP['description'] = eng_desc
  setup.SETUP['long_description'] = eng_long_desc

def out_license(setup):
  lic_text = setup.SETUP['license']
  to_fetch = None
  for regex, info in list(LICENSES.items()):
    if re.search(regex, lic_text, re.IGNORECASE):
      to_fetch = info
      break
  if not to_fetch:
    raise DocumentsException('Unknown lic_text %r' % lic_text)

  license_fname = _find_license()
  if not license_fname:
    license_fname = 'LICENSE-2.0.txt'
    LOG.info('Creating license file %r' % license_fname)
  else:
    LOG.info('License file already exists as %r' % license_fname)
  url, y_regex, name_regex = to_fetch
  if url.startswith('http'):
    txt = urllib.request.urlopen(url).read()
  else:
    txt = open(os.path.join(os.path.dirname(__file__), url)).read()
    if url.endswith('rot13'):
      txt = txt.encode('rot13')

  year = time.strftime('%Y', time.localtime())
  re_yyyy = re.compile(y_regex, re.DOTALL)
  txt = re_yyyy.sub(year, txt)
  copyright_name = setup.SETUP['author']
  if hasattr(setup, 'COPYRIGHT_NAME'):
    copyright_name = setup.COPYRIGHT_NAME
  if name_regex:
    re_name = re.compile(name_regex, re.DOTALL)
    txt = re_name.sub(copyright_name, txt)
  else:
    txt += ' ' + copyright_name
  util._safe_overwrite(txt.split('\n'), license_fname)

def _install_lines(setup):
  lines = _title(_('Installing %s') % setup.NAME)
  lines.append('')
  lines += _underline('Downloading')
  lines.append('')
  vcs = None
  if hasattr(setup, 'VCS'):
    vcs = setup.VCS
  else:
    vcs = setup.SETUP['url']
  url = setup.SETUP['url']
  if 'code.google.com/' in vcs:
    LOG.info('Adding code.google.com links')
    lines.append(_('You will always find the latest version at:'))
    lines.append('')
    lines.append('  %s/downloads/list' % url)
    lines.append('')
    if vcs.endswith('/hg/') or vcs.endswith('/hg'):
      lines.append(_('If you prefer you can clone repository from::'))
      lines.append('')
      lines.append('  hg clone %s %s' % (vcs, setup.NAME))
      lines.append('')
    # TODO(scottkirkwood): add svn

  lines += _underline(_('Installation'))
  lines.append('')
  lines.append(_('To install using ``pip``,::'))
  lines.append('')
  lines.append('  $ pip install %s' % setup.NAME)
  lines.append('')
  lines.append(_('To install using ``easy_install``,::'))
  lines.append('')
  lines.append('  $ easy_install %s' % setup.NAME)
  lines.append('')
  lines.append(_('To install from .deb package::'))
  lines.append('')
  lines.append('  $ sudo dpkg -i %s*.deb' % setup.NAME)
  lines.append('')
  lines.append('If you get errors like Package %s depends on XXX;'
               ' however it is not installed.' % setup.NAME)
  lines.append('')
  lines.append('  $ sudo apt-get -f install')
  lines.append('Should install everything you need, then run:')
  lines.append('  $ sudo dpkg -i %s*.deb # again' % setup.NAME)

  if hasattr(setup, 'DEPENDS'):
    lines.append('')
    lines += _underline(_('Dependancies'))
    lines.append('')
    lines.append(_('This program requires::'))
    lines.append('')
    lines += _fill_depends(setup)

  lines.append('')
  lines.append(_('-- file generated by %s.') % util.MAGIC_NAME)
  return lines

def out_install(setup):
  langs = _langs(setup)
  for lang in langs:
    dot_lang = _set_locale(setup, lang)
    fname = 'INSTALL%s.rst' % dot_lang
    util._safe_overwrite(_install_lines(setup), fname)
  _set_locale(setup, '')

if __name__ == '__main__':
  import sys
  LOG.setLevel(logging.DEBUG)
  setup_dir = os.path.abspath(__file__ + '/../../..')
  print(setup_dir)
  sys.path.insert(0, setup_dir)
  import setup
  out_readme(setup)
  out_license(setup)
  out_install(setup)
