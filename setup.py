#!/usr/bin/env python
from setuptools import setup, find_packages

from spambayes_lite import __version__


setup(
    name='spambayes_lite',
    version = __version__,
    description = "Bare-bones spam classification system based on a modified version of SpamBayes.",
    author = "the spambayes project, Daniel Brandt",
    author_email = "spambayes@python.org, me@dbrandt.se",
    url = "http://spambayes.sourceforge.net",
    install_requires=["lockfile", "dnspython"],

    packages=find_packages(),
    # classifiers = [
    #     'Development Status :: 5 - Production/Stable',
    #     'Environment :: Console',
    #     'Environment :: Plugins',
    #     'Environment :: Win32 (MS Windows)',
    #     'License :: OSI Approved :: Python Software Foundation License',
    #     'Operating System :: POSIX',
    #     'Operating System :: MacOS :: MacOS X',
    #     'Operating System :: Microsoft :: Windows :: Windows 95/98/2000',
    #     'Operating System :: Microsoft :: Windows :: Windows NT/2000',
    #     'Natural Language :: English',
    #     'Programming Language :: Python',
    #     'Programming Language :: C',
    #     'Intended Audience :: End Users/Desktop',
    #     'Topic :: Communications :: Email :: Filters',
    #     'Topic :: Communications :: Email :: Post-Office :: POP3',
    #     'Topic :: Communications :: Email :: Post-Office :: IMAP',
    #     ],
    )
