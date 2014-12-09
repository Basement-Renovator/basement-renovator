from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import struct, os
import xml.etree.ElementTree as ET


def getEntity(id, subtype, variant):
	global entityXML
	ret = {}

	try:
		if subtype == 0 and variant == 0:
			en = entityXML.find("entity[@id='{0}']".format(id))
		elif subtype == 0:
			en = entityXML.find("entity[@id='{0}'][@variant='{1}']".format(id, variant))
		elif variant == 0:
			en = entityXML.find("entity[@id='{0}'][@subtype='{1}']".format(id, subtype))
		else:
			en = entityXML.find("entity[@id='{0}'][@subtype='{1}'][@variant='{2}']".format(id, subtype, variant))

		ret['Name'] = en.get('name')
		ret['BaseHP'] = en.get('baseHP')
		ret['Boss'] = en.get('boss')
		ret['Champion'] = en.get('champion')

		# atree = ET.parse('animations_converted/' + en.get('anm2path'))
		# aroot = atree.getroot()

		# image = aroot.find(".Content/Spritesheets/Spritesheet[@Id='0']")
		# frame = aroot.find("./Animations[@DefaultAnimation]/Animation/LayerAnimations/LayerAnimation/Frame")

		# sourceImage = QImage()
		# sourceImage.load('gfx/' + image.get('Path'), 'Format_ARGB32')

		# cropRect = QRect(int(frame.get('XCrop')), int(frame.get('YCrop')), int(frame.get('Width')), int(frame.get('Height')))

		# pixmapImg = QImage(int(frame[0].get('Width')), int(frame[0].get('Height')), QImage.Format_ARGB32)
		# RenderPainter = QPainter(pixmapImg)

		# for layer in frame:
		# 	cropRect = QRect(int(layer.get('XCrop')), int(layer.get('YCrop')), int(layer.get('Width')), int(layer.get('Height')))
		# 	RenderPainter.drawImage(0,0,sourceImage.copy(cropRect))

		# RenderPainter.end()
		ret['pixmap'] = QPixmap()
		# ret['pixmap'].convertFromImage(sourceImage.copy(cropRect))

	except:
		# print ('Entity {0}:{1}:{2} not found.'.format(id, subtype, variant))
		ret['Name'] = 'Unknown'
		pass

	return ret


def openMap():
	global EntityOutput

	maps = ['00.special rooms.stb', '01.basement.stb', '02.cellar.stb', '03.caves.stb', 
			'04.catacombs.stb', '05.depths.stb', '06.necropolis.stb', '07.womb.stb', 
			'08.utero.stb', '09.sheol.stb', '10.cathedral.stb', 
			'11.dark room.stb', '12.chest.stb']

	for path in maps:
		# Let's read the file and parse it into our list items
		print (path)
		stb = open(path, 'rb').read()

		rooms = struct.unpack_from('<I', stb, 0)[0]
		off = 4

		print('Room Count: '+str(rooms))
		for room in range(rooms):

			roomData = struct.unpack_from('<IIBH', stb, off)
			off += 11

			roomName = struct.unpack_from('<{0}s'.format(roomData[3]), stb, off)[0].decode()
			off += roomData[3]

			entityTable = struct.unpack_from('<fBBBH', stb, off)
			off += 9

			doors = []
			for door in range(entityTable[3]):
				doors.append(struct.unpack_from('<hh?', stb, off))
				off += 5

			entities = []
			for entity in range(entityTable[4]):
				spawnLoc = struct.unpack_from('<hhB', stb, off)
				off += 5

				for spawn in range(spawnLoc[2]):
					t = struct.unpack_from('<HHHf', stb, off)
					entities.append([spawnLoc[0], spawnLoc[1], t[0], t[1], t[2], t[3]])
					off += 10

			for entity in entities:
				# x, y, mytype, variant, subtype, weight
				e = {}
				e['ID'] = entity[2]
				e['Variant'] = entity[3]
				e['Subtype'] = entity[4]
				e['Weight'] = entity[5]

				di = getEntity(e['ID'], e['Subtype'], e['Variant'])

				e.update(di)

				if 'pixmap' in di:
					# e['pixmap'].save('resources/Entities/{ID}.{Variant}.{Subtype} - {Name}.png'.format(**e))
					e['pixmap'] = 'resources/Entities/{ID}.{Variant}.{Subtype} - {Name}.png'.format(**e)
					EntityOutput.add((e['ID'], e['Name'], e['Subtype'], e['Variant'], e['pixmap'], e['Boss'], e['Champion'], e['BaseHP']))
				else:
					EntityOutput.add((e['ID'], e['Name'], e['Subtype'], e['Variant'], ''))

				
######

app = QApplication([])

EntityOutput = set()

tree = ET.parse('entities2.xml')
entityXML = tree.getroot()
root = ET.Element('data')
ETout = ET.ElementTree(root)

openMap()

from operator import *
for e in sorted(EntityOutput, key=itemgetter(0,3,2)):
	new = ET.SubElement(root, 'entity')
	new.set('ID', str(e[0]))
	new.set('Name', str(e[1]))
	new.set('Subtype', str(e[2]))
	new.set('Variant', str(e[3]))
	new.set('Image', e[4])

	if len(e) > 5:
		new.set('Boss', e[5])
		new.set('Champion', e[6])
		new.set('BaseHP', e[7])


ETout.write('resources/Entities.xml')
