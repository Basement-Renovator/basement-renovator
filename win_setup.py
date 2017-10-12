from distutils.core import setup
import py2exe, sys, os, shutil

sys.argv.append('py2exe')

if os.path.exists('dist'):
	shutil.rmtree('dist')

setup(
	name="Basement Renovator",
	version="0.1",
	author="Tempus",
	author_email="Tempus@chronometry.ca",
	windows = [{'script': "BasementRenovator.py"}],
	options = {'py2exe': {
		'bundle_files': 1, 
		'compressed': False, 
		"includes":["sip", "xml.etree"],
		'optimize': 2,
		'bundle_files': 3,
		"icon_resources": [(0, "resources/UI/BasementRenovator.ico")]
	}}
)


os.mkdir('dist/platforms')
shutil.copytree('resources', 'dist/resources')
shutil.copy('C:\\Python34/Lib/site-packages/PyQt5/plugins/platforms/qwindows.dll', 'dist/platforms')
shutil.copy('C:\\Python34/Lib/site-packages/PyQt5/libEGL.dll', 'dist')