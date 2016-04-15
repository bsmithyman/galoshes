'''Galoshes
'''

from distutils.core import setup
import numpy as np
from setuptools import find_packages

CLASSIFIERS = [
'Development Status :: 3 - Alpha',
'Intended Audience :: Developers',
'Intended Audience :: Science/Research',
'License :: OSI Approved :: MIT License',
'Programming Language :: Python',
'Topic :: Scientific/Engineering',
'Topic :: Scientific/Engineering :: Mathematics',
'Topic :: Scientific/Engineering :: Physics',
'Operating System :: Microsoft :: Windows',
'Operating System :: POSIX',
'Operating System :: Unix',
'Operating System :: MacOS',
'Natural Language :: English',
]

with open('README.md') as fp:
    LONG_DESCRIPTION = ''.join(fp.readlines())

setup(
    name = 'galoshes',
    version = '0.1.4',
    packages = find_packages(),
    install_requires = ['numpy>=1.7',
                       ],
    author = 'Brendan Smithyman',
    author_email = 'brendan@bitsmithy.net',
    description = 'galoshes',
    long_description = LONG_DESCRIPTION,
    license = 'MIT',
    keywords = 'dictionary class attribute',
    url = 'https://github.com/bsmithyman/galoshes',
    download_url = 'https://github.com/bsmithyman/galoshes',
    classifiers = CLASSIFIERS,
    platforms = ['Windows', 'Linux', 'Solaris', 'Mac OS-X', 'Unix'],
    use_2to3 = False,
    include_dirs=[np.get_include()],
)
