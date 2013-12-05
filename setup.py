#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(name = "birdback",
	version = "1.0.0",
	description = "birdback — simple fast Ubuntu backups",
	long_description = open('README.md').read(),
	author = "Liam Edwards-Playne",
	author_email = "liam@liamz.co",
	url = "http://github.com/liamzebedee/birdback",
	license = "GPLv3",
	
	package_dir = {'birdback' : 'src/birdback'},
	packages = ['birdback'],
	dependency_links = ['git+https://github.com/liamzebedee/scandir.git#egg=scandir-0.1'],
	install_requires = ['scandir', 'pyinotify'],
	
	data_files=[('/usr/local/share/icons/hicolor/scalable/apps', ['birdback.svg', 'birdback-active.svg'])],
)
