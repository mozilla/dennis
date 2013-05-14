#######################################################################
# This file is part of dennis.
#
# Copyright (C) 2013 Will Kahn-Greene
# Licensed under the Simplified BSD License. See LICENSE for full
# license.
#######################################################################

from setuptools import setup, find_packages
import re
import os


READMEFILE = 'README.rst'
VERSIONFILE = os.path.join('steve', '__init__.py')
VSRE = r"""^__version__ = ['"]([^'"]*)['"]"""


def get_version():
    version_file = open(VERSIONFILE, 'rt').read()
    return re.search(VSRE, version_file, re.M).group(1)


setup(
    name='dennis',
    version=get_version(),
    description='l10n and PO file helper tools',
    long_description=open(READMEFILE).read(),
    license='Simplified BSD License',
    author='Will Kahn-Greene',
    author_email='willg@bluesock.org',
    keywords='l10n localization po',
    url='http://github.com/willkg/dennis',
    zip_safe=True,
    packages=find_packages(),
    include_package_data=True,
    scripts=['scripts/dennis-cmd'],
    install_requires=[
        'polib',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
)
