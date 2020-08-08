#!/usr/bin/env python3

from distutils.core import setup
import re
import gettext

NAME = 'pybdist'
DIR = 'src/pybdist'
gettext.install(NAME, DIR + 'locale')

VER = '0.3.1'
PY_NAME = 'pybdist'
DEB_NAME = 'python-bdist'
RELEASE_FILE = 'RELEASE.rst'
LANGS = ['pt_BR']

PY_SRC = f'{PY_NAME}.py'
DEPENDS = ['fakeroot', 'lintian', 'help2man', 'build-essential',
    'python-twitter', 'python-simplejson', 'pychecker',
    'python-docutils', 'python-nose', 'aspell', 'aspell-en', 'python-polib',
    'python-apt'
    ]
MENU_SUBSECTION = ''
DEPENDS_STR = ' '.join(DEPENDS)
AUTHOR_NAME = 'Scott Kirkwood'
COPYRIGHT_NAME = 'Google Inc.'
GOOGLE_CODE_EMAIL = 'scott@forusers.com'
MAILING_LIST = 'pybdist-discuss@googlegroups.com'
VCS = f'http://{NAME}.code.google.com/hg'

SETUP = dict(
  name=NAME,
  version=VER,
  packages=['pybdist'],
  package_dir={
      'pybdist': 'src/pybdist'},
  package_data = {
      'pybdist': [
          '*.txt', '*.rot13', 'locale/**/*/*.mo'],
  },
  author=AUTHOR_NAME,
  author_email='scott@forusers.com',
  platforms=['POSIX'],
  license='Apache 2.0',
  keywords=['python', 'utility', 'library'],
  url=f'http://code.google.com/p/{NAME}',
  download_url=f'http://{NAME}.googlecode.com/files/{NAME}-{VER}.zip',
  description=_('Python Build Distribution Library (pybdist)'),
  long_description=_("""A library used for personal projects to create a zip, tar and Debian
distributions.  Assumes folders are in a certain location so might not be
suitable for other projects. Also supports uploading to code.google.com, pypi,
mercurial, announcing on twitter and mailing lists."""),
  classifiers=[ # see http://pypi.python.org/pypi?:action=list_classifiers
      'Development Status :: 3 - Alpha',
      'Intended Audience :: Developers',
      'License :: OSI Approved :: Apache Software License',
      'Operating System :: POSIX :: Linux',
      'Topic :: Software Development :: Libraries',
  ],
)

if __name__ == '__main__':
  setup(**SETUP)
