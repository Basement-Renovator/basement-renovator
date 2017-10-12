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

# print("copy plugins")
# subprocess.call(["cp", "-r", "PlugIns", "dist/Basement Renovator.app/Contents/PlugIns"])
# subprocess.call(["cp", "qt.conf", "dist/Basement Renovator.app/Contents/Resources/qt.conf"])



# This shitty mac deploy simply won't work. here are some things:
#
#	- you'll need libqcocoa.dylib from your qt plugins/platforms directory, and you should put it into .app/Contents/PlugIns
#	- you should touch .app/Contents/Resources/qt.conf
#


# Some non-working snippets

# sys.argv.append('-platformpluginpath')
# sys.argv.append('/Users/Tempus/Desktop/Basement Renovator/Basement-Renovator/dist/Basement Renovator.app/Contents/Resources/PlugIns')

# QCoreApplication.addLibraryPath('/Users/Tempus/Desktop/Basement Renovator/Basement-Renovator/dist/Basement Renovator.app/Contents/')

# os.system('export QT_PLUGIN_PATH="{0}/PlugIns"'.format(os.getcwd()))

# from qtLibPathFacade.qtLibPathFacade import QtLibPathFacade
# main:
#	QtLibPathFacade.addBundledPluginsPath()
