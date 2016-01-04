import struct, os, shutil
import xml.etree.ElementTree as ET

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

app = QApplication([])


isaacResourceFolder = '/Users/Chronometrics/Dropbox/Basement Renovator/Afterbirth Rooms/resources/'



itemXML = ET.ElementTree(file=isaacResourceFolder + 'items.xml')
iroot = itemXML.getroot()

ele = ET.Element('root')
tree = ET.ElementTree(ele)
entityXML = tree.getroot()



categories = [('passive', 'Passive Items'), ('active', 'Active Items'), ('familiar', 'Familiars')]
for cat in categories:

	r = iroot.findall(cat[0])
	for i in r:

		e = ET.SubElement(entityXML, 'entity')

		e.set('Name', i.get('name'))
		e.set('Image', 'resources/Entities/Items/5.100.{0} - {1}.png'.format(i.get('id'), i.get('name')))

		e.set('Group', cat[1])
		e.set('Kind', 'Collect')

		e.set('ID', "5")
		e.set('Variant', '100')
		e.set('Subtype', i.get('id'))

		v = os.path.exists('resources/NewEntities/Items/' + i.get('gfx'))
		print (v, 'resources/NewEntities/Items/' + i.get('gfx'))
		if v:
			shutil.move('resources/NewEntities/Items/' + i.get('gfx'), e.get('Image'))

		# v = os.path.exists(isaacResourceFolder + 'items/collectibles/' + i.get('gfx'))
		# if v:
		# 	shutil.move(isaacResourceFolder + 'items/collectibles/' + i.get('gfx'), e.get('Image'))
quit()

# Trinkets
r = iroot.findall('trinket')
for i in r:

	e = ET.SubElement(entityXML, 'entity')

	e.set('Name', i.get('name'))
	e.set('Image', 'resources/Entities/5.350.{0} - {1}.png'.format(i.get('id'), i.get('name')))

	e.set('Group', 'Trinkets')
	e.set('Kind', 'Collect')

	e.set('ID', "5")
	e.set('Variant', '350')
	e.set('Subtype', i.get('id'))

	v = os.path.exists(isaacResourceFolder + 'items/trinkets/' + i.get('gfx'))
	if v:
		shutil.move(isaacResourceFolder + 'items/trinkets/' + i.get('gfx'), e.get('Image'))
