#######################################################################
# This file is part of dennis.
#
# Copyright (C) 2013-2022 Will Kahn-Greene
# Licensed under the Simplified BSD License. See LICENSE for full
# license.
#######################################################################

from setuptools import setup, find_packages
import re
import os


READMEFILE = "README.rst"
VERSIONFILE = os.path.join("dennis", "__init__.py")
VSRE = r"""^__version__ = ['"]([^'"]*)['"]"""


def get_version():
    version_file = open(VERSIONFILE, "rt").read()
    return re.search(VSRE, version_file, re.M).group(1)


setup(
    name="dennis",
    version=get_version(),
    description=(
        "Utilities for working with PO and POT files to ease development "
        "and improve localization quality"
    ),
    long_description=open(READMEFILE).read(),
    license="Simplified BSD License",
    author="Will Kahn-Greene",
    author_email="willkg@bluesock.org",
    keywords="l10n localization PO POT lint translate development",
    url="https://github.com/willkg/dennis",
    zip_safe=True,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "polib>=1.0.8",
        "click>=6",
    ],
    entry_points="""
        [console_scripts]
        dennis-cmd=dennis.cmdline:click_run
    """,
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "License :: OSI Approved :: BSD License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Unix",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
    ],
)
