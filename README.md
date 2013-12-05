birdback — simple fast Ubuntu backups
=====================================

birdback is a simple, fast and open-source backup tool for Ubuntu Linux users:
 - an icon is shown in the global menu bar of Ubuntu for controlling the application
 - USBs/HDDs are detected and mounted automatically for backup
 - backups are made of the user's home folder **ONLY** (for now)
 - backups are simply files being copied over in an efficient manner (see section below for more info)
 - when it comes time for the backup to be restored, the user can choose how and what files they copy back to the main HDD
 
What birdback does not do:
 - cross-platform backups (Ubuntu Linux only)
 - versioned backups
 - encryption

Licensed under GPLv3 to Liam Edwards-Playne and contributors.

## Why is birdback fast?
Even though birdback is written in higher-level langauge such as Python, it is still pretty fast. This is because of the very simple two-pass backup process.

When birdback is instructed to backup the home folder, it walks the directory tree and constructs a list of files to backup based on whether they are already on the backup destination and are the newest version of the file. This is inherently fast because it is just read operations. It is made even faster by using scandir, a quicker alternative to the standard lib's `os.walk`. 
The second stage is copying these files to the backup destination, which is just writing data.

## Install
I'm going to make this more automated later, perhaps in a Debian package.

 1. Clone git repo.
 2. `sudo apt-get install python3 python3-dev python3-setuptools python3-gobject`
 3. `sudo python setup.py build`
 4. `sudo python setup.py install`
