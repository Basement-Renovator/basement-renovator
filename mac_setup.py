from distutils.core import setup
import py2app, sys, os, shutil

sys.argv.append('py2app')

if os.path.exists('dist'):
	shutil.rmtree('dist')

setup(
	name="Basement Renovator",
	version="0.1",
	author="Tempus",
	author_email="Tempus@chronometry.ca",
	app=["BasementRenovator.py"],
	options={"py2app": {"argv_emulation": True, "includes": ["sip", "PyQt5._qt"]}},
	setup_requires=["py2app"]) 
)

os.mkdir('dist/platforms')
shutil.copytree('resources', 'dist/resources')


# UNTESTED!