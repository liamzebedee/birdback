#!/usr/bin/env python
from setuptools import setup, find_packages

setup(name = "birdback",
	version = "0.0.1",
	description = "birdback - simple Ubuntu backup solution",
	author = "Liam Edwards-Playne",
	author_email = "liamzebedee@yahoo.com.au",
	url = "http://github.com/liamzebedee/birdback",
	license = "GPLv3",
	
	package_dir = {'birdback' : 'src/birdback'},
	packages = ['birdback'],
	dependency_links = ['https://github.com/liamzebedee/scandir/tarball/master#egg=scandir-0.1'],
	install_requires = [],
	
	data_files=[('share/icons/hicolor/scalable/apps', ['birdback.svg'])],
	scripts = [],
)
