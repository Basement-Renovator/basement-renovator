###########################################
# 
#    Binding of Isaac: Rebirth Stage Editor
#
#
 #
  #
  #		UI Elements
  #			Main Scene: Click to select, right click to paint. Auto resizes to match window zoom. Renders background.
  #			Entity: A QGraphicsItem to be added to the scene for drawing.
  #			Room List: Shows a list of rooms with mini-renders as icons. Needs add and remove buttons. Should drag and drop re-sort.
  #			Entity Palette: A palette from which to choose entities to draw.
  #			Properties: Possibly a contextual menu thing?
  #
 #
#
#	Todo: 
#		Idiot proof the variant numbers further
#			Variant number hardcoding notes:
#				Horsemen, shops, devil/angel trapdoor rooms, Satan, Lamb
#


from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import struct, os
import xml.etree.ElementTree as ET


########################
#       XML Data       #
########################

def getEntityXML():
	tree = ET.parse('resources/Entities.xml')
	root = tree.getroot()

	return root

########################
#      Scene/View      #
########################

class RoomScene(QGraphicsScene):

	def __init__(self):
		QGraphicsScene.__init__(self, 0,0,0,0)
		self.newRoomSize(13, 7)

		self.BG = [	"01_basement.png", "02_cellar.png", "03_caves.png", "04_catacombs.png", 
					"05_depths.png", "06_necropolis.png", "07_the womb.png", "08_utero.png", 
					"09_sheol.png", "10_cathedral.png", "11_chest.png", "12_darkroom.png", 
					"0a_library.png", "0b_shop.png", "0c_isaacsroom.png", "0d_barrenroom.png", 
					"0e_arcade.png", "0e_diceroom.png", "0f_secretroom.png"
					]
		self.grid = True

		# Make the bitfont
		q = QImage()
		q.load('resources/UI/Bitfont.png')

		self.bitfont = [QPixmap.fromImage(q.copy(i*12,0,12,12)) for i in range(10)]
		self.bitText = True

	def newRoomSize(self, w, h):
		self.roomWidth = w
		self.roomHeight = h

		self.setSceneRect(-52, -52, self.roomWidth*26+52*2, self.roomHeight*26+52*2)

	def clearDoors(self):
		for item in self.items():
			if isinstance(item, Door):
				item.remove()

	def drawForeground(self, painter, rect):

		# Bitfont drawing: moved to the RoomEditorWidget.drawForeground for easier anti-aliasing

		# Grey out the screen to show it's inactive if there are no rooms selected
		if mainWindow.roomList.selectedRoom() is None:
			painter.setPen(QPen(Qt.white,1,Qt.SolidLine))
			painter.setBrush(QBrush(QColor(100,100,100,100)))

			b = QBrush(QColor(100,100,100,100))
			painter.fillRect(rect, b)
			return

		# Draw me a foreground grid
		if not self.grid: return
		
		painter.setRenderHint(QPainter.Antialiasing, True)
		painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

		rect = QRectF(0,0,self.roomWidth*26,self.roomHeight*26)
		ts = 26

		startx = rect.x()
		endx = startx + rect.width()
		
		starty = rect.y()
		endy = starty + rect.height()
		
		painter.setPen(QPen(QColor.fromRgb(255,255,255,100), 1, Qt.DashLine))
		
		x = startx
		y1 = rect.top()
		y2 = rect.bottom()
		while x <= endx:
			painter.drawLine(x, starty, x, endy)
			x += ts
		
		y = starty
		x1 = rect.left()
		x2 = rect.right()
		while y <= endy:
			painter.drawLine(startx, y, endx, y)
			y += ts

	def drawBackground(self, painter, rect):
		roomBG = 1

		if mainWindow.roomList.selectedRoom():
			roomBG = mainWindow.roomList.selectedRoom().roomBG

		tile = QImage()
		tile.load('resources/Backgrounds/{0}'.format(self.BG[roomBG-1]))

		corner = tile.copy(		QRect(0,	0,	26*7,	26*4)	)
		vert =   tile.copy(		QRect(26*7,	0,	26*2,	26*6)	)
		horiz =  tile.copy(		QRect(0, 26*4,	26*9,	26*2)	)

		t = -52
		xm = 26 * (self.roomWidth+2)  - 26*7
		ym = 26 * (self.roomHeight+2) - 26*4

		# Corner Painting
		painter.drawPixmap	(t,t, 	QPixmap().fromImage(corner.mirrored(False, False)))
		painter.drawPixmap	(xm,t, 	QPixmap().fromImage(corner.mirrored(True, False)))
		painter.drawPixmap	(t,ym,	QPixmap().fromImage(corner.mirrored(False, True)))
		painter.drawPixmap	(xm,ym,	QPixmap().fromImage(corner.mirrored(True, True)))

		# Mirrored Textures
		uRect = QImage(26*4, 26*6, QImage.Format_RGB32)
		lRect = QImage(26*9, 26*4, QImage.Format_RGB32)

		uRect.fill(1)
		lRect.fill(1)

		vp = QPainter()
		vp.begin(uRect)
		vp.drawPixmap(0, 0,QPixmap().fromImage(vert))
		vp.drawPixmap(52,0,QPixmap().fromImage(vert.mirrored(True, False)))
		vp.end()

		vh = QPainter()
		vh.begin(lRect)
		vh.drawPixmap(0, 0,QPixmap().fromImage(horiz))
		vh.drawPixmap(0,52,QPixmap().fromImage(horiz.mirrored(False, True)))
		vh.end()

		painter.drawTiledPixmap(26*7-52-13, -52, 26 * (self.roomWidth - 10)+26, 26*6, QPixmap().fromImage(uRect))
		painter.drawTiledPixmap(-52, 26*4-52-13, 26*9, 26 * (self.roomHeight - 4)+26, QPixmap().fromImage(lRect))
		painter.drawTiledPixmap(26*7-52-13, self.roomHeight*26-26*4, 26 * (self.roomWidth - 10)+26, 26*6, QPixmap().fromImage(uRect.mirrored(False, True)))
		painter.drawTiledPixmap(self.roomWidth*26-26*7, 26*4-52-13, 26*9, 26 * (self.roomHeight - 4)+26, QPixmap().fromImage(lRect.mirrored(True, False)))

		if self.roomHeight == 14 and self.roomWidth == 26:

			center = tile.copy(		QRect(26*3,	26*3, 26*6, 26*3)	)

			painter.drawPixmap	(26*7,  26*4, 	QPixmap().fromImage(center.mirrored(False, False)))
			painter.drawPixmap	(26*13, 26*4, 	QPixmap().fromImage(center.mirrored(True, False)))
			painter.drawPixmap	(26*7 , 26*7,	QPixmap().fromImage(center.mirrored(False, True)))
			painter.drawPixmap	(26*13, 26*7,	QPixmap().fromImage(center.mirrored(True, True)))

class RoomEditorWidget(QGraphicsView):

	def __init__(self, scene, parent=None):
		QGraphicsView.__init__(self, scene, parent)

		self.setViewportUpdateMode(self.FullViewportUpdate)
		self.setDragMode(self.RubberBandDrag)
		self.setTransformationAnchor(QGraphicsView.AnchorViewCenter)
		self.setAlignment(Qt.AlignTop|Qt.AlignLeft)
		self.newScale = 1.0
		
		self.assignNewScene(scene)

	def assignNewScene(self, scene):
		self.setScene(scene)
		self.centerOn(0,0)

		self.objectToPaint = None
		self.lastTile = None
		
	def tryToPaint(self, event):
		'''Called when a paint attempt is initiated'''

		paint = self.objectToPaint
		if paint is None: return

		clicked = self.mapToScene(event.x(), event.y())
		x, y = clicked.x(), clicked.y()
		if x > self.scene().roomWidth  * 26: return
		if y > self.scene().roomHeight * 26: return

		if x < 0: x = 0
		if y < 0: y = 0

		x = int(x / 26)
		y = int(y / 26)

		# Don't stack multiple grid entities
		for i in self.scene().items():
			if isinstance(i, Entity):
				if i.entity['X'] == x and i.entity['Y'] == y:
					if int(i.entity['Type']) > 999 and int(self.objectToPaint.ID) > 999:
						return

		# Make sure we're not spawning oodles
		if (x,y) in self.lastTile: return
		self.lastTile.add((x,y))

		en = Entity(x,y,int(paint.ID), int(paint.variant), int(paint.subtype), 0)

		self.scene().addItem(en)
		mainWindow.dirt()

	def mousePressEvent(self, event):
		if event.button() == Qt.RightButton:
			if mainWindow.roomList.selectedRoom() is not None:
				self.lastTile = set()
				self.tryToPaint(event)
				event.accept()
		else:
			self.lastTile = None
			QGraphicsView.mousePressEvent(self, event)

	def mouseMoveEvent(self, event):
		if self.lastTile:
			if mainWindow.roomList.selectedRoom() is not None:
				self.tryToPaint(event)
				event.accept()
		else:
			QGraphicsView.mouseMoveEvent(self, event)

	def mouseReleaseEvent(self, event):
		self.lastTile = None
		QGraphicsView.mouseReleaseEvent(self, event)

	def keyPressEvent(self, event):
		if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
			scene = self.scene()

			selection = scene.selectedItems()
			if len(selection) > 0:
				for obj in selection:
					obj.setSelected(False)
					obj.remove()
				scene.update()
				self.update()
				mainWindow.dirt()
				return
		else:
			QGraphicsView.keyPressEvent(self, event)

	def drawBackground(self, painter, rect):
		painter.fillRect(rect, QColor(0, 0, 0))

		QGraphicsView.drawBackground(self,painter,rect)

	def resizeEvent(self, event):
		QGraphicsView.resizeEvent(self, event)

		w = self.scene().roomWidth
		h = self.scene().roomHeight

		xScale = event.size().width()  / (w*26 + 52*2)
		yScale = event.size().height() / (h*26 + 52*2)
		newScale = min([xScale, yScale])

		tr = QTransform()
		tr.scale(newScale, newScale)
		self.newScale = newScale

		self.setTransform(tr)

		if newScale == yScale:
			self.setAlignment(Qt.AlignTop|Qt.AlignHCenter)
		else:
			self.setAlignment(Qt.AlignVCenter|Qt.AlignLeft)

	def drawForeground(self, painter, rect):

		QGraphicsView.drawForeground(self,painter,rect)

		painter.setRenderHint(QPainter.Antialiasing, True)
		painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

		# Display the number of entities on a given tile, in bitFont or regular font
		tiles = [[0 for y in range(26)] for x in range(14)]
		for e in self.scene().items():
			if isinstance(e,Entity):
				tiles[e.entity['Y']][e.entity['X']] += 1
	
		if not self.scene().bitText:
			painter.setPen(QPen(Qt.white,1,Qt.SolidLine))
			painter.font().setPixelSize(5)

		for y in enumerate(tiles):
			for x in enumerate(y[1]):

				if x[1] > 1:

					if self.scene().bitText:
						c = x[1]

						if x[1] >= 10:
							painter.drawPixmap( (x[0] + 1) * 26 - 24, (y[0] + 1) * 26 - 12, self.scene().bitfont[int(c/10)] )
							c = c % 10

						painter.drawPixmap( (x[0] + 1) * 26 - 12, (y[0] + 1) * 26 - 12, self.scene().bitfont[c] )

					else:
						painter.drawText( x[0] * 26, y[0] * 26, 26, 26, Qt.AlignBottom | Qt.AlignRight, str(x[1]) )

class Entity(QGraphicsItem):
	SNAP_TO = 26

	def __init__(self, x, y, mytype, variant, subtype, weight):
		QGraphicsItem.__init__(self)
		self.setFlags(
				self.ItemSendsGeometryChanges |
				self.ItemIsSelectable |
				self.ItemIsMovable
				)

		# Supplied entity info
		self.entity = {}
		self.entity['X'] = x
		self.entity['Y'] = y
		self.entity['Type'] = mytype
		self.entity['Variant'] = variant
		self.entity['Subtype'] = subtype
		self.entity['Weight'] = weight

		# Derived Entity Info
		self.entity['name'] = None
		self.entity['baseHP'] = None
		self.entity['boss'] = None
		self.entity['champion'] = None
		self.entity['pixmap'] = None

		self.getEntityInfo(mytype, subtype, variant)

		self.updatePosition()
		if self.entity['Type'] < 999:
			self.setZValue(1)
		else:
			self.setZValue(0)

		if not hasattr(Entity, 'SELECTION_PEN'):
			Entity.SELECTION_PEN = QPen(Qt.green, 1, Qt.DashLine)
	
	def getEntityInfo(self, t, subtype, variant):
		global entityXML
		en = entityXML.find("entity[@ID='{0}'][@Subtype='{1}'][@Variant='{2}']".format(t, subtype, variant))

		self.entity['name'] = en.get('Name')
		self.entity['baseHP'] = en.get('BaseHP')
		self.entity['boss'] = en.get('Boss')
		self.entity['champion'] = en.get('Champion')

		if self.entity['Type'] is 5 and self.entity['Variant'] is 100:
			i = QImage()
			i.load('resources/Entities/5.100.0 - Collectible.png')

			d = QImage()
			d.load(en.get('Image'))

			p = QPainter(i)
			p.drawImage(0,0,d)
			p.end()

			self.entity['pixmap'] = QPixmap.fromImage(i)

		else:
			self.entity['pixmap'] = QPixmap()
			self.entity['pixmap'].load(en.get('Image'))

	def itemChange(self, change, value):

		if change == self.ItemPositionChange:
			currentX, currentY = self.x(), self.y()

			x, y = value.x(), value.y()

			try:
				w = self.scene().roomWidth
				h = self.scene().roomHeight
			except:
				w = 26
				h = 14

			x = int((x + (self.SNAP_TO/2)) / self.SNAP_TO) * self.SNAP_TO
			y = int((y + (self.SNAP_TO/2)) / self.SNAP_TO) * self.SNAP_TO

			if x < 0: x = 0
			if x >= (self.SNAP_TO * (w-1)): x = (self.SNAP_TO * (w-1))
			if y < 0: y = 0
			if y >= (self.SNAP_TO * (h-1)): y = (self.SNAP_TO * (h-1))

			if x != currentX or y != currentY:
				self.entity['X'] = int(x/self.SNAP_TO)
				self.entity['Y'] = int(y/self.SNAP_TO)
			else:
				mainWindow.dirt()

			value.setX(x)
			value.setY(y)
			return value

		return QGraphicsItem.itemChange(self, change, value)

	def boundingRect(self):

		if self.entity['pixmap']:
			return QRectF(self.entity['pixmap'].rect())
		else:
			return QRectF(0.0,0.0,26.0,26.0)

	def updatePosition(self):
		self.setPos(self.entity['X']*26, self.entity['Y']*26)

	def paint(self, painter, option, widget):

		painter.setRenderHint(QPainter.Antialiasing, True)
		painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

		painter.setBrush(Qt.Dense5Pattern)
		painter.setPen(QPen(Qt.white))

		if self.entity['pixmap']:
			x = -(self.entity['pixmap'].width() -26) / 2
			y = -(self.entity['pixmap'].height()-26) / 2
			
			# Creeper special case
			if self.entity['Type'] in [240, 241, 242]: 
				w = self.scene().roomWidth -1
				h = self.scene().roomHeight-1
				ex = self.entity['X']
				ey = self.entity['Y']

				distances = [w - ex, ex, ey, h - ey]
				closest = min(distances)
				direction = distances.index(closest)

				painter.setPen(QPen(QColor(220,220,180), 2, Qt.DashDotLine))

				if direction == 0: # Right
					painter.drawLine(26,13, closest*26+26, 13)

				elif direction == 1: # Left
					painter.drawLine(0,13, -closest*26, 13)

				elif direction == 2: # Top
					painter.drawLine(13,0, 13, -closest*26)

				elif direction == 3: # Bottom
					painter.drawLine(13,26, 13, closest*26+26)
				
				painter.drawPixmap(x,y,self.entity['pixmap'])

			# Most Painting
			else:
				painter.drawPixmap(x,y,self.entity['pixmap'])

		else:
			painter.drawRect(0, 0, 26, 26)
			painter.drawText(4,16,str(self.entity['Type']))
			painter.drawText(4,32,str(self.entity['Variant']))
			painter.drawText(4,48,str(self.entity['Subtype']))
	
		if self.isSelected():
			painter.setPen(self.SELECTION_PEN)
			painter.setBrush(Qt.NoBrush)
			painter.drawRect(x,y,self.entity['pixmap'].width(), self.entity['pixmap'].height())

	def remove(self):
		self.scene().removeItem(self)

class Door(QGraphicsItem):

	def __init__(self, doorItem):
		QGraphicsItem.__init__(self)

		# Supplied entity info
		self.doorItem = doorItem
		self.exists = doorItem[2]

		self.setPos(self.doorItem[0]*26-13, self.doorItem[1]*26-13)

		tr = QTransform()
		if doorItem[0] == -1:
			tr.rotate(270)
			self.moveBy(-13, 0)
		elif doorItem[0] in [13,26]:
			tr.rotate(90)
			self.moveBy(13, 0)
		elif doorItem[1] in [7,14]:
			tr.rotate(180)
			self.moveBy(0, 13)
		else:
			self.moveBy(0, -13)

		self.image = QImage('resources/Backgrounds/Door.png').transformed(tr)
		self.disabledImage = QImage('resources/Backgrounds/DisabledDoor.png').transformed(tr)
	
	def paint(self, painter, option, widget):

		painter.setRenderHint(QPainter.Antialiasing, True)
		painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

		if self.exists:
			painter.drawImage(0,0, self.image)
		else:
			painter.drawImage(0,0, self.disabledImage)
	
	def boundingRect(self):
		return QRectF(0.0,0.0,64.0,52.0)

	def mouseDoubleClickEvent(self, event):

		if self.exists:
			self.exists = False
		else:
			self.exists = True

		self.doorItem[2] = self.exists

		event.accept()
		self.update()
		mainWindow.dirt()
	
	def remove(self):
		self.scene().removeItem(self)


########################
#     Dock Widgets     #
########################

# Room Selector
########################

class Room(QListWidgetItem):

	def __init__(self, name="New Room", doors=[], spawns=[], mytype=1, variant=0, difficulty=1, weight=1.0, width=13, height=7):
		"""Initializes the room item."""

		QListWidgetItem.__init__(self)

		self.setText(name)

		self.roomSpawns = spawns
		self.roomDoors = doors
		self.roomType = mytype
		self.roomVariant = variant
		self.roomDifficulty = difficulty
		self.roomWeight = weight
		self.roomWidth = width
		self.roomHeight = height

		self.roomBG = 1
		self.setRoomBG()

		self.setFlags(self.flags() | Qt.ItemIsEditable)
		self.setToolTip()

		if doors == []: self.makeNewDoors()
		self.renderDisplayIcon()

	def makeNewDoors(self):
		if self.roomWidth == 13 and self.roomHeight == 7:
			self.roomDoors = [[6,-1,True],[-1,3,True],[13,3,True],[6,7,True]]
		elif self.roomWidth == 26 and self.roomHeight == 14:
			self.roomDoors = [[6,-1,True],[-1,3,True],[-1,10,True],[19,-1,True],[6,14,True],[19,14,True],[26,3,True],[26,10,True]]
		elif self.roomWidth == 26:
			self.roomDoors = [[6,-1,True],[-1,3,True],[6,7,True],[19,-1,True],[19,7,True],[26,3,True]]
		elif self.roomHeight == 14:
			self.roomDoors = [[6,-1,True],[-1,3,True],[-1,10,True],[13,3,True],[13,10,True],[6,14,True]]

	def clearDoors(self):
		mainWindow.scene.clearDoors()
		for door in self.roomDoors:
			d = Door(door)
			mainWindow.scene.addItem(d)

	def getSpawnCount(self):
		ret = 0

		for x in self.roomSpawns:
			for y in x:
				if len(y) is not 0:
					ret += 1

		return ret

	def setToolTip(self):
		tip = "{4}x{5} - Type: {0}, Variant: {1}, Difficulty: {2}, Weight: {3}".format(self.roomType, self.roomVariant, self.roomDifficulty, self.roomWeight, self.roomWidth, self.roomHeight)
		QListWidgetItem.setToolTip(self, tip)

	def renderDisplayIcon(self):
		"""Renders the mini-icon for display."""

		q = QImage()
		q.load('resources/UI/RoomIcons.png')

		i = QIcon(QPixmap.fromImage(q.copy(self.roomType*16,0,16,16)))

		self.setIcon(i)

	def setRoomBG(self):
		c = self.roomType

		roomType = ['basement', 'cellar', 'caves', 'catacombs', 'depths', 'necropolis', 'womb', 'utero', 'sheol', 'cathedral', 'chest', 'dark room']
		for t in roomType:
			if t in mainWindow.path:
				self.roomBG = roomType.index(t)+1

		if c == 12:
			self.roomBG = 13
		elif c == 2:
			self.roomBG = 14
		elif c == 18:
			self.roomBG = 15
		elif c == 19:
			self.roomBG = 16
		elif c == 9:
			self.roomBG = 17
		elif c == 21:
			self.roomBG = 18
		elif c == 7:
			self.roomBG = 19

		elif c in [10,11,13,14,17]:
			self.roomBG = 9
		elif c in [15]:
			self.roomBG = 10
		elif c in [20]:
			self.roomBG = 11
		elif c in [3]:
			self.roomBG = 12

		elif c in [8]:
			if self.roomVariant in [2,6]:
				self.roomBG = 12
			elif self.roomVariant in [0]:
				self.roomBG = 8
			elif self.roomVariant in [1]:
				self.roomBG = 10
			else:
				self.roomBG = 1

class RoomDelegate(QStyledItemDelegate):

	def __init__(self):

		self.pixmap = QPixmap('resources/UI/CurrentRoom.png')
		QStyledItemDelegate.__init__(self)

	def paint(self, painter, option, index):

		painter.fillRect(option.rect.right()-19, option.rect.top(), 17, 16, QBrush(Qt.white))

		QStyledItemDelegate.paint(self, painter, option, index)

		item = mainWindow.roomList.list.item(index.row())
		if item:
			if item.data(100):
				painter.drawPixmap(option.rect.right()-19, option.rect.top(), self.pixmap)

class FilterMenu(QMenu):

	def __init__(self):

		QMenu.__init__(self)

	def paintEvent(self, event):
	
		QMenu.paintEvent(self, event)

		painter = QPainter(self) 

		for act in self.actions():
			rect = self.actionGeometry(act)
			painter.fillRect(rect.right()/2-12, rect.top()-2, 24, 24, QBrush(Qt.transparent))
			painter.drawPixmap(rect.right()/2-12, rect.top()-2, act.icon().pixmap(24, 24));    

class RoomSelector(QWidget):

	def __init__(self):
		"""Initialises the widget."""

		QWidget.__init__(self)

		self.layout = QVBoxLayout()
		self.layout.setSpacing(0)

		self.filterEntity = None

		self.setupFilters()
		self.setupList()
		self.setupToolbar()

		self.layout.addLayout(self.filter)
		self.layout.addWidget(self.list)
		self.layout.addWidget(self.toolbar)

		self.setLayout(self.layout)
		self.setButtonStates()

	def setupFilters(self):
		self.filter = QHBoxLayout()
		self.filter.setSpacing(4)

		fq = QImage()
		fq.load('resources/UI/FilterIcons.png')
		
		# Set the custom data
		self.filter.typeData = -1
		self.filter.weightData = -1
		self.filter.sizeData = -1

		# Entity Toggle Button
		self.entityToggle = QToolButton()
		self.entityToggle.setCheckable(True)
		self.entityToggle.checked = False
		self.entityToggle.setIconSize(QSize(24, 24))
		self.entityToggle.toggled.connect(self.setEntityToggle)
		self.entityToggle.toggled.connect(self.changeFilter)
		self.entityToggle.setIcon(QIcon(QPixmap.fromImage(fq.copy(0,0,24,24))))

		# Type Toggle Button
		self.typeToggle = QToolButton()
		self.typeToggle.setIconSize(QSize(24, 24))
		self.typeToggle.setPopupMode(QToolButton.InstantPopup)

		typeMenu = QMenu()

		q = QImage()
		q.load('resources/UI/RoomIcons.png')

		self.typeToggle.setIcon(QIcon(QPixmap.fromImage(fq.copy(1*24+4,4,16,16))))
		act = typeMenu.addAction(QIcon(QPixmap.fromImage(fq.copy(1*24+4,4,16,16))), '')
		act.setData(-1)

		for i in range(22):
			act = typeMenu.addAction(QIcon(QPixmap.fromImage(q.copy(i*16,0,16,16))), '')
			act.setData(i)

		self.typeToggle.triggered.connect(self.setTypeFilter)
		self.typeToggle.setMenu(typeMenu)

		# Weight Toggle Button
		self.weightToggle = QToolButton()
		self.weightToggle.setIconSize(QSize(24, 24))
		self.weightToggle.setPopupMode(QToolButton.InstantPopup)

		weightMenu = FilterMenu()

		q = QImage()
		q.load('resources/UI/WeightIcons.png')

		self.weightToggle.setIcon(QIcon(QPixmap.fromImage(fq.copy(2*24,0,24,24))))
		act = weightMenu.addAction(QIcon(QPixmap.fromImage(fq.copy(2*24,0,24,24))), '')
		act.setData(-1)
		act.setIconVisibleInMenu(False)

		w = [0.25,0.5,0.75,1.0,1.5,2.0,5.0,1000.0]
		for i in range(8):
			act = weightMenu.addAction(QIcon(QPixmap.fromImage(q.copy(i*24,0,24,24))), '')
			act.setData(w[i])
			act.setIconVisibleInMenu(False)

		self.weightToggle.triggered.connect(self.setWeightFilter)
		self.weightToggle.setMenu(weightMenu)

		# Size Toggle Button
		self.sizeToggle = QToolButton()
		self.sizeToggle.setIconSize(QSize(24, 24))
		self.sizeToggle.setPopupMode(QToolButton.InstantPopup)

		sizeMenu = FilterMenu()

		q = QImage()
		q.load('resources/UI/SizeIcons.png')

		self.sizeToggle.setIcon(QIcon(QPixmap.fromImage(fq.copy(3*24,0,24,24))))
		act = sizeMenu.addAction(QIcon(QPixmap.fromImage(fq.copy(3*24,0,24,24))), '')
		act.setData(-1)
		act.setIconVisibleInMenu(False)

		w = ['Small', 'Wide', 'Tall', 'Large']
		for i in range(4):
			act = sizeMenu.addAction(QIcon(QPixmap.fromImage(q.copy(i*24,0,24,24))), '')
			act.setData(w[i])
			act.setIconVisibleInMenu(False)

		self.sizeToggle.triggered.connect(self.setSizeFilter)
		self.sizeToggle.setMenu(sizeMenu)

		# Add to Layout
		self.filter.addStretch()
		self.filter.addWidget(QLabel("Filter by:"))
		self.filter.addWidget(self.entityToggle)
		self.filter.addWidget(self.typeToggle)
		self.filter.addWidget(self.weightToggle)
		self.filter.addWidget(self.sizeToggle)
		self.filter.setContentsMargins(4,0,0,4)

	def setupList(self):
		self.list = QListWidget()
		self.list.setViewMode(self.list.ListMode)
		self.list.setSelectionMode(self.list.ExtendedSelection)
		self.list.setResizeMode(self.list.Adjust)
		self.list.setContextMenuPolicy(Qt.CustomContextMenu)

		self.list.setAutoScroll(True)
		self.list.setDragEnabled(True)
		self.list.setDragDropMode(4)

		self.list.setVerticalScrollBarPolicy(0)
		self.list.setHorizontalScrollBarPolicy(1)

		self.list.setIconSize(QSize(52, 52))
		d = RoomDelegate()
		self.list.setItemDelegate(d)

		self.list.itemSelectionChanged.connect(self.setButtonStates)
		self.list.doubleClicked.connect(self.activateEdit)
		self.list.customContextMenuRequested.connect(self.customContextMenu)

	def setupToolbar(self):
		self.toolbar = QToolBar()

		self.addRoomButton = self.toolbar.addAction(QIcon(), 'Add', self.addRoom)
		self.removeRoomButton = self.toolbar.addAction(QIcon(), 'Delete', self.removeRoom)
		self.duplicateRoomButton = self.toolbar.addAction(QIcon(), 'Duplicate', self.duplicateRoom)
		self.exportRoomButton = self.toolbar.addAction(QIcon(), 'Export...', self.exportRoom)

	def activateEdit(self):
		self.list.editItem(self.selectedRoom())

	@pyqtSlot(QPoint)
	def customContextMenu(self, pos):
		menu = QMenu(self.list)

		# Size Changing Menu
		size = menu.addMenu('Size')
		s = size.addAction('Small')
		w = size.addAction('Wide')
		t = size.addAction('Tall')
		l = size.addAction('Large')

		size.triggered.connect(self.changeSize)
		if self.selectedRoom().roomWidth == 13 and self.selectedRoom().roomHeight == 7:
			s.setCheckable(True)
			s.setChecked(True)
		elif self.selectedRoom().roomWidth == 26 and self.selectedRoom().roomHeight == 14:
			l.setCheckable(True)
			l.setChecked(True)
		elif self.selectedRoom().roomWidth == 26:
			w.setCheckable(True)
			w.setChecked(True)
		elif self.selectedRoom().roomHeight == 14:
			t.setCheckable(True)
			t.setChecked(True)

		menu.addSeparator()

		# Type
		Type = QWidgetAction(menu)
		c = QComboBox()

		types= ["Null Room", "Normal Room", "Shop", "Error Room", "Treasure Room", "Boss Room", 
				"Mini-Boss Room", "Secret Room", "Super Secret Room", "Arcade", "Curse Room", "Challenge Room", 
				"Library", "Sacrifice Room", "Devil Room", "Angel Room", "Item Dungeon", "Boss Rush Room", 
				"Isaac's Room", "Barren Room", "Chest Room", "Dice Room", "Black Market"] 

		if "00." not in mainWindow.path:
			types=["Null Room", "Normal Room"]

		c.addItems(types)
		c.setCurrentIndex(self.selectedRoom().roomType)
		c.currentIndexChanged.connect(self.changeType)
		Type.setDefaultWidget(c)
		menu.addAction(Type)

		# Difficulty
		diff = menu.addMenu('Difficulty')
		
		for d in [0,1,2,5,10]:
			m = diff.addAction('{0}'.format(d))

			if self.selectedRoom().roomDifficulty == d:
				m.setCheckable(True)
				m.setChecked(True)

		diff.triggered.connect(self.changeDifficulty)

		# Weight
		weight = menu.addMenu('Weight')
		
		for w in [0.25,0.5,0.75,1.0,1.5,2.0,5.0,1000.0]:
			m = weight.addAction('{0}'.format(w))

			if self.selectedRoom().roomWeight == w:
				m.setCheckable(True)
				m.setChecked(True)

		weight.triggered.connect(self.changeWeight)

		# Variant
		Variant = QWidgetAction(menu)
		s = QSpinBox()
		s.setRange(0,65534)

		s.setValue(self.selectedRoom().roomVariant)

		Variant.setDefaultWidget(s)
		s.valueChanged.connect(self.changeVariant)
		menu.addAction(Variant)

		# End it
		menu.exec_(self.list.mapToGlobal(pos))

	@pyqtSlot(bool)
	def setEntityToggle(self, checked):
		self.entityToggle.checked = checked

	@pyqtSlot(QAction)
	def setTypeFilter(self, action):
		self.filter.typeData = action.data()
		self.typeToggle.setIcon(action.icon())
		self.changeFilter()

	@pyqtSlot(QAction)
	def setWeightFilter(self, action):
		self.filter.weightData = action.data()
		self.weightToggle.setIcon(action.icon())
		self.changeFilter()

	@pyqtSlot(QAction)
	def setSizeFilter(self, action):
		self.filter.sizeData = action.data()
		self.sizeToggle.setIcon(action.icon())
		self.changeFilter()

	@pyqtSlot()
	def changeFilter(self):
		
		# Here we go
		for room in self.getRooms():
			entityCond = typeCond = weightCond = sizeCond = True

			# Check if the right entity is in the room
			if self.entityToggle.checked and self.filterEntity:
				entityCond = False

				for x in room.roomSpawns:
					for y in x:
						for e in y:
							if int(self.filterEntity.ID) in e and int(self.filterEntity.subtype) in e and int(self.filterEntity.variant) in e:
								entityCond = True

			# Check if the room is the right type
			if self.filter.typeData is not -1:
				typeCond = self.filter.typeData == room.roomType

			# Check if the room is the right weight
			if self.filter.weightData is not -1:
				weightCond = self.filter.weightData == room.roomWeight

			# Check if the room is the right size
			if self.filter.sizeData is not -1:
				sizeCond = False

				text = self.filter.sizeData
				w = room.roomWidth
				h = room.roomHeight

				if w is 13 and h is 7 and text == 'Small':
					sizeCond = True
				if w is 26 and h is 7 and text == 'Wide':
					sizeCond = True
				if w is 13 and h is 14 and text == 'Tall':
					sizeCond = True
				if w is 26 and h is 14 and text == 'Large':
					sizeCond = True

			# Filter em' out
			if entityCond and typeCond and weightCond and sizeCond:
				room.setHidden(False)
			else:
				room.setHidden(True)		

	def setEntityFilter(self, entity):
		self.filterEntity = entity
		self.entityToggle.setIcon(entity.icon)
		self.changeFilter()

	@pyqtSlot(QAction)
	def changeSize(self, action):

		# Set the Size
		if action.text() == "Small":
			w,h = 13,7
		elif action.text() == "Wide":
			w,h = 26,7
		elif action.text() == "Tall":
			w,h = 13,14
		elif action.text() == "Large":
			w,h = 26,14

		# No sense in doing work we don't have to!
		if self.selectedRoom().roomWidth == w and self.selectedRoom().roomHeight == h:
			return

		# Check to see if resizing will destory any entities
		warn = False
		mainWindow.storeEntityList()

		for y in enumerate(self.selectedRoom().roomSpawns):
			for x in enumerate(y[1]):
				for entity in x[1]:

					if x[0] >= w or y[0] >= h:
						warn = True

		if warn:
			msgBox = QMessageBox(QMessageBox.Warning,
					"Resize Room?", "Resizing this room will delete entities placed outside the new size. Are you sure you want to resize this room?",
					QMessageBox.NoButton, self)
			msgBox.addButton("Resize", QMessageBox.AcceptRole)
			msgBox.addButton("Cancel", QMessageBox.RejectRole)
			if msgBox.exec_() == QMessageBox.RejectRole:
				# It's time for us to go now.
				return

		# Clear the room and reset the size
		mainWindow.scene.clear()
		self.selectedRoom().roomWidth = w
		self.selectedRoom().roomHeight = h

		self.selectedRoom().makeNewDoors()
		self.selectedRoom().clearDoors()
		mainWindow.scene.newRoomSize(w, h)
		
		mainWindow.editor.resizeEvent(QResizeEvent(mainWindow.editor.size(), mainWindow.editor.size()))

		# Spawn those entities
		for y in enumerate(self.selectedRoom().roomSpawns):
			for x in enumerate(y[1]):
				for entity in x[1]:
					if x[0] >= w or y[0] >= h: continue

					e = Entity(x[0], y[0], entity[0], entity[1], entity[2], entity[3])
					mainWindow.scene.addItem(e)

		self.selectedRoom().setToolTip()
		mainWindow.dirt()

	@pyqtSlot(int)
	def changeType(self, rtype):
		self.selectedRoom().roomType = rtype
		self.selectedRoom().renderDisplayIcon()
		self.selectedRoom().setRoomBG()

		self.selectedRoom().setToolTip()

		mainWindow.scene.update()
		mainWindow.dirt()

	@pyqtSlot(int)
	def changeVariant(self, var):
		self.selectedRoom().roomVariant = var
		self.selectedRoom().setToolTip()
		mainWindow.dirt()

	@pyqtSlot(QAction)
	def changeDifficulty(self, action):
		self.selectedRoom().roomDifficulty = int(action.text())
		self.selectedRoom().setToolTip()
		mainWindow.dirt()

	@pyqtSlot(QAction)
	def changeWeight(self, action):
		self.selectedRoom().roomWeight = float(action.text())
		self.selectedRoom().setToolTip()
		mainWindow.dirt()

	def keyPressEvent(self, event):
		self.list.keyPressEvent(event)

		if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
			self.removeRoom()

	def addRoom(self):
		"""Creates a new room."""
		
		r = Room()
		self.list.insertItem(self.list.currentRow()+1, r)
		self.list.setCurrentItem(r, QItemSelectionModel.ClearAndSelect)
		mainWindow.dirt()

	def removeRoom(self):
		"""Removes selected room (no takebacks)"""

		rooms = self.selectedRooms()
		if rooms is None or len(rooms) == 0:
			return

		if len(rooms) == 1:
			s = "this room"
		else:
			s = "these rooms"

		msgBox = QMessageBox(QMessageBox.Warning,
				"Delete Room?", "Are you sure you want to delete {0}? This action cannot be undone.".format(s),
				QMessageBox.NoButton, self)
		msgBox.addButton("Delete", QMessageBox.AcceptRole)
		msgBox.addButton("Cancel", QMessageBox.RejectRole)
		if msgBox.exec_() == QMessageBox.AcceptRole:

			self.list.clearSelection()
			for item in rooms:
				self.list.takeItem(self.list.currentRow())
	
			mainWindow.dirt()

	def duplicateRoom(self):
		"""Duplicates the selected room"""

		rooms = self.selectedRooms()
		if rooms is None or len(rooms) == 0:
			return

		mainWindow.storeEntityList()

		rv = rooms[0].roomVariant
		v = 0

		initialPlace = self.list.currentRow()
		self.selectedRoom().setData(100, False)
		self.list.setCurrentItem(None, QItemSelectionModel.ClearAndSelect)

		for room in rooms:
			v += 1

			r = Room(	room.text() + ' (copy)', [list(door) for door in room.roomDoors], room.roomSpawns, room.roomType, 
						v+rv, room.roomDifficulty, room.roomWeight, room.roomWidth, room.roomHeight)

			self.list.insertItem(initialPlace+v, r)
			self.list.setCurrentItem(r, QItemSelectionModel.Select)

		mainWindow.dirt()
	
	def exportRoom(self):

		# Get a new
		dialogDir = '' if mainWindow.path is '' else os.path.dirname(mainWindow.path)
		target = QFileDialog.getSaveFileName(self, 'Select a new name or an existing stb', dialogDir, 'Stage Bundle (*.stb)', '', QFileDialog.DontConfirmOverwrite)
		mainWindow.restoreEditMenu()

		if len(target) == 0:
			return

		path = target[0]

		# Append these rooms onto the new stb
		if os.path.exists(path):
			rooms = self.selectedRooms()
			oldRooms = mainWindow.open(path)

			oldRooms.extend(rooms)

			mainWindow.save(oldRooms, path)

		# Make a new stb with the selected rooms
		else:
			mainWindow.save(self.selectedRooms(), path)

	def setButtonStates(self):
		rooms = len(self.selectedRooms()) > 0

		self.removeRoomButton.setEnabled(rooms)
		self.duplicateRoomButton.setEnabled(rooms)
		self.exportRoomButton.setEnabled(rooms)

	def selectedRoom(self):
		return self.list.currentItem()

	def selectedRooms(self):
		return self.list.selectedItems()

	def getRooms(self):
		ret = []
		for i in range(self.list.count()):
			ret.append(self.list.item(i))

		return ret

# Entity Palette
########################

class EntityGroupItem(object):
	"""Group Item to contain Entities for sorting"""

	def __init__(self, name):

		self.objects = []
		self.startIndex = 0
		self.endIndex = 0

		self.name = name
		self.alignment = Qt.AlignCenter

	def getItem(self, index):
		''' Retrieves an item of a specific index. The index is already checked for validity '''

		if index == self.startIndex:
			return self

		if (index <= self.startIndex + len(self.objects)):
			return self.objects[index - self.startIndex - 1]

	def calculateIndices(self, index):		
		self.startIndex = index
		self.endIndex = len(self.objects) + index

class EntityItem(object):
	"""A single entity, pretty much just an icon and a few params."""

	def __init__(self, name, ID, subtype, variant, iconPath):
		self.name = name
		self.ID = ID
		self.subtype = subtype
		self.variant = variant
		self.icon = QIcon(iconPath)

class EntityGroupModel(QAbstractListModel):
	"""Model containing all the grouped objects in a tileset"""

	def __init__(self, kind):
		self.groups = {}
		self.kind = kind
		self.view = None

		QAbstractListModel.__init__(self)

		global entityXML
		enList = entityXML.findall("entity")

		for en in enList:
			g = en.get('Group')
			k = en.get('Kind')

			if self.kind == k:
				if g not in self.groups.keys():
					self.groups[g] = EntityGroupItem(g)

				e = EntityItem(en.get('Name'), en.get('ID'), en.get('Subtype'), en.get('Variant'), en.get('Image'))

				self.groups[g].objects.append(e)

		i = 0
		for key, group in sorted(self.groups.items()):
			group.calculateIndices(i)
			i = group.endIndex + 1

	def rowCount(self, parent=None):
		c = 0

		for group in self.groups.values():
			c += len(group.objects) + 1

		return c

	def flags(self, index):
		item = self.getItem(index.row())

		if isinstance(item, EntityGroupItem):
			return Qt.NoItemFlags
		else:
			return Qt.ItemIsEnabled | Qt.ItemIsSelectable

	def getItem(self, index):
		for group in self.groups.values():
			if (group.startIndex <= index) and (index <= group.endIndex):
				return group.getItem(index)

	def data(self, index, role=Qt.DisplayRole):
		# Should return the contents of a row when asked for the index 
		#
		# Can be optimized by only dealing with the roles we need prior
		# to lookup: Role order is 13, 6, 7, 9, 10, 1, 0, 8

		if ((role > 1) and (role < 6)):
			return None

		elif (role == Qt.ForegroundRole):
			return QBrush(Qt.black)

		elif role == Qt.TextAlignmentRole:
			return Qt.AlignCenter


		if not index.isValid(): return None
		n = index.row()

		if n < 0: return None
		if n >= self.rowCount(): return None

		item = self.getItem(n)

		if role == Qt.DecorationRole:
			if isinstance(item, EntityItem):
				return item.icon

		if role == Qt.ToolTipRole or role == Qt.StatusTipRole or role == Qt.WhatsThisRole:
			if isinstance(item, EntityItem):
				return "{0}".format(item.name) 

		elif role == Qt.DisplayRole:
			if isinstance(item, EntityGroupItem):
				return item.name

		elif (role == Qt.SizeHintRole):
			if isinstance(item, EntityGroupItem):
				return QSize(self.view.viewport().width(), 24)

		elif role == Qt.BackgroundRole:
			if isinstance(item, EntityGroupItem):

				colour = 165

				if colour > 255:
					colour = 255

				brush = QBrush(QColor(colour, colour, colour), Qt.Dense4Pattern)

				return brush

		elif (role == Qt.FontRole):
			font = QFont()
			font.setPixelSize(16)
			font.setBold(True)

			return font

		return None

class EntityPalette(QWidget):

	def __init__(self):
		"""Initialises the widget. Remember to call setTileset() on it
		whenever the layer changes."""

		QWidget.__init__(self)

		self.menuSetup = False

		self.layout = QVBoxLayout()
		self.layout.setSpacing(0)

		self.tabs = QTabWidget()
		self.layout.addWidget(self.tabs)

		for group in ["Pickups", "Enemies", "Bosses", "Stage", "Collect"]:

			listView = QListView()
			listView.setFlow(QListView.LeftToRight)
			listView.setLayoutMode(QListView.SinglePass)
			listView.setMovement(QListView.Static)
			listView.setResizeMode(QListView.Adjust)
			listView.setWrapping(True)
			listView.setIconSize(QSize(26,26))

			listView.setModel(EntityGroupModel(group))
			listView.model().view = listView

			listView.clicked.connect(self.objSelected)

			if group == "Bosses":
				listView.setIconSize(QSize(52,52))

			if group == "Collect":
				listView.setIconSize(QSize(32,64))

			self.tabs.addTab(listView, group)

		self.setLayout(self.layout)

	def currentSelectedObject(self):
		"""Returns the currently selected object reference, for painting purposes."""

		index = self.tabs.currentWidget().currentIndex().row()
		obj = self.tabs.currentWidget().model().getItem(index)

		return obj

	@pyqtSlot()
	def objSelected(self):
		"""Throws a signal emitting the current object when changed"""
		self.objChanged.emit(self.currentSelectedObject())

		# Throws a signal when the selected object is used as a replacement
		if QApplication.keyboardModifiers() == Qt.AltModifier:
			self.objReplaced.emit(self.currentSelectedObject())

	objChanged = pyqtSignal(EntityItem)
	objReplaced = pyqtSignal(EntityItem)


########################
#      Main Window     #
########################

class MainWindow(QMainWindow):

	def __init__(self):
		QMainWindow.__init__(self)

		self.setWindowTitle('Basement Renovator')
		self.setWindowIcon(QIcon('Resources/Koopatlas.png'))
		self.setIconSize(QSize(16, 16))

		self.dirty = False
		
		self.scene = RoomScene()
		self.clipboard = None

		self.editor = RoomEditorWidget(self.scene)
		self.setCentralWidget(self.editor)

		self.setupDocks()
		self.setupMenuBar()

		# Restore Settings
		if settings.value('GridEnabled', False): self.showGrid()
		if settings.value('BitfontEnabled', False): self.switchBitFont()

		self.restoreState(settings.value('MainWindowState', self.saveState()), 0)
		self.restoreGeometry(settings.value('MainWindowGeometry', self.saveGeometry()))

		# Setup a new map
		self.newMap()	
		self.clean()

	def setupMenuBar(self):
		mb = self.menuBar()

		f = mb.addMenu('&File')
		self.fa = f.addAction('New',						self.newMap, QKeySequence("Ctrl+N"))
		self.fb = f.addAction('Open...',					self.openMap, QKeySequence("Ctrl+O"))
		f.addSeparator()
		self.fd = f.addAction('Save',						self.saveMap, QKeySequence("Ctrl+S"))
		self.fe = f.addAction('Save As...',					self.saveMapAs, QKeySequence("Ctrl+Shift+S"))
		f.addSeparator()
		self.fg = f.addAction('Take Screenshot...',			self.screenshot, QKeySequence("Ctrl+Alt+S"))
		f.addSeparator()
		# self.fi = f.addAction('Quit')

		self.e = mb.addMenu('Edit')
		self.ea = self.e.addAction('Copy',						self.copy, QKeySequence.Copy)
		self.eb = self.e.addAction('Cut',						self.cut, QKeySequence.Cut)
		self.ec = self.e.addAction('Paste',						self.paste, QKeySequence.Paste)
		self.ed = self.e.addAction('Select All',					self.selectAll, QKeySequence.SelectAll)
		self.ee = self.e.addAction('Deselect',					self.deSelect, QKeySequence("Ctrl+D"))
		self.e.addSeparator()

		v = mb.addMenu('View')
		self.wa = v.addAction('Hide Grid',					self.showGrid, QKeySequence("Ctrl+G"))
		self.wd = v.addAction('Use Aliased Counter',		self.switchBitFont, QKeySequence("Ctrl+Alt+A"))
		v.addSeparator()
		self.wb = v.addAction('Hide Entity Painter',		self.showPainter, QKeySequence("Ctrl+Alt+P"))
		self.wc = v.addAction('Hide Room List',				self.showRoomList, QKeySequence("Ctrl+Alt+R"))

		h = mb.addMenu('Help')
		self.ha = h.addAction('About Basement Renovator',			self.aboutDialog)
		self.hb = h.addAction('Basement Renovator Documentation',	self.goToHelp)
		# self.hc = h.addAction('Keyboard Shortcuts')

	def setupDocks(self):
		self.roomList = RoomSelector()
		self.roomListDock = QDockWidget('Rooms')
		self.roomListDock.setWidget(self.roomList)
		self.roomListDock.visibilityChanged.connect(self.updateDockVisibility)
		self.roomListDock.setObjectName("RoomListDock")

		self.roomList.list.currentItemChanged.connect(self.handleSelectedRoomChanged)

		self.addDockWidget(Qt.RightDockWidgetArea, self.roomListDock)

		self.EntityPalette = EntityPalette()
		self.EntityPaletteDock = QDockWidget('Entity Palette')
		self.EntityPaletteDock.setWidget(self.EntityPalette)
		self.EntityPaletteDock.visibilityChanged.connect(self.updateDockVisibility)
		self.EntityPaletteDock.setObjectName("EntityPaletteDock")

		self.EntityPalette.objChanged.connect(self.handleObjectChanged)
		self.EntityPalette.objReplaced.connect(self.handleObjectReplaced)

		self.addDockWidget(Qt.LeftDockWidgetArea, self.EntityPaletteDock)

	def restoreEditMenu(self):
		a = self.e.actions()
		self.e.insertAction(a[1], self.ea)
		self.e.insertAction(a[2], self.eb)
		self.e.insertAction(a[3], self.ec)
		self.e.insertAction(a[4], self.ed)
		self.e.insertAction(a[5], self.ee)

	def updateTitlebar(self):
		if self.path is '':
			effectiveName = 'Untitled Map'
		else:
			effectiveName = os.path.basename(self.path)

		self.setWindowTitle('%s - Basement Renovator' % effectiveName)

	def checkDirty(self):
		if self.dirty is False:
			return False

		msgBox = QMessageBox(QMessageBox.Warning,
				"File is not saved", "Completing this operation without saving could cause loss of data.",
				QMessageBox.NoButton, self)
		msgBox.addButton("Continue", QMessageBox.AcceptRole)
		msgBox.addButton("Cancel", QMessageBox.RejectRole)
		if msgBox.exec_() == QMessageBox.AcceptRole:
			return False

		return True

	def dirt(self):
		self.dirty = True

	def clean(self):
		self.dirty = False

	def storeEntityList(self, room=None):
		if not room:
			room = self.roomList.selectedRoom()

		eList = self.scene.items()

		spawns = [[[] for y in range(26)] for x in range(14)]
		doors = []

		for e in eList:
			if isinstance(e, Door):
				doors.append(e.doorItem)

			else:
				spawns[e.entity['Y']][e.entity['X']].append([e.entity['Type'], e.entity['Variant'], e.entity['Subtype'], e.entity['Weight']])

		room.roomSpawns = spawns
		room.roomDoors = doors

	def closeEvent(self, event):
		"""Handler for the main window close event"""
		
		if self.checkDirty():
			event.ignore()
		else:
			# save our state			
			settings.setValue('MainWindowGeometry', self.saveGeometry())
			settings.setValue('MainWindowState', self.saveState(0))			
						
			event.accept()


#####################
# Slots for Widgets #
#####################

	@pyqtSlot(Room, Room)
	def handleSelectedRoomChanged(self, current, prev):

		if current:

			# Encode the current room, just in case there are changes
			if prev:
				self.storeEntityList(prev)

				# Clear the current room mark
				prev.setData(100, False)

			# Clear the room and reset the size
			self.scene.clear()
			self.scene.newRoomSize(current.roomWidth, current.roomHeight)
			
			self.editor.resizeEvent(QResizeEvent(self.editor.size(), self.editor.size()))

			# Make some doors
			current.clearDoors()

			# Spawn those entities
			for y in enumerate(current.roomSpawns):
				for x in enumerate(y[1]):
					for entity in x[1]:
						e = Entity(x[0], y[0], entity[0], entity[1], entity[2], entity[3])
						self.scene.addItem(e)

			# Make the current Room mark for clearer multi-selection
			current.setData(100, True)

	@pyqtSlot(EntityItem)
	def handleObjectChanged(self, entity):
		self.editor.objectToPaint = entity
		self.roomList.setEntityFilter(entity)

	@pyqtSlot(EntityItem)
	def handleObjectReplaced(self, entity):
		for item in self.scene.selectedItems():
			item.entity['Type'] = int(entity.ID)
			item.entity['Variant'] = int(entity.variant)
			item.entity['Subtype'] = int(entity.subtype)

			item.getEntityInfo(int(entity.ID), int(entity.subtype), int(entity.variant))
			item.update()

		self.dirt()


########################
# Slots for Menu Items #
########################

# File
########################
	def newMap(self):
		if self.checkDirty(): return
		self.roomList.list.clear()
		self.scene.clear()
		self.path = ''

		self.updateTitlebar()
		self.dirt()

	def openMap(self):

		if self.checkDirty(): return

		target = QFileDialog.getOpenFileName(
			self, 'Open Map', '', 'Stage Bundle (*.stb)')
		self.restoreEditMenu()

		# Looks like nothing was selected
		if len(target[0]) == 0:
			return

		self.roomList.list.clear()
		self.scene.clear()
		self.path = ''

		self.path = target[0]
		self.updateTitlebar()

		rooms = self.open()
		for room in rooms:
			self.roomList.list.addItem(room)

		self.clean()

	def open(self, path=None):

		if not path:
			path = self.path

		# Let's read the file and parse it into our list items
		stb = open(path, 'rb').read()

		# Room count
		rooms = struct.unpack_from('<I', stb, 0)[0]
		off = 4
		ret = []

		for room in range(rooms):

			# Room Type, Room Variant, Difficulty, Length of Room Name String
			roomData = struct.unpack_from('<IIBH', stb, off)
			off += 11

			# Room Name
			roomName = struct.unpack_from('<{0}s'.format(roomData[3]), stb, off)[0].decode()
			off += roomData[3]

			# Weight, width, height, number of doors, number of entities
			entityTable = struct.unpack_from('<fBBBH', stb, off)
			off += 9

			doors = []
			for door in range(entityTable[3]):
				# X, Y, exists
				d = struct.unpack_from('<hh?', stb, off)
				doors.append([d[0], d[1], d[2]])
				off += 5

			spawns = [[[] for y in range(26)] for x in range(14)]
			for entity in range(entityTable[4]):
				# x, y, number of entities at this position
				spawnLoc = struct.unpack_from('<hhB', stb, off)
				off += 5

				for spawn in range(spawnLoc[2]):
					#  type, variant, subtype, weight
					t = struct.unpack_from('<HHHf', stb, off)
					spawns[spawnLoc[1]][spawnLoc[0]].append([t[0], t[1], t[2], t[3]])
					off += 10

			r = Room(roomName, doors, spawns, roomData[0], roomData[1], roomData[2], entityTable[0], entityTable[1], entityTable[2])
			ret.append(r)

		return ret

	def saveMap(self, forceNewName=False):
		target = self.path

		if target is '' or forceNewName:
			dialogDir = '' if target is '' else os.path.dirname(target)
			target = QFileDialog.getSaveFileName(self, 'Save Map', dialogDir, 'Stage Bundle (*.stb)')
			self.restoreEditMenu()

			if len(target) == 0:
				return

			self.path = target[0]
			self.updateTitlebar()

		self.save(self.roomList.getRooms())
		self.clean()

	def saveMapAs(self):
		self.saveMap(True)

	def save(self, rooms, path=None):
		if not path:
			path = self.path

		self.storeEntityList()

		stb = open(path, 'wb')
		out = struct.pack('<I', len(rooms))

		for room in rooms:

			out += struct.pack('<IIBH{0}sfBB'.format(len(room.text())),
							 room.roomType, room.roomVariant, room.roomDifficulty, len(room.text()),
							 room.text().encode(), room.roomWeight, room.roomWidth, room.roomHeight)

			# Doors and Entities
			out += struct.pack('<BH', len(room.roomDoors), room.getSpawnCount())

			for door in room.roomDoors:
				out += struct.pack('<hh?', door[0], door[1], door[2])

			for y in enumerate(room.roomSpawns):
				for x in enumerate(y[1]):
					if len(x[1]) == 0: continue

					out += struct.pack('<hhB', x[0], y[0], len(x[1]))

					for entity in x[1]:
						out += struct.pack('<HHHf', entity[0], entity[1], entity[2], 2.0)

		stb.write(out)

	@pyqtSlot()
	def screenshot(self):
		fn = QFileDialog.getSaveFileName(self, 'Choose a new filename', 'untitled.png', 'Portable Network Grahics (*.png)')[0]
		if fn == '': return

		g = self.scene.grid
		self.scene.grid = False

		ScreenshotImage = QImage(self.scene.sceneRect().width(), self.scene.sceneRect().height(), QImage.Format_ARGB32)
		ScreenshotImage.fill(Qt.transparent)
		
		RenderPainter = QPainter(ScreenshotImage)
		self.scene.render(RenderPainter, QRectF(ScreenshotImage.rect()), self.scene.sceneRect())
		RenderPainter.end()
		   
		ScreenshotImage.save(fn, 'PNG', 50)

		self.scene.grid = g

# Edit
########################
	@pyqtSlot()
	def selectAll(self):

		path = QPainterPath()
		path.addRect(self.scene.sceneRect())
		self.scene.setSelectionArea(path)

	@pyqtSlot()
	def deSelect(self):
		self.scene.clearSelection()

	@pyqtSlot()
	def copy(self):
		self.clipboard = []
		for item in self.scene.selectedItems():
			self.clipboard.append([item.entity['X'], item.entity['Y'], item.entity['Type'], item.entity['Variant'], item.entity['Subtype'], item.entity['Weight']])

	@pyqtSlot()
	def cut(self):
		self.clipboard = []
		for item in self.scene.selectedItems():
			self.clipboard.append([item.entity['X'], item.entity['Y'], item.entity['Type'], item.entity['Variant'], item.entity['Subtype'], item.entity['Weight']])
			item.remove()

	@pyqtSlot()
	def paste(self):
		if not self.clipboard: return

		self.scene.clearSelection()
		for item in self.clipboard:
			i = Entity(*item)
			self.scene.addItem(i)

		self.dirt()

# Miscellaneous
########################

	@pyqtSlot()
	def showGrid(self):
		"""Handle toggling of the grid being showed"""
		settings.setValue('GridEnabled', self.scene.grid)

		if self.wa.text() == "Show Grid":
			self.scene.grid = True
			self.wa.setText("Hide Grid")
		else:
			self.scene.grid = False
			self.wa.setText("Show Grid")
		
		self.scene.update()

	@pyqtSlot()
	def switchBitFont(self):
		"""Handle toggling of the bitfont for entity counting"""
		settings.setValue('BitfontEnabled', self.scene.bitText)

		if self.wd.text() == "Use Aliased Counter":
			self.scene.bitText = False
			self.wd.setText("Use Bitfont Counter")
		else:
			self.scene.bitText = True
			self.wd.setText("Use Aliased Counter")

		self.scene.update()

	@pyqtSlot()
	def showPainter(self):
		if self.EntityPaletteDock.isVisible(): 
			self.EntityPaletteDock.hide()
		else:
			self.EntityPaletteDock.show()

		self.updateDockVisibility()

	@pyqtSlot()
	def showRoomList(self):
		if self.roomListDock.isVisible():
			self.roomListDock.hide()
		else:
			self.roomListDock.show()

		self.updateDockVisibility()

	@pyqtSlot()
	def updateDockVisibility(self):

		if self.EntityPaletteDock.isVisible():
			self.wb.setText('Hide Entity Painter')
		else:
			self.wb.setText('Show Entity Painter')

		if self.roomListDock.isVisible():
			self.wc.setText('Hide Room List')
		else:
			self.wc.setText('Show Room List')


# Help
########################

	@pyqtSlot(bool)
	def aboutDialog(self):
		caption = "About the Basement Renovator"

		text = "<big><b>Basement Renovator</b></big><br><br>    The Basement Renovator Editor is an editor for custom rooms, for use with the Binding of Isaac Rebirth. In order to use it, you must have unpacked the .stb files from Binding of Isaac Rebirth.<br><br>    The Basement Renovator was programmed by Tempus (u/Chronometrics).<br><br>    Find the source at <github link here>."


		msg = QMessageBox.about(mainWindow, caption, text)

	@pyqtSlot(bool)
	def goToHelp(self):
		QDesktopServices().openUrl(QUrl('http://www.reddit.com/r/themoddingofisaac'))


if __name__ == '__main__':

	import sys

	# XML Globals
	entityXML = getEntityXML()

	# Application
	app = QApplication(sys.argv)
	app.setWindowIcon(QIcon('resources/UI/BasementRenovator.png'))

	settings = QSettings('RoomEditor', 'Binding of Isaac Rebirth: Room Editor')

	mainWindow = MainWindow()
	mainWindow.setWindowIcon(QIcon('resources/UI/BasementRenovator-Small.png'))
	mainWindow.setGeometry(100, 500, 1280, 600)
	mainWindow.show()

	sys.exit(app.exec_())
