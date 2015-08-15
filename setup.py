#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
import os
import re
import sys
import socket

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('LICENSE') as f:
    license = f.read()
with open('README.rst') as f:
    description = f.read()

def include_data_files(directories):
    for d in directories:
        dest, source = d
        datadir = os.path.abspath(os.path.dirname(__file__)) + source
        data_file= [(dest, [
           os.path.join(d, f) for f in files]) for d,folders,files in os.walk(datadir)]
        yield data_file[0]

files = []
# files to be placed in different directories
directories = [('/usr/local/lib/','/nfce/darumaframework'),
               ('/u1/caixa/','/nfce/cmds'),
               ('/etc/rc.d/','/nfce/scripts'),
               ('/u1/tools','/tools')]
for df in  include_data_files(directories):
    files.append(df)

setup(
    name='nfce',
    version='0.0.1',
    author='Edytarcio Pereira',
    author_email='edytarcio.silva@armazemparaiba.com.br',
    packages=['nfce'],
    package_dir={'nfce': 'nfce'},
    # date to be included in the instalation directory
    package_data={'nfce': ['darumaframework/*','cmds/*','scripts/*']},
    data_files = files,
    url='http://www.armazemparaiba.com.br',
    license=license,
    description='Wrapper for DarumaFramework',
    long_description=description,
    keywords='python, daruma, nfce',
    platforms='',
    install_requires = [],
    entry_points = {'console_scripts': ['nfce = nfce.commands:nfce']},
    classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Programming Language :: Python',
          'License :: Other/Proprietary License',
          'Operating System :: POSIX',
          'Operating System :: Unix',
          'Topic :: Communications',
          'Topic :: Utilities',
          ],
)

