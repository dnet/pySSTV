# -*- encoding: utf-8 -*-

from __future__ import unicode_literals
from distutils.core import setup

setup(
    name='PySSTV',
    version='0.1',
    description='Python classes for generating Slow-scan Television transmissions',
    author='András Veres-Szentkirályi',
    author_email='vsza@vsza.hu',
    url='https://github.com/dnet/pySSTV',
    packages=['pysstv', 'pysstv.tests', 'pysstv.examples'],
    keywords='HAM SSTV slow-scan television Scottie Martin Robot',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Topic :: Communications :: Ham Radio',
        'Topic :: Multimedia :: Video :: Conversion',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        ],
    long_description=open('README.md').read(),
)
