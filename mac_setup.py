from distutils.core import setup
import py2app, sys, os, shutil
import subprocess

sys.argv.append('py2app')

if os.path.exists('build'):
	shutil.rmtree('build')

if os.path.exists('dist'):
	shutil.rmtree('dist')


# IMPORTANT - Read this
print ("Run with 'python3.5 mac_setup.py py2app -A --packages=PyQt5' if you're having troubles.")


setup(
	name="Basement Renovator",
	version="0.1",
	author="Tempus",
	author_email="Tempus@chronometry.ca",
	app=["BasementRenovatorAfterbirth.py"],
	options={"py2app": {
		"argv_emulation": True, 
		"includes": ["sip"],
		"packages": "PyQt5",
		"iconfile": "resources/UI/BasementRenovator.icns",
		"resources": "resources"
		}},
	setup_requires=["py2app"] 
)
