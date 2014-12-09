import struct, os
import xml.etree.ElementTree as ET

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

app = QApplication([])


itemXML = ET.ElementTree(file='/Users/Tempus/Dropbox/IsaacDev/Clean Rips/resources/items.xml')
iroot = itemXML.getroot()

ele = ET.Element('root')
tree = ET.ElementTree(ele)
entityXML = tree.getroot()


p = QPainter()

# Trinkets
# r = iroot.findall('trinket')
# for i in r:

# 	e = ET.SubElement(entityXML, 'entity')

# 	e.set('Name', i.get('name'))
# 	t = i.get('gfx')
# 	e.set('Image', 'resources/Entities/5.350.{0} - {1}.png'.format(i.get('id'), t[t.rfind('_'):].lower()))

# 	e.set('Group', 'Trinkets')
# 	e.set('Kind', 'Collect')

# 	e.set('ID', "5")
# 	e.set('Variant', '350')
# 	e.set('Subtype', i.get('id'))

# Passive Items
r = iroot.findall('passive')
for i in r:

	# Collectible
	# q = QImage()
	# q.load('resources/Entities/5.100.0 - Collectible.png')

	d = QImage()
	d.load('resources/Entities/collectibles/{0}'.format(i.get('gfx')))

	# p.begin(q)
	# p.drawImage(0,0,d)
	# p.end()

	e = ET.SubElement(entityXML, 'entity')

	e.set('Name', i.get('name'))
	e.set('Image', 'resources/Entities/Items/5.100.{0} - {1}.png'.format(i.get('id'), i.get('name')))
	d.save(e.get('Image'))

	e.set('Group', 'Passive Items')
	e.set('Kind', 'Collect')

	e.set('ID', "5")
	e.set('Variant', '100')
	e.set('Subtype', i.get('id'))

	v = os.path.exists(e.get('Image'))

	# Shop
	# q = QImage()
	# q.load('resources/Entities/collectibles/shop.png')

	# d = QImage()
	# d.load('resources/Entities/collectibles/{0}'.format(i.get('gfx')))

	# p.begin(d)
	# p.drawImage(0,0,q)
	# p.end()

	e = ET.SubElement(entityXML, 'entity')

	e.set('Name', i.get('name'))
	e.set('Image', 'resources/Entities/Items/5.100.{0} - {1}.png'.format(i.get('id'), i.get('name')))
	# d.save(e.get('Image'))

	e.set('Group', 'Passive Shop Items')
	e.set('Kind', 'Collect')

	e.set('ID', "5")
	e.set('Variant', '150')
	e.set('Subtype', i.get('id'))

	if not v or not os.path.exists(e.get('Image')):
		print(i.get('name'), v, os.path.exists(e.get('Image')))

# Active Items
r = iroot.findall('active')
for i in r:

	# Collectible
	# q = QImage()
	# q.load('resources/Entities/5.100.0 - Collectible.png')

	d = QImage()
	d.load('resources/Entities/collectibles/{0}'.format(i.get('gfx')))

	# p.begin(q)
	# p.drawImage(0,0,d)
	# p.end()

	e = ET.SubElement(entityXML, 'entity')

	e.set('Name', i.get('name'))
	e.set('Image', 'resources/Entities/Items/5.100.{0} - {1}.png'.format(i.get('id'), i.get('name')))
	d.save(e.get('Image'))

	e.set('Group', 'Active Items')
	e.set('Kind', 'Collect')

	e.set('ID', "5")
	e.set('Variant', '100')
	e.set('Subtype', i.get('id'))

	v = os.path.exists(e.get('Image'))

	# Shop
	# q = QImage()
	# q.load('resources/Entities/collectibles/shop.png')

	# d = QImage()
	# d.load('resources/Entities/collectibles/{0}'.format(i.get('gfx')))

	# p.begin(d)
	# p.drawImage(0,0,q)
	# p.end()

	e = ET.SubElement(entityXML, 'entity')

	e.set('Name', i.get('name'))
	e.set('Image', 'resources/Entities/Items/5.100.{0} - {1}.png'.format(i.get('id'), i.get('name')))
	# d.save(e.get('Image'))

	e.set('Group', 'Active Shop Items')
	e.set('Kind', 'Collect')

	e.set('ID', "5")
	e.set('Variant', '150')
	e.set('Subtype', i.get('id'))

	if not v or not os.path.exists(e.get('Image')):
		print(i.get('name'), v, os.path.exists(e.get('Image')))

# Familiars
r = iroot.findall('familiar')
for i in r:

	# Collectible
	# q = QImage()
	# q.load('resources/Entities/5.100.0 - Collectible.png')

	d = QImage()
	d.load('resources/Entities/collectibles/{0}'.format(i.get('gfx')))

	# p.begin(q)
	# p.drawImage(0,0,d)
	# p.end()

	e = ET.SubElement(entityXML, 'entity')

	e.set('Name', i.get('name'))
	e.set('Image', 'resources/Entities/Items/5.100.{0} - {1}.png'.format(i.get('id'), i.get('name')))
	d.save(e.get('Image'))

	e.set('Group', 'Familiars')
	e.set('Kind', 'Collect')

	e.set('ID', "5")
	e.set('Variant', '100')
	e.set('Subtype', i.get('id'))

	v = os.path.exists(e.get('Image'))

	# Shop
	# q = QImage()
	# q.load('resources/Entities/collectibles/shop.png')

	# d = QImage()
	# d.load('resources/Entities/collectibles/{0}'.format(i.get('gfx')))

	# p.begin(d)
	# p.drawImage(0,0,q)
	# p.end()

	e = ET.SubElement(entityXML, 'entity')

	e.set('Name', i.get('name'))
	e.set('Image', 'resources/Entities/Items/5.100.{0} - {1}.png'.format(i.get('id'), i.get('name')))
	# d.save(e.get('Image'))

	e.set('Group', 'Shop Familiars')
	e.set('Kind', 'Collect')

	e.set('ID', "5")
	e.set('Variant', '150')
	e.set('Subtype', i.get('id'))

	if not v or not os.path.exists(e.get('Image')):
		print(i.get('name'), v, os.path.exists(e.get('Image')))

tree.write('resources/Entities2.xml')
