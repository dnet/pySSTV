# -*- encoding: utf-8 -*-

from setuptools import setup

setup(
    name='PySSTV',
    version='0.5.4',
    description='Python classes for generating Slow-scan Television transmissions',
    author=u'András Veres-Szentkirályi',
    author_email='vsza@vsza.hu',
    url='https://github.com/dnet/pySSTV',
    packages=['pysstv', 'pysstv.tests', 'pysstv.examples'],
    entry_points={
        'console_scripts': [
            'pysstv = pysstv.__main__:main',
        ],
    },
    keywords='HAM SSTV slow-scan television Scottie Martin Robot Pasokon',
    install_requires = ['Pillow'],
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Topic :: Communications :: Ham Radio',
        'Topic :: Multimedia :: Video :: Conversion',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        ],
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
)
