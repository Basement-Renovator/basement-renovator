import struct, os
import xml.etree.ElementTree as ET


tree = ET.ElementTree(file='resources/Entities.xml')
entityXML = tree.getroot()

eList = entityXML.findall('entity')

for e in eList:

	e.set('Group', 'All')
	e.set('Kind', 'Misc')

	# Groups
	if e.get('ID') == "5":
		e.set('Kind', 'Pickups')

	if (int(e.get('ID')) > 9) and (int(e.get('ID')) < 1000):
		e.set('Kind', 'Enemies')

	if e.get('Boss') == "1":
		e.set('Kind', 'Bosses')

	if int(e.get('ID')) > 999:
		e.set('Kind', 'Grid')


tree.write('resources/Entities2.xml')
