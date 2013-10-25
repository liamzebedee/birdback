# While writing this I was listening to Flight of the Conchord's song 'Hiphopopotamus vs. Rhymenoceros'
# When naming, I thought I'd take a cue from the Rhymenocerous, of whose back the birds lie.
import scandir
import time

count = 0
mainBackupDir = '/home/liamzebedee'
ignoredDirs = ['.cache', '.ccache', 'Downloads', 'tmp']
start = time.time()
for root, dirs, files in scandir.walk(mainBackupDir):
	for ignoredDir in ignoredDirs:
		if ignoredDir in dirs: dirs.remove(ignoredDir)
		if root == (mainBackupDir + '/.local/share'):
			if 'Trash' in dirs: dirs.remove('Trash')
	for name in files:
		count += 1
	print(root)
end = time.time()
print(str(start))
print(str(end))
interval = end - start
print('Process took ', str(interval))
