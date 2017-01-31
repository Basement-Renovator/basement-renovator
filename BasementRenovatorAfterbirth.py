#!/usr/bin/python3
###########################################
#
#    Binding of Isaac: Rebirth Stage Editor
#		by Colin Noga
#		   Chronometrics / Tempus
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
#   Afterbirth Todo:
#		Fix up Rebirth/Afterbirth detection
#
#	Low priority
#		Clear Corner Rooms Grid
#		Fix icon for win_setup.py
#


from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from collections import OrderedDict

import struct, os, subprocess, platform, webbrowser
import xml.etree.ElementTree as ET
import psutil


########################
#       XML Data       #
########################

def getEntityXML():
	tree = ET.parse('resources/EntitiesAfterbirthPlus.xml')
	root = tree.getroot()

	return root

def findModsPath():
	modsPath = ''

	if QFile.exists(settings.value('ModsFolder')):
		modsPath = settings.value('ModsFolder')

	else:
		cantFindPath = False
		# Windows path things
		if "Windows" in platform.system():
			modsPath = os.path.join(os.path.expanduser("~"), "Documents", "My Games", "Binding of Isaac Afterbirth+ Mods")
			if not QFile.exists(modsPath):
				cantFindPath = True

		# Mac Path things
		elif "Darwin" in platform.system():
			modsPath = os.path.expanduser("~/Library/Application Support/Binding of Isaac Afterbirth+ Mods")
			if not QFile.exists(modsPath):
				cantFindPath = True

		# Linux and others
		else:
			modsPath = os.path.expanduser("~/.local/share/binding of isaac afterbirth+ mods/")
			if not QFile.exists(modsPath):
				cantFindPath = True

		# Fallback Resource Folder Locating
		if cantFindPath == True:
			modsPathOut = QFileDialog.getExistingDirectory(None, 'Please Locate The Binding of Isaac: Afterbirth+ Mods Folder')
			if not modsPathOut:
				QMessageBox.warning(None, "Error", "Couldn't locate Mods folder and no folder was selected.")
				return
			else:
				modsPath = modsPathOut
			if modsPath == "":
				QMessageBox.warning(None, "Error", "Couldn't locate Mods folder and no folder was selected.")
				return
			if not QDir(modsPath).exists:
				QMessageBox.warning(None, "Error", "Selected folder does not exist or is not a folder.")
				return

		# Looks like nothing was selected
		if len(modsPath) == 0:
			QMessageBox.warning(None, "Error", "Could not find The Binding of Isaac: Afterbirth+ Mods folder (" + modsPath + ")")
			return

		settings.setValue('ModsFolder', modsPath)

	return modsPath

def linuxPathSensitivityTraining(path):

	path = path.replace("\\", "/")

	directory, file = os.path.split(path)

	contents = os.listdir(directory)

	for item in contents:
		if item.lower() == file.lower():
			return os.path.normpath(os.path.join(directory, item))

	return os.path.normpath(path)


########################
#      Scene/View      #
########################

class RoomScene(QGraphicsScene):

	def __init__(self):
		QGraphicsScene.__init__(self, 0, 0, 0, 0)
		self.newRoomSize(13, 7, 1)

		self.BG = [
			"01_basement", "02_cellar", "03_caves", "04_catacombs",
			"05_depths", "06_necropolis", "07_the womb", "08_utero",
			"09_sheol", "10_cathedral", "11_chest", "12_darkroom",
			"0a_library", "0b_shop", "0c_isaacsroom", "0d_barrenroom",
			"0e_arcade", "0e_diceroom", "0f_secretroom", "18_bluewomb"
		]
		self.grid = True

		# Make the bitfont
		q = QImage()
		q.load('resources/UI/Bitfont.png')

		self.bitfont = [QPixmap.fromImage(q.copy(i * 12, 0, 12, 12)) for i in range(10)]
		self.bitText = True

		self.tile = None

	def newRoomSize(self, w, h, s):
		# Fuck their room size code is inelegant and annoying - these are kept for error checking purposes, of which I didn't do a great job
		self.initialRoomWidth = w
		self.initialRoomHeight = h

		# Drawing variables
		self.roomWidth = w
		self.roomHeight = h
		self.roomShape = s

		self.setSceneRect(-52, -52, self.roomWidth * 26 + 52 * 2, self.roomHeight * 26 + 52 * 2)

	def clearDoors(self):
		for item in self.items():
			if isinstance(item, Door):
				item.remove()

	def drawForeground(self, painter, rect):

		# Bitfont drawing: moved to the RoomEditorWidget.drawForeground for easier anti-aliasing

		# Grey out the screen to show it's inactive if there are no rooms selected
		if mainWindow.roomList.selectedRoom() == None:
			painter.setPen(QPen(Qt.white, 1, Qt.SolidLine))
			painter.setBrush(QBrush(QColor(100, 100, 100, 100)))

			b = QBrush(QColor(100, 100, 100, 100))
			painter.fillRect(rect, b)
			return

		# Draw me a foreground grid
		if not self.grid: return

		painter.setRenderHint(QPainter.Antialiasing, True)
		painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

		rect = QRectF(0, 0, self.roomWidth * 26, self.roomHeight * 26)

		# Modify Rect for slim rooms
		if self.roomShape in [2, 7]:
			rect = QRectF(0, 52, self.roomWidth * 26, self.roomHeight * 26)

		if self.roomShape in [3, 5]:
			rect = QRectF(104, 0, self.roomWidth * 26, self.roomHeight * 26)

		# Actual drawing code
		ts = 26

		startx = rect.x()
		endx = startx + rect.width()

		starty = rect.y()
		endy = starty + rect.height()

		painter.setPen(QPen(QColor.fromRgb(255, 255, 255, 100), 1, Qt.DashLine))

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

	def loadBackground(self):

		roomBG = 1

		if mainWindow.roomList.selectedRoom():
			roomBG = mainWindow.roomList.selectedRoom().roomBG

		self.tile = QImage()
		self.tile.load('resources/Backgrounds/{0}.png'.format(self.BG[roomBG-1]))

		self.corner = self.tile.copy(QRect(0,      0,      26 * 7, 26 * 4))
		self.vert   = self.tile.copy(QRect(26 * 7, 0,      26 * 2, 26 * 6))
		self.horiz  = self.tile.copy(QRect(0,      26 * 4, 26 * 9, 26 * 2))

		# I'll need to do something here for the other corner
		self.innerCorner = QImage()
		self.innerCorner.load('resources/Backgrounds/{0}Inner.png'.format(self.BG[roomBG - 1]))

	def drawBackground(self, painter, rect):

		self.loadBackground()

		########## SHAPE DEFINITIONS
		# w x h
		# 1 = 1x1, 2 = 1x0.5, 3 = 0.5x1, 4 = 2x1, 5 = 2x0.5, 6 = 1x2, 7 = 0.5x2, 8 = 2x2
		# 9 = DR corner, 10 = DL corner, 11 = UR corner, 12 = UL corner

		# Regular Rooms
		if self.roomShape in [1, 4, 6, 8]:
			self.drawBGRegularRooms(painter, rect)

		# Slim Rooms
		elif self.roomShape in [2, 3, 5, 7]:
			self.drawBGSlimRooms(painter, rect)

		# L Rooms
		elif self.roomShape in [9, 10, 11, 12]:
			self.drawBGCornerRooms(painter, rect)

		# Uh oh
		else:
			print ("This room is not a known shape. {0} - {1} x {2}".format(self.roomShape, self.roomWidth, self.roomHeight))
			self.drawBGRegularRooms(painter, rect)

	def drawBGRegularRooms(self, painter, rect):
		t = -52
		xm = 26 * (self.roomWidth + 2)  - 26 * 7
		ym = 26 * (self.roomHeight + 2) - 26 * 4

		# Corner Painting
		painter.drawPixmap(t,  t,  QPixmap().fromImage(self.corner.mirrored(False, False)))
		painter.drawPixmap(xm, t,  QPixmap().fromImage(self.corner.mirrored(True, False)))
		painter.drawPixmap(t,  ym, QPixmap().fromImage(self.corner.mirrored(False, True)))
		painter.drawPixmap(xm, ym, QPixmap().fromImage(self.corner.mirrored(True, True)))

		# Mirrored Textures
		uRect = QImage(26 * 4, 26 * 6, QImage.Format_RGB32)
		lRect = QImage(26 * 9, 26 * 4, QImage.Format_RGB32)

		uRect.fill(1)
		lRect.fill(1)

		vp = QPainter()
		vp.begin(uRect)
		vp.drawPixmap(0,  0, QPixmap().fromImage(self.vert))
		vp.drawPixmap(52, 0, QPixmap().fromImage(self.vert.mirrored(True, False)))
		vp.end()

		vh = QPainter()
		vh.begin(lRect)
		vh.drawPixmap(0, 0,  QPixmap().fromImage(self.horiz))
		vh.drawPixmap(0, 52, QPixmap().fromImage(self.horiz.mirrored(False, True)))
		vh.end()

		painter.drawTiledPixmap(
			26 * 7 - 52 - 13,
			-52,
			26 * (self.roomWidth - 10) + 26,
			26 * 6,
			QPixmap().fromImage(uRect)
		)
		painter.drawTiledPixmap(
			-52,
			26 * 4 - 52 - 13,
			26 * 9,
			26 * (self.roomHeight - 4) + 26,
			QPixmap().fromImage(lRect)
		)
		painter.drawTiledPixmap(
			26 * 7 - 52 - 13,
			self.roomHeight * 26 - 26 * 4,
			26 * (self.roomWidth - 10) + 26,
			26 * 6,
			QPixmap().fromImage(uRect.mirrored(False, True))
		)
		painter.drawTiledPixmap(
			self.roomWidth * 26 - 26 * 7,
			26 * 4 - 52 - 13,
			26 * 9,
			26 * (self.roomHeight - 4) + 26,
			QPixmap().fromImage(lRect.mirrored(True, False))
		)

		if self.roomHeight == 14 and self.roomWidth == 26:

			self.center = self.tile.copy(QRect(26 * 3, 26 * 3, 26 * 6, 26 * 3))

			painter.drawPixmap	(26 * 7,  26 * 4, QPixmap().fromImage(self.center.mirrored(False, False)))
			painter.drawPixmap	(26 * 13, 26 * 4, QPixmap().fromImage(self.center.mirrored(True, False)))
			painter.drawPixmap	(26 * 7,  26 * 7, QPixmap().fromImage(self.center.mirrored(False, True)))
			painter.drawPixmap	(26 * 13, 26 * 7, QPixmap().fromImage(self.center.mirrored(True, True)))

	def drawBGSlimRooms(self, painter, rect):

		t = -52
		yo = 0
		xo = 0

		# Thin in Height
		if self.roomShape in [2, 7]:
			self.roomHeight = 3
			yo = (2 * 26)

		# Thin in Width
		if self.roomShape in [3, 5]:
			self.roomWidth = 5
			xo = (4 * 26)

		xm = 26 * (self.roomWidth+2)  - 26 * 7
		ym = 26 * (self.roomHeight+2) - 26 * 4

		# Corner Painting
		painter.drawPixmap(t + xo,  t + yo,  QPixmap().fromImage(self.corner.mirrored(False, False)))
		painter.drawPixmap(xm + xo, t + yo,  QPixmap().fromImage(self.corner.mirrored(True, False)))
		painter.drawPixmap(t + xo,  ym + yo, QPixmap().fromImage(self.corner.mirrored(False, True)))
		painter.drawPixmap(xm + xo, ym + yo, QPixmap().fromImage(self.corner.mirrored(True, True)))

		# Mirrored Textures
		uRect = QImage(26 * 4, 26 * 4, QImage.Format_RGB32)
		lRect = QImage(26 * 7, 26 * 4, QImage.Format_RGB32)

		uRect.fill(1)
		lRect.fill(1)

		vp = QPainter()
		vp.begin(uRect)
		vp.drawPixmap(0,  0, QPixmap().fromImage(self.vert))
		vp.drawPixmap(52, 0, QPixmap().fromImage(self.vert.mirrored(True, False)))
		vp.end()

		vh = QPainter()
		vh.begin(lRect)
		vh.drawPixmap(0, 0,  QPixmap().fromImage(self.horiz))
		vh.drawPixmap(0, 52, QPixmap().fromImage(self.horiz.mirrored(False, True)))
		vh.end()

		painter.drawTiledPixmap(
			xo + 26 * 7 - 52 - 13,
			yo + -52,
			26 * (self.roomWidth - 10) + 26,
			26 * 4,
			QPixmap().fromImage(uRect)
		)
		painter.drawTiledPixmap(
			xo + -52,
			yo + 26 * 4 - 52 -13,
			26 * 7,
			26 * (self.roomHeight - 4) + 26,
			QPixmap().fromImage(lRect)
		)
		painter.drawTiledPixmap(
			xo + 26 * 7 - 52 - 13,
			yo + self.roomHeight * 26 - 26 * 2,
			26 * (self.roomWidth - 10) + 26,
			26 * 4,
			QPixmap().fromImage(uRect.mirrored(False, True))
		)
		painter.drawTiledPixmap(
			xo + self.roomWidth * 26 - 26 * 5,
			yo + 26 * 4 - 52 - 13,
			26 * 7,
			26 * (self.roomHeight - 4) + 26,
			QPixmap().fromImage(lRect.mirrored(True, False))
		)

		if self.roomHeight == 14 and self.roomWidth == 26:

			self.center = self.tile.copy(QRect(26 * 3, 26 * 3, 26 * 6, 26 * 3))

			painter.drawPixmap(xo + 26 * 7,  yo + 26 * 4, QPixmap().fromImage(self.center.mirrored(False, False)))
			painter.drawPixmap(xo + 26 * 13, yo + 26 * 4, QPixmap().fromImage(self.center.mirrored(True, False)))
			painter.drawPixmap(xo + 26 * 7 , yo + 26 * 7, QPixmap().fromImage(self.center.mirrored(False, True)))
			painter.drawPixmap(xo + 26 * 13, yo + 26 * 7, QPixmap().fromImage(self.center.mirrored(True, True)))

	def drawBGCornerRooms(self, painter, rect):
		t = -52
		xm = 26 * (self.roomWidth + 2)  - 26 * 7
		ym = 26 * (self.roomHeight + 2) - 26 * 4

		# Mirrored Textures
		uRect = QImage(26 * 4, 26 * 6, QImage.Format_RGB32)
		lRect = QImage(26 * 9, 26 * 4, QImage.Format_RGB32)

		uRect.fill(1)
		lRect.fill(1)

		vp = QPainter()
		vp.begin(uRect)
		vp.drawPixmap(0,  0, QPixmap().fromImage(self.vert))
		vp.drawPixmap(52, 0, QPixmap().fromImage(self.vert.mirrored(True, False)))
		vp.end()

		vh = QPainter()
		vh.begin(lRect)
		vh.drawPixmap(0, 0,  QPixmap().fromImage(self.horiz))
		vh.drawPixmap(0, 52, QPixmap().fromImage(self.horiz.mirrored(False, True)))
		vh.end()

		# Exterior Corner Painting
		painter.drawPixmap(t,  t,  QPixmap().fromImage(self.corner.mirrored(False, False)))
		painter.drawPixmap(xm, t,  QPixmap().fromImage(self.corner.mirrored(True, False)))
		painter.drawPixmap(t,  ym, QPixmap().fromImage(self.corner.mirrored(False, True)))
		painter.drawPixmap(xm, ym, QPixmap().fromImage(self.corner.mirrored(True, True)))

		# Exterior Wall Painting
		painter.drawTiledPixmap(26 * 7 - 52 - 13, -52, 26 * (self.roomWidth - 10) + 26, 26 * 6, QPixmap().fromImage(uRect))
		painter.drawTiledPixmap(-52, 26 * 4 - 52 - 13, 26 * 9, 26 * (self.roomHeight - 4) + 26, QPixmap().fromImage(lRect))
		painter.drawTiledPixmap(26 * 7 - 52 - 13, self.roomHeight * 26 - 26 * 4, 26 * (self.roomWidth - 10) + 26, 26 * 6, QPixmap().fromImage(uRect.mirrored(False, True)))
		painter.drawTiledPixmap(self.roomWidth * 26 - 26 * 7, 26 * 4 - 52 - 13, 26 * 9, 26 * (self.roomHeight - 4) + 26, QPixmap().fromImage(lRect.mirrored(True, False)))

		# Center Floor Painting
		self.center = self.tile.copy(QRect(26 * 3, 26 * 3, 26 * 6, 26 * 3))

		painter.drawPixmap(26 * 7,  26 * 4, QPixmap().fromImage(self.center.mirrored(False, False)))
		painter.drawPixmap(26 * 13, 26 * 4, QPixmap().fromImage(self.center.mirrored(True, False)))
		painter.drawPixmap(26 * 7,  26 * 7, QPixmap().fromImage(self.center.mirrored(False, True)))
		painter.drawPixmap(26 * 13, 26 * 7, QPixmap().fromImage(self.center.mirrored(True, True)))

		# Interior Corner Painting (This is the annoying bit)
		# New midpoints
		xm = 26 * (self.roomWidth / 2)
		ym = 26 * (self.roomHeight / 2)

		# New half-lengths/heights
		xl = 26 * (self.roomWidth + 4) / 2
		yl = 26 * (self.roomHeight + 4) / 2


		if self.roomShape == 9:
			# Clear the dead area
			painter.fillRect(t, t, xl, yl, QColor(0, 0, 0, 255))

			# Draw the horizontal wall
			painter.drawTiledPixmap(xm - 26 * 8, ym + t, 26 * 6, 26 * 6, QPixmap().fromImage(uRect))

			# Draw the vertical wall
			painter.drawTiledPixmap(xm + t, ym - 26 * 5, 26 * 9, 26 * 3, QPixmap().fromImage(lRect))

			# Draw the three remaining corners
			painter.drawPixmap(t,      ym + t, QPixmap().fromImage(self.corner.mirrored(False, False)))
			painter.drawPixmap(xm + t, t,      QPixmap().fromImage(self.corner.mirrored(False, False)))
			painter.drawPixmap(xm + t, ym + t, QPixmap().fromImage(self.innerCorner.mirrored(False, False)))

		elif self.roomShape == 10:
			# Clear the dead area
			painter.fillRect(xm, t , xl, yl, QColor(0, 0, 0, 255))

			# Draw the horizontal wall
			painter.drawTiledPixmap(xm - t, ym + t, 26 * 6, 26 * 6, QPixmap().fromImage(uRect))

			# Draw the vertical wall
			painter.drawTiledPixmap(xm - 26 * 7, ym - 26 * 5, 26 * 9, 26 * 3, QPixmap().fromImage(lRect.mirrored(True, False)))

			# Draw the three remaining corners
			painter.drawPixmap(26 * (self.roomWidth + 2) - 26 * 7, ym + t, QPixmap().fromImage(self.corner.mirrored(True, False)))
			painter.drawPixmap(xm - 26 * 5, t, QPixmap().fromImage(self.corner.mirrored(True, False)))
			painter.drawPixmap(xm, ym + t, QPixmap().fromImage(self.innerCorner.mirrored(True, False)))

		elif self.roomShape == 11:
			# Clear the dead area
			painter.fillRect(t, ym, xl, yl, QColor(0, 0, 0, 255))

			# Draw the horizontal wall
			painter.drawTiledPixmap(xm - 26 * 8, ym + t * 2, 26 * 6, 26 * 6, QPixmap().fromImage(uRect.mirrored(False, True)))

			# Draw the vertical wall
			painter.drawTiledPixmap(xm + t, ym - t, 26 * 9, 26 * 3, QPixmap().fromImage(lRect))

			# Draw the three remaining corners
			painter.drawPixmap(t,      ym + t,     QPixmap().fromImage(self.corner.mirrored(False, True)))
			painter.drawPixmap(xm + t, ym * 2 + t, QPixmap().fromImage(self.corner.mirrored(False, True)))
			painter.drawPixmap(xm + t, ym,         QPixmap().fromImage(self.innerCorner.mirrored(False, True)))

		elif self.roomShape == 12:
			# Clear the dead area
			painter.fillRect(xm, ym, xl, yl, QColor(0, 0, 0, 255))

			# Draw the horizontal wall
			painter.drawTiledPixmap(xm + 26 * 2, ym + t * 2, 26 * 6, 26 * 6, QPixmap().fromImage(uRect.mirrored(False, True)))

			# Draw the vertical wall
			painter.drawTiledPixmap(xm - 26 * 7, ym - t, 26 * 9, 26 * 3, QPixmap().fromImage(lRect.mirrored(True, False)))

			# Draw the three remaining corners
			painter.drawPixmap(xm + 26 * 8, ym + t,      QPixmap().fromImage(self.corner.mirrored(True, True)))
			painter.drawPixmap(xm - 26 * 5, ym + 26 * 5, QPixmap().fromImage(self.corner.mirrored(True, True)))
			painter.drawPixmap(xm,          ym,          QPixmap().fromImage(self.innerCorner.mirrored(True, True)))

class RoomEditorWidget(QGraphicsView):

	def __init__(self, scene, parent=None):
		QGraphicsView.__init__(self, scene, parent)

		self.setViewportUpdateMode(self.FullViewportUpdate)
		self.setDragMode(self.RubberBandDrag)
		self.setTransformationAnchor(QGraphicsView.AnchorViewCenter)
		self.setAlignment(Qt.AlignTop | Qt.AlignLeft)
		self.newScale = 1.0

		self.assignNewScene(scene)

		self.statusBar = True
		self.canDelete = True

	def assignNewScene(self, scene):
		self.setScene(scene)
		self.centerOn(0, 0)

		self.objectToPaint = None
		self.lastTile = None

	def tryToPaint(self, event):
		'''Called when a paint attempt is initiated'''

		paint = self.objectToPaint
		if paint == None: return

		clicked = self.mapToScene(event.x(), event.y())
		x, y = clicked.x(), clicked.y()
		if x > self.scene().roomWidth  * 26: x = (self.scene().roomWidth-1)  * 26
		if y > self.scene().roomHeight * 26: y = (self.scene().roomHeight-1) * 26

		if x < 0: x = 0
		if y < 0: y = 0

		x = int(x / 26)
		y = int(y / 26)

		# Don't stack multiple grid entities
		for i in self.scene().items():
			if isinstance(i, Entity):
				if i.entity['X'] == x and i.entity['Y'] == y:
					
					i.removeWeightPopup(True)

					if int(i.entity['Type']) > 999 and int(self.objectToPaint.ID) > 999:
						return

		# Make sure we're not spawning oodles
		if (x, y) in self.lastTile: return
		self.lastTile.add((x, y))

		en = Entity(x, y, int(paint.ID), int(paint.variant), int(paint.subtype), 1.0)

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
		if (event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace) and self.canDelete:
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

		QGraphicsView.drawBackground(self, painter, rect)

	def resizeEvent(self, event):
		QGraphicsView.resizeEvent(self, event)

		w = self.scene().roomWidth
		h = self.scene().roomHeight

		xScale = event.size().width()  / (w * 26 + 52 * 2)
		yScale = event.size().height() / (h * 26 + 52 * 2)
		newScale = min([xScale, yScale])

		tr = QTransform()
		tr.scale(newScale, newScale)
		self.newScale = newScale

		self.setTransform(tr)

		if newScale == yScale:
			self.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
		else:
			self.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

	def paintEvent(self, event):
		# Purely handles the status overlay text
		QGraphicsView.paintEvent(self, event)

		if not self.statusBar: return

		# Display the room status in a text overlay
		painter = QPainter()
		painter.begin(self.viewport())

		painter.setRenderHint(QPainter.Antialiasing, True)
		painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
		painter.setPen(QPen(Qt.white, 1, Qt.SolidLine))

		room = mainWindow.roomList.selectedRoom()
		if room:
			# Room Type Icon
			q = QPixmap()
			q.load('resources/UI/RoomIcons.png')

			painter.drawPixmap(2, 3, q.copy(room.roomType * 16, 0, 16, 16))

			# Top Text
			font = painter.font()
			font.setPixelSize(13)
			painter.setFont(font)
			painter.drawText(20, 16, "{0} - {1}".format(room.roomVariant, room.data(0x100)) )

			# Bottom Text
			font = painter.font()
			font.setPixelSize(10)
			painter.setFont(font)
			painter.drawText(8, 30, "Difficulty: {1}, Weight: {2}, Subvariant: {0}".format(room.roomSubvariant, room.roomDifficulty, room.roomWeight))

		# Display the currently selected entity in a text overlay
		selectedEntities = self.scene().selectedItems()

		if len(selectedEntities) == 1:
			e = selectedEntities[0]
			r = event.rect()

			# Entity Icon
			i = QIcon()
			painter.drawPixmap(QRect(r.right() - 32, 2, 32, 32), e.entity["pixmap"])

			# Top Text
			font = painter.font()
			font.setPixelSize(13)
			painter.setFont(font)
			painter.drawText(r.right() - 34 - 200, 2, 200, 16, Qt.AlignRight | Qt.AlignBottom, "{1}.{2}.{3} - {0}".format(e.entity["name"], e.entity["Type"], e.entity["Variant"], e.entity["Subtype"]) )

			# Bottom Text
			font = painter.font()
			font.setPixelSize(10)
			painter.setFont(font)
			painter.drawText(r.right() - 34 - 200, 20, 200, 12, Qt.AlignRight | Qt.AlignBottom, "Base HP : {0}".format(e.entity["baseHP"]) )

		elif len(selectedEntities) > 1:
			e = selectedEntities[0]
			r = event.rect()

			# Case Two: more than one type of entity
			# Entity Icon
			i = QIcon()
			painter.drawPixmap(QRect(r.right() - 32, 2, 32, 32), e.entity["pixmap"])

			# Top Text
			font = painter.font()
			font.setPixelSize(13)
			painter.setFont(font)
			painter.drawText(r.right() - 34 - 200, 2, 200, 16, Qt.AlignRight | Qt.AlignBottom, "{0} Entities Selected".format(len(selectedEntities)) )

			# Bottom Text
			font = painter.font()
			font.setPixelSize(10)
			painter.setFont(font)
			painter.drawText(r.right() - 34 - 200, 20, 200, 12, Qt.AlignRight | Qt.AlignBottom, ", ".join(set([x.entity['name'] for x in selectedEntities])) )

			pass

		painter.end()

	def drawForeground(self, painter, rect):
		QGraphicsView.drawForeground(self, painter, rect)

		painter.setRenderHint(QPainter.Antialiasing, True)
		painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

		# Display the number of entities on a given tile, in bitFont or regular font
		tiles = [[0 for y in range(26)] for x in range(14)]
		for e in self.scene().items():
			if isinstance(e, Entity):
				tiles[e.entity['Y']][e.entity['X']] += 1

		if not self.scene().bitText:
			painter.setPen(QPen(Qt.white, 1, Qt.SolidLine))
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

		self.popup = None
		mainWindow.scene.selectionChanged.connect(self.removeWeightPopup)

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
		self.entity['known'] = False

		self.getEntityInfo(mytype, subtype, variant)

		self.updatePosition()
		if self.entity['Type'] < 999:
			self.setZValue(1)
		else:
			self.setZValue(0)

		if not hasattr(Entity, 'SELECTION_PEN'):
			Entity.SELECTION_PEN = QPen(Qt.green, 1, Qt.DashLine)

		self.setToolTip("{name} @ {X} x {Y} - {Type}.{Variant}.{Subtype}; HP: {baseHP}".format(**self.entity))
		self.setAcceptHoverEvents(True)

	def getEntityInfo(self, t, subtype, variant):

		# Try catch so I can not crash BR so often
		try:
			global entityXML
			en = entityXML.find("entity[@ID='{0}'][@Subtype='{1}'][@Variant='{2}']".format(t, subtype, variant))

			self.entity['name'] = en.get('Name')
			self.entity['baseHP'] = en.get('BaseHP')
			self.entity['boss'] = en.get('Boss')
			self.entity['champion'] = en.get('Champion')

			if self.entity['Type'] == 5 and self.entity['Variant'] == 100:
				i = QImage()
				i.load('resources/Entities/5.100.0 - Collectible.png')
				i = i.convertToFormat(QImage.Format_ARGB32)

				d = QImage()
				d.load(en.get('Image'))

				p = QPainter(i)
				p.drawImage(0, 0, d)
				p.end()

				self.entity['pixmap'] = QPixmap.fromImage(i)

			else:
				self.entity['pixmap'] = QPixmap()
				self.entity['pixmap'].load(en.get('Image'))

			self.entity['known'] = True

		except:
			print ("Entity {0}, Subtype {1}, Variant {2} expected, but was not found".format(t, subtype, variant))
			self.entity['pixmap'] = QPixmap()
			self.entity['pixmap'].load("resources/Entities/questionmark.png")

	def itemChange(self, change, value):

		if change == self.ItemPositionChange:
			self.removeWeightPopup(True)

			currentX, currentY = self.x(), self.y()

			x, y = value.x(), value.y()

			# Debug code
			# if 'eep' in self.entity['name']:
			# 	print (self.entity['X'], self.entity['Y'], x, y)

			try:
				w = self.scene().initialRoomWidth
				h = self.scene().initialRoomHeight
			except:
				w = 26
				h = 14

			x = int((x + (self.SNAP_TO / 2)) / self.SNAP_TO) * self.SNAP_TO
			y = int((y + (self.SNAP_TO / 2)) / self.SNAP_TO) * self.SNAP_TO

			if x < 0: x = 0
			if x >= (self.SNAP_TO * (w - 1)): x = (self.SNAP_TO * (w - 1))
			if y < 0: y = 0
			if y >= (self.SNAP_TO * (h - 1)): y = (self.SNAP_TO * (h - 1))

			if x != currentX or y != currentY:
				self.entity['X'] = int(x / self.SNAP_TO)
				self.entity['Y'] = int(y / self.SNAP_TO)
				if self.isSelected():
					mainWindow.dirt()

			value.setX(x)
			value.setY(y)

			# Debug code
			# if 'eep' in self.entity['name']:
			# 	print (self.entity['X'], self.entity['Y'], x, y)

			return value

		return QGraphicsItem.itemChange(self, change, value)

	def boundingRect(self):

		#if self.entity['pixmap']:
		#	return QRectF(self.entity['pixmap'].rect())
		#else:
		return QRectF(0.0, 0.0, 26.0, 26.0)

	def updatePosition(self):
		self.setPos(self.entity['X'] * 26, self.entity['Y'] * 26)

	def paint(self, painter, option, widget):

		painter.setRenderHint(QPainter.Antialiasing, True)
		painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

		painter.setBrush(Qt.Dense5Pattern)
		painter.setPen(QPen(Qt.white))

		if self.entity['pixmap']:
			x = -(self.entity['pixmap'].width() -26) / 2

			# Centering code
			zamiellLovesMakingMyCodeDirty = [44, 236, 218]
			if self.entity['Type'] in zamiellLovesMakingMyCodeDirty or \
			  (self.entity['Type'] == 5 and self.entity['Variant'] == 380) or \
			  (self.entity['Type'] == 291 and self.entity['Variant'] == 1) or \
			  (self.entity['Type'] == 291 and self.entity['Variant'] == 3):

				y = -(self.entity['pixmap'].height() - 26) / 2
			else:
				y = -(self.entity['pixmap'].height() - 26)

			# Curse room special case
			if self.entity['Type'] == 5 and self.entity['Variant'] == 50 and mainWindow.roomList.selectedRoom().roomType == 10:
				self.entity['pixmap'] = QPixmap()
				self.entity['pixmap'].load('resources/Entities/5.360.0 - Red Chest.png')

			# Creeper special case
			if self.entity['Type'] in [240, 241, 242]:
				w = self.scene().roomWidth -1
				h = self.scene().roomHeight - 1
				ex = self.entity['X']
				ey = self.entity['Y']

				distances = [w - ex, ex, ey, h - ey]
				closest = min(distances)
				direction = distances.index(closest)

				# Wall lines
				painter.setPen(QPen(QColor(220, 220, 180), 2, Qt.DashDotLine))
				painter.setBrush(Qt.NoBrush)

				if direction == 0: # Right
					painter.drawLine(26, 13, closest * 26 + 26, 13)

				elif direction == 1: # Left
					painter.drawLine(0, 13, -closest * 26, 13)

				elif direction == 2: # Top
					painter.drawLine(13, 0, 13, -closest * 26)

				elif direction == 3: # Bottom
					painter.drawLine(13, 26, 13, closest * 26 + 26)

				painter.drawPixmap(x, y, self.entity['pixmap'])

			# Most Painting
			else:
				painter.drawPixmap(x, y, self.entity['pixmap'])

			if self.isSelected():
				painter.setPen(self.SELECTION_PEN)
				painter.setBrush(Qt.NoBrush)
				painter.drawRect(x, y, self.entity['pixmap'].width(), self.entity['pixmap'].height())

				# Grid space boundary
				painter.setPen(Qt.green)
				painter.drawLine(0, 0, 0, 4)
				painter.drawLine(0, 0, 4, 0)

				painter.drawLine(26, 0, 26, 4)
				painter.drawLine(26, 0, 22, 0)

				painter.drawLine(0, 26, 4, 26)
				painter.drawLine(0, 26, 0, 22)

				painter.drawLine(26, 26, 22, 26)
				painter.drawLine(26, 26, 26, 22)

		if self.entity["known"] == False:
			painter.setFont(QFont("Arial", 6));			

			painter.drawText(2, 26, "{}.{}.{}".format(
				str(self.entity['Type']),
				str(self.entity['Variant']),
				str(self.entity['Subtype'])))

	def remove(self):
		if self.popup:
			self.popup.remove()
		self.scene().removeItem(self)

	def hoverEnterEvent(self, event):
		self.createWeightPopup()

	def hoverLeaveEvent(self, event):
		self.removeWeightPopup()

	def createWeightPopup(self):
		# Get the stack
		stack = self.collidingItems()
		stack.append(self)

		# Make sure there are no doors or popups involved
		stack = [x for x in stack if isinstance(x,Entity)]

		# 1 is not a stack.
		if len(stack) <= 1: return

		# If there's no popu, make a popup
		if self.popup == None:
			popup = EntityStack(stack)
			self.scene().views()[0].canDelete = False
			self.scene().addItem(popup)
			self.popup = popup

	def removeWeightPopup(self, force=False):
		if self in mainWindow.scene.selectedItems() and not force:
			return

		if self.popup:
			self.popup.remove()
			self.popup = None
			self.scene().views()[0].canDelete = True

class EntityStack(QGraphicsItem):

	class WeightSpinner(QDoubleSpinBox):
		def __init__(self):
			QDoubleSpinBox.__init__(self)

			self.setRange(0.0, 100.0)
			self.setDecimals(2)
			self.setSingleStep(0.1)
			self.setFrame(False)
			self.setAlignment(Qt.AlignHCenter)

			self.setFont(QFont("Arial", 10))

			palette = self.palette()
			palette.setColor(QPalette.Base, Qt.transparent)
			palette.setColor(QPalette.Text, Qt.white)
			palette.setColor(QPalette.Window, Qt.transparent)

			self.setPalette(palette)
			self.setButtonSymbols(QAbstractSpinBox.NoButtons)

	class Proxy(QGraphicsProxyWidget):
		def __init__(self, button, parent):
			QGraphicsProxyWidget.__init__(self, parent)

			self.setWidget(button)

	def __init__(self, items):
		QGraphicsItem.__init__(self)
		self.setZValue(1000)

		self.items = items

		self.spinners = []
		
		w = 0
		for item in self.items:
			w += 4
			pix = item.entity['pixmap']
			w += pix.width()

			weight = self.WeightSpinner()
			weight.setValue(item.entity["Weight"])
			weight.valueChanged.connect(self.weightChanged)
			weightProxy = self.Proxy(weight, self)
			self.spinners.append(weightProxy)

	def weightChanged(self):
		for n, spinner in enumerate(self.spinners):
			self.items[n].entity['Weight'] = spinner.widget().value()

	def paint(self, painter, option, widget):
		painter.setRenderHint(QPainter.Antialiasing, True)
		painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

		brush = QBrush(QColor(0,0,0,80))
		painter.setPen(QPen(Qt.transparent))
		painter.setBrush(brush)

		r = self.boundingRect().adjusted(0,0,0,-16)

		path = QPainterPath()
		path.addRoundedRect(r, 4, 4)
		path.moveTo(r.center().x()-6, r.bottom())
		path.lineTo(r.center().x()+6, r.bottom())
		path.lineTo(r.center().x(), r.bottom()+12)
		painter.drawPath(path)

		painter.setPen(QPen(Qt.white))
		painter.setFont(QFont("Arial", 8));
		
		w = 0
		for item in self.items:
			self.spinners[self.items.index(item)].setPos(w-8, r.bottom()-26)
			w += 4
			pix = item.entity['pixmap']
			painter.drawPixmap(w, r.bottom()-20-pix.height(), pix)
			
			# painter.drawText(w, r.bottom()-16, pix.width(), 8, Qt.AlignCenter, "{:.1f}".format(item.entity['Weight']))
			w += pix.width()

	def boundingRect(self):
		width = 0
		height = 0

		# Calculate the combined size
		for item in self.items:
			if item.entity['pixmap']:
				width = width + item.entity['pixmap'].rect().width()
				if item.entity['pixmap'].rect().height() > height:
					height = item.entity['pixmap'].rect().height()
			else:
				width = width + 26
				if 26 > height:
					height = 26

		# Add in buffers
		height = height + 8 + 8 + 8 + 16 # Top, bottom, weight text, and arrow
		width = width + 4 + len(self.items)*4 # Left and right and the middle bits

		self.setX(self.items[-1].x() - width/2 + 13)
		self.setY(self.items[-1].y() - height)

		return QRectF(0.0, 0.0, width, height)

	def remove(self):
		# Fix for the nullptr left by the scene parent of the widget, avoids a segfault from the dangling pointer
		for spin in self.spinners:
			self.scene().removeItem(spin)
			# spin.widget().setParent(None)
			spin.setWidget(None)	# Turns out this function calls the above commented out function
			del spin # Probably useless

		self.scene().removeItem(self)
		del self # Probably useless

class Door(QGraphicsItem):

	def __init__(self, doorItem):
		QGraphicsItem.__init__(self)

		# Supplied entity info
		self.doorItem = doorItem
		self.exists = doorItem[2]

		self.setPos(self.doorItem[0] * 26 - 13, self.doorItem[1] * 26 - 13)

		tr = QTransform()
		if doorItem[0] in [-1, 12]:
			tr.rotate(270)
			self.moveBy(-13, 0)
		elif doorItem[0] in [13, 26]:
			tr.rotate(90)
			self.moveBy(13, 0)
		elif doorItem[1] in [7, 14]:
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
			painter.drawImage(0, 0, self.image)
		else:
			painter.drawImage(0, 0, self.disabledImage)

	def boundingRect(self):
		return QRectF(0.0, 0.0, 64.0, 52.0)

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

	def __init__(self, name="New Room", doors=[], spawns=[], mytype=1, variant=0, subvariant=0, difficulty=1, weight=1.0, width=13, height=7, shape=1):
		"""Initializes the room item."""

		QListWidgetItem.__init__(self)

		# self.setText(name)

		self.setData(0x100, name)
		self.setText("{0} - {1}".format(variant, self.data(0x100)))

		self.roomSpawns = spawns
		self.roomDoors = doors
		self.roomType = mytype
		self.roomVariant = variant
		self.roomSubvariant = subvariant # 0-64, usually 0 except for special rooms
		self.setDifficulty(difficulty)
		self.roomWeight = weight
		self.roomWidth = width
		self.roomHeight = height
		self.roomShape = shape           # w x h -> 1 = 1x1, 2 = 1x0.5, 3 = 0.5x1, 4 = 2x1, 5 = 2x0.5, 6 = 1x2, 7 = 0.5x2, 8 = 2x2, 9 = corner?, 10 = corner?, 11 = corner?, 12 = corner?

		self.roomBG = 1
		self.setRoomBG()

		self.setFlags(self.flags() | Qt.ItemIsEditable)
		self.setToolTip()

		if doors == []: self.makeNewDoors()
		self.renderDisplayIcon()

	def setDifficulty(self, d):
		self.roomDifficulty = d
		self.setForeground(QColor.fromHsvF(1, 1, d / 10, 1))

	def makeNewDoors(self):
		self.roomDoors = []

		########## SHAPE DEFINITIONS
		# w x h
		# 1 = 1x1, 2 = 1x0.5, 3 = 0.5x1, 4 = 2x1, 5 = 2x0.5, 6 = 1x2, 7 = 0.5x2, 8 = 2x2
		# 9 = DR corner, 10 = DL corner, 11 = UR corner, 12 = UL corner

		if self.roomShape == 1:
			self.roomDoors = [[6, -1, True], [-1, 3, True], [13, 3, True], [6, 7, True]]

		elif self.roomShape == 2:
			self.roomDoors = [[-1, 3, True], [13, 3, True]]

		elif self.roomShape == 3:
			self.roomDoors = [[6, -1, True], [6, 7, True]]

		elif self.roomShape == 4:
			self.roomDoors = [[6, -1, True], [13, 3, True], [-1, 3, True], [13, 10, True], [-1, 10, True], [6, 14, True]]

		elif self.roomShape == 5:
			self.roomDoors = [[6, -1, True], [6, 14, True]]

		elif self.roomShape == 6:
			self.roomDoors = [[6, -1, True], [-1, 3, True], [6, 7, True], [19, 7, True], [26, 3, True], [19, -1, True]]

		elif self.roomShape == 7:
			self.roomDoors = [[-1, 3, True], [26, 3, True]]

		elif self.roomShape == 8:
			self.roomDoors = [[6, -1, True], [-1, 3, True], [-1, 10, True], [19, -1, True], [6, 14, True], [19, 14, True], [26, 3, True], [26, 10, True]]

		elif self.roomShape == 9:
			self.roomDoors = [[19, -1, True], [26, 3, True], [6, 14, True], [19, 14, True], [12, 3, True], [-1, 10, True], [26, 10, True], [6, 6, True]]

		elif self.roomShape == 10:
			self.roomDoors = [[-1, 3, True], [13, 3, True], [6, -1, True], [19, 6, True], [6, 14, True], [19, 14, True], [-1, 10, True], [26, 10, True]]

		elif self.roomShape == 11:
			self.roomDoors = [[-1, 3, True], [6, 7, True], [6, -1, True], [12, 10, True], [19, -1, True], [26, 3, True], [19, 14, True], [26, 10, True]]

		elif self.roomShape == 12:
			self.roomDoors = [[-1, 3, True], [6, -1, True], [19, -1, True], [13, 10, True], [26, 3, True], [6, 14, True], [-1, 10, True], [19, 7, True]]

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
		tip = "{4}x{5} - Type: {0}, Variant: {1}, Difficulty: {2}, Weight: {3}, Shape: {6}".format(self.roomType, self.roomVariant, self.roomDifficulty, self.roomWeight, self.roomWidth, self.roomHeight, self.roomShape)
		QListWidgetItem.setToolTip(self, tip)

	def renderDisplayIcon(self):
		"""Renders the mini-icon for display."""

		q = QImage()
		q.load('resources/UI/RoomIcons.png')

		i = QIcon(QPixmap.fromImage(q.copy(self.roomType * 16, 0, 16, 16)))

		self.setIcon(i)

	def setRoomBG(self):
		c = self.roomType

		roomType = ['basement', 'cellar', 'caves', 'catacombs', 'depths', 'necropolis', 'womb', 'utero', 'sheol', 'cathedral', 'chest', 'dark room', 'bluewomb']

		self.roomBG = 1

		for t in roomType:
			if t in mainWindow.path:
				self.roomBG = roomType.index(t) + 1

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

		elif c in [10, 11, 13, 14, 17]:
			self.roomBG = 9
		elif c in [15]:
			self.roomBG = 10
		elif c in [20]:
			self.roomBG = 11
		elif c in [3]:
			self.roomBG = 12

		elif c in [8]:
			if self.roomVariant in [0]:
				self.roomBG = 7
			elif self.roomVariant in [1]:
				self.roomBG = 10
			elif self.roomVariant in [2]:
				self.roomBG = 9
			elif self.roomVariant in [3]:
				self.roomBG = 4
			elif self.roomVariant in [4]:
				self.roomBG = 2
			elif self.roomVariant in [5]:
				self.roomBG = 1
			elif self.roomVariant in [6]:
				self.roomBG = 12
			elif self.roomVariant in [7]:
				self.roomBG = 13
			else:
				self.roomBG = 12

class RoomDelegate(QStyledItemDelegate):

	def __init__(self):

		self.pixmap = QPixmap('resources/UI/CurrentRoom.png')
		QStyledItemDelegate.__init__(self)

	def paint(self, painter, option, index):

		painter.fillRect(option.rect.right() - 19, option.rect.top(), 17, 16, QBrush(Qt.white))

		QStyledItemDelegate.paint(self, painter, option, index)

		item = mainWindow.roomList.list.item(index.row())
		if item:
			if item.data(100):
				painter.drawPixmap(option.rect.right() - 19, option.rect.top(), self.pixmap)

class FilterMenu(QMenu):

	def __init__(self):

		QMenu.__init__(self)

	def paintEvent(self, event):

		QMenu.paintEvent(self, event)

		painter = QPainter(self)

		for act in self.actions():
			rect = self.actionGeometry(act)
			painter.fillRect(rect.right() / 2 - 12, rect.top() - 2, 24, 24, QBrush(Qt.transparent))
			painter.drawPixmap(rect.right() / 2 - 12, rect.top() - 2, act.icon().pixmap(24, 24));

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
		self.filter = QGridLayout()
		self.filter.setSpacing(4)

		fq = QImage()
		fq.load('resources/UI/FilterIcons.png')

		# Set the custom data
		self.filter.typeData = -1
		self.filter.weightData = -1
		self.filter.sizeData = -1

		# ID Filter
		self.IDFilter = QLineEdit()
		self.IDFilter.setPlaceholderText("ID / Name")
		self.IDFilter.textChanged.connect(self.changeFilter)

		# Entity Toggle Button
		self.entityToggle = QToolButton()
		self.entityToggle.setCheckable(True)
		self.entityToggle.checked = False
		self.entityToggle.setIconSize(QSize(24, 24))
		self.entityToggle.toggled.connect(self.setEntityToggle)
		self.entityToggle.toggled.connect(self.changeFilter)
		self.entityToggle.setIcon(QIcon(QPixmap.fromImage(fq.copy(0, 0, 24, 24))))

		# Type Toggle Button
		self.typeToggle = QToolButton()
		self.typeToggle.setIconSize(QSize(24, 24))
		self.typeToggle.setPopupMode(QToolButton.InstantPopup)

		typeMenu = QMenu()

		q = QImage()
		q.load('resources/UI/RoomIcons.png')

		self.typeToggle.setIcon(QIcon(QPixmap.fromImage(fq.copy(1 * 24 + 4, 4, 16, 16))))
		act = typeMenu.addAction(QIcon(QPixmap.fromImage(fq.copy(1 * 24 + 4, 4, 16, 16))), '')
		act.setData(-1)
		self.typeToggle.setDefaultAction(act)

		for i in range(24):
			act = typeMenu.addAction(QIcon(QPixmap.fromImage(q.copy(i * 16, 0, 16, 16))), '')
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

		self.weightToggle.setIcon(QIcon(QPixmap.fromImage(fq.copy(2 * 24, 0, 24, 24))))
		act = weightMenu.addAction(QIcon(QPixmap.fromImage(fq.copy(2 * 24, 0, 24, 24))), '')
		act.setData(-1)
		act.setIconVisibleInMenu(False)
		self.weightToggle.setDefaultAction(act)

		w = [0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 5.0, 1000.0]
		for i in range(9):
			act = weightMenu.addAction(QIcon(QPixmap.fromImage(q.copy(i * 24, 0, 24, 24))), '')
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
		q.load('resources/UI/ShapeIcons.png')

		self.sizeToggle.setIcon(QIcon(QPixmap.fromImage(fq.copy(3 * 24, 0, 24, 24))))
		act = sizeMenu.addAction(QIcon(QPixmap.fromImage(fq.copy(3 * 24, 0, 24, 24))), '')
		act.setData(-1)
		act.setIconVisibleInMenu(False)
		self.sizeToggle.setDefaultAction(act)

		for i in range(12):
			act = sizeMenu.addAction(QIcon(QPixmap.fromImage(q.copy(i * 16, 0, 16, 16))), '')
			act.setData(i + 1)
			act.setIconVisibleInMenu(False)

		self.sizeToggle.triggered.connect(self.setSizeFilter)
		self.sizeToggle.setMenu(sizeMenu)

		# Add to Layout
		self.filter.addWidget(QLabel("Filter by:"), 0, 0)
		self.filter.addWidget(self.IDFilter, 0, 1)
		self.filter.addWidget(self.entityToggle, 0, 2)
		self.filter.addWidget(self.typeToggle, 0, 3)
		self.filter.addWidget(self.weightToggle, 0, 4)
		self.filter.addWidget(self.sizeToggle, 0, 5)
		self.filter.setContentsMargins(4, 0, 0, 4)

		# Filter active notification and clear buttons

		# Palette
		self.clearAll = QToolButton()
		self.clearAll.setIconSize(QSize(24, 0))
		self.clearAll.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
		self.clearAll.clicked.connect(self.clearAllFilter)

		self.clearName = QToolButton()
		self.clearName.setIconSize(QSize(24, 0))
		self.clearName.setSizePolicy(self.IDFilter.sizePolicy())
		self.clearName.clicked.connect(self.clearNameFilter)

		self.clearEntity = QToolButton()
		self.clearEntity.setIconSize(QSize(24, 0))
		self.clearEntity.clicked.connect(self.clearEntityFilter)

		self.clearType = QToolButton()
		self.clearType.setIconSize(QSize(24, 0))
		self.clearType.clicked.connect(self.clearTypeFilter)

		self.clearWeight = QToolButton()
		self.clearWeight.setIconSize(QSize(24, 0))
		self.clearWeight.clicked.connect(self.clearWeightFilter)

		self.clearSize = QToolButton()
		self.clearSize.setIconSize(QSize(24, 0))
		self.clearSize.clicked.connect(self.clearSizeFilter)

		self.filter.addWidget(self.clearAll, 1, 0)
		self.filter.addWidget(self.clearName, 1, 1)
		self.filter.addWidget(self.clearEntity, 1, 2)
		self.filter.addWidget(self.clearType, 1, 3)
		self.filter.addWidget(self.clearWeight, 1, 4)
		self.filter.addWidget(self.clearSize, 1, 5)

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

		self.list.itemDelegate().closeEditor.connect(self.editComplete)

	def setupToolbar(self):
		self.toolbar = QToolBar()

		self.addRoomButton       = self.toolbar.addAction(QIcon(), 'Add', self.addRoom)
		self.removeRoomButton    = self.toolbar.addAction(QIcon(), 'Delete', self.removeRoom)
		self.duplicateRoomButton = self.toolbar.addAction(QIcon(), 'Duplicate', self.duplicateRoom)
		self.exportRoomButton    = self.toolbar.addAction(QIcon(), 'Export...', self.exportRoom)

		# self.IDButton = self.toolbar.addAction(QIcon(), 'ID', self.turnIDsOn)
		# self.IDButton.setCheckable(True)
		# self.IDButton.setChecked(True)

	def activateEdit(self):
		room = self.selectedRoom()
		room.setText(room.data(0x100))
		self.list.editItem(self.selectedRoom())

	def editComplete(self, lineEdit):
		room = self.selectedRoom()
		room.setData(0x100, lineEdit.text())
		room.setText("{0} - {1}".format(room.roomVariant, room.data(0x100)))

	#@pyqtSlot(bool)
	def turnIDsOn(self):
		return

	#@pyqtSlot(QPoint)
	def customContextMenu(self, pos):
		if not self.selectedRoom(): return

		menu = QMenu(self.list)

		# Size Changing Menu
		size = menu.addMenu('Size')

		q = QImage()
		q.load('resources/UI/ShapeIcons.png')

		for sizeName in range(1, 13):
			i = QIcon(QPixmap.fromImage(q.copy((sizeName - 1) * 16, 0, 16, 16)))

			s = size.addAction(i, str(sizeName))
			if self.selectedRoom().roomShape == sizeName:
				s.setCheckable(True)
				s.setChecked(True)

		size.triggered.connect(self.changeSize)

		menu.addSeparator()

		# Type
		Type = QWidgetAction(menu)
		c = QComboBox()

		types= [
			"Null Room", "Normal Room", "Shop", "Error Room", "Treasure Room", "Boss Room",
			"Mini-Boss Room", "Secret Room", "Super Secret Room", "Arcade", "Curse Room", "Challenge Room",
			"Library", "Sacrifice Room", "Devil Room", "Angel Room", "Item Dungeon", "Boss Rush Room",
			"Isaac's Room", "Barren Room", "Chest Room", "Dice Room", "Black Market", "Greed Mode Descent"
		]

		#if "00." not in mainWindow.path:
		#	types=["Null Room", "Normal Room"]

		q = QImage()
		q.load('resources/UI/RoomIcons.png')

		for i, t in enumerate(types):
			c.addItem(QIcon(QPixmap.fromImage(q.copy(i * 16, 0, 16, 16))), t)
		c.setCurrentIndex(self.selectedRoom().roomType)
		c.currentIndexChanged.connect(self.changeType)
		Type.setDefaultWidget(c)
		menu.addAction(Type)

		# Difficulty
		diff = menu.addMenu('Difficulty')

		for d in [0, 1, 2, 5, 10]:
			m = diff.addAction('{0}'.format(d))

			if self.selectedRoom().roomDifficulty == d:
				m.setCheckable(True)
				m.setChecked(True)

		diff.triggered.connect(self.changeDifficulty)

		# Weight
		weight = menu.addMenu('Weight')

		for w in [0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 5.0, 1000.0]:
			m = weight.addAction('{0}'.format(w))

			if self.selectedRoom().roomWeight == w:
				m.setCheckable(True)
				m.setChecked(True)

		weight.triggered.connect(self.changeWeight)

		menu.addSeparator()

		# Variant
		Variant = QWidgetAction(menu)
		s = QSpinBox()
		s.setRange(0, 65534)
		s.setPrefix("ID -  ")

		s.setValue(self.selectedRoom().roomVariant)

		Variant.setDefaultWidget(s)
		s.valueChanged.connect(self.changeVariant)
		menu.addAction(Variant)

		# SubVariant
		Subvariant = QWidgetAction(menu)
		sv = QSpinBox()
		sv.setRange(0, 256)
		sv.setPrefix("Sub - ")

		sv.setValue(self.selectedRoom().roomSubvariant)

		Subvariant.setDefaultWidget(sv)
		sv.valueChanged.connect(self.changeSubvariant)
		menu.addAction(Subvariant)

		# End it
		menu.exec_(self.list.mapToGlobal(pos))

	#@pyqtSlot(bool)
	def clearAllFilter(self):
		self.IDFilter.clear()
		self.entityToggle.setChecked(False)
		self.filter.typeData = -1
		self.typeToggle.setIcon(self.typeToggle.defaultAction().icon())
		self.filter.weightData = -1
		self.weightToggle.setIcon(self.weightToggle.defaultAction().icon())
		self.filter.sizeData = -1
		self.sizeToggle.setIcon(self.sizeToggle.defaultAction().icon())
		self.changeFilter()

	def clearNameFilter(self):
		self.IDFilter.clear()
		self.changeFilter()

	def clearEntityFilter(self):
		self.entityToggle.setChecked(False)
		self.changeFilter()

	def clearTypeFilter(self):
		self.filter.typeData = -1
		self.typeToggle.setIcon(self.typeToggle.defaultAction().icon())
		self.changeFilter()

	def clearWeightFilter(self):
		self.filter.weightData = -1
		self.weightToggle.setIcon(self.weightToggle.defaultAction().icon())
		self.changeFilter()

	def clearSizeFilter(self):
		self.filter.sizeData = -1
		self.sizeToggle.setIcon(self.sizeToggle.defaultAction().icon())
		self.changeFilter()

	#@pyqtSlot(bool)
	def setEntityToggle(self, checked):
		self.entityToggle.checked = checked

	#@pyqtSlot(QAction)
	def setTypeFilter(self, action):
		self.filter.typeData = action.data()
		self.typeToggle.setIcon(action.icon())
		self.changeFilter()

	#@pyqtSlot(QAction)
	def setWeightFilter(self, action):
		self.filter.weightData = action.data()
		self.weightToggle.setIcon(action.icon())
		self.changeFilter()

	#@pyqtSlot(QAction)
	def setSizeFilter(self, action):
		self.filter.sizeData = action.data()
		self.sizeToggle.setIcon(action.icon())
		self.changeFilter()

	def colourizeClearFilterButtons(self):
		colour = "background-color: #F00;"

		all = False

		# Name Button
		if len(self.IDFilter.text()) > 0:
			self.clearName.setStyleSheet(colour)
			all = True
		else:
			self.clearName.setStyleSheet("")

		# Entity Button
		if self.entityToggle.checked:
			self.clearEntity.setStyleSheet(colour)
			all = True
		else:
			self.clearEntity.setStyleSheet("")

		# Type Button
		if self.filter.typeData is not -1:
			self.clearType.setStyleSheet(colour)
			all = True
		else:
			self.clearType.setStyleSheet("")

		# Weight Button
		if self.filter.weightData is not -1:
			self.clearWeight.setStyleSheet(colour)
			all = True
		else:
			self.clearWeight.setStyleSheet("")

		# Size Button
		if self.filter.sizeData is not -1:
			self.clearSize.setStyleSheet(colour)
			all = True
		else:
			self.clearSize.setStyleSheet("")

		# All Button
		if all:
			self.clearAll.setStyleSheet(colour)
		else:
			self.clearAll.setStyleSheet("")

	#@pyqtSlot()
	def changeFilter(self):
		self.colourizeClearFilterButtons()

		# Here we go
		for room in self.getRooms():
			IDCond = entityCond = typeCond = weightCond = sizeCond = True

			if self.IDFilter.text().lower() not in room.text().lower():
				IDCond = False

			# Check if the right entity is in the room
			if self.entityToggle.checked and self.filterEntity:
				entityCond = False

				for x in room.roomSpawns:
					for y in x:
						for e in y:
							if int(self.filterEntity.ID) == e[0] and int(self.filterEntity.subtype) == e[2] and int(self.filterEntity.variant) == e[1]:
								entityCond = True

			# Check if the room is the right type
			if self.filter.typeData is not -1:
				if self.filter.typeData == 0: # This is a null room, but we'll look for empty rooms too
					typeCond = (self.filter.typeData == room.roomType) or (len(room.roomSpawns) == 0)

					uselessEntities = [0, 1, 2, 1940]
					hasUsefulEntities = False
					for y in enumerate(room.roomSpawns):
						for x in enumerate(y[1]):
							for entity in x[1]:
								if entity[0] not in uselessEntities:
									hasUsefulEntities = True

					if typeCond == False and hasUsefulEntities == False:
						typeCond = True

				else: # All the normal rooms
					typeCond = self.filter.typeData == room.roomType

			# Check if the room is the right weight
			if self.filter.weightData is not -1:
				weightCond = self.filter.weightData == room.roomWeight

			# Check if the room is the right size
			if self.filter.sizeData is not -1:
				sizeCond = False

				shape = self.filter.sizeData

				if room.roomShape == shape:
					sizeCond = True

			# Filter em' out
			if IDCond and entityCond and typeCond and weightCond and sizeCond:
				room.setHidden(False)
			else:
				room.setHidden(True)

	def setEntityFilter(self, entity):
		self.filterEntity = entity
		self.entityToggle.setIcon(entity.icon)
		self.changeFilter()

	#@pyqtSlot(QAction)
	def changeSize(self, action):

		# Set the Size - gotta lotta shit to do here
		s = int(action.text())

		w = 26
		if s in [1, 2, 3, 4, 5]:
			w = 13

		h = 14
		if s in [1, 2, 3, 6, 7]:
			h = 7

		# No sense in doing work we don't have to!
		if self.selectedRoom().roomWidth == w and self.selectedRoom().roomHeight == h and self.selectedRoom().roomShape == s:
			return

		# Check to see if resizing will destroy any entities
		warn = False
		mainWindow.storeEntityList()

		for y in enumerate(self.selectedRoom().roomSpawns):
			for x in enumerate(y[1]):
				for entity in x[1]:

					if x[0] >= w or y[0] >= h:
						warn = True

		if warn:
			msgBox = QMessageBox(
				QMessageBox.Warning,
				"Resize Room?", "Resizing this room will delete entities placed outside the new size. Are you sure you want to resize this room?",
				QMessageBox.NoButton,
				self
			)
			msgBox.addButton("Resize", QMessageBox.AcceptRole)
			msgBox.addButton("Cancel", QMessageBox.RejectRole)
			if msgBox.exec_() == QMessageBox.RejectRole:
				# It's time for us to go now.
				return

		# Clear the room and reset the size
		mainWindow.scene.clear()
		self.selectedRoom().roomWidth = w
		self.selectedRoom().roomHeight = h
		self.selectedRoom().roomShape = s

		self.selectedRoom().makeNewDoors()
		self.selectedRoom().clearDoors()
		mainWindow.scene.newRoomSize(w, h, s)

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

	#@pyqtSlot(int)
	def changeType(self, rtype):
		for r in self.selectedRooms():
			r.roomType = rtype
			r.renderDisplayIcon()
			r.setRoomBG()

			r.setToolTip()

		mainWindow.scene.update()
		mainWindow.dirt()

	#@pyqtSlot(int)
	def changeVariant(self, var):
		for r in self.selectedRooms():
			r.roomVariant = var
			r.setToolTip()
			r.setText("{0} - {1}".format(r.roomVariant, r.data(0x100)))
		mainWindow.dirt()
		mainWindow.scene.update()

	#@pyqtSlot(int)
	def changeSubvariant(self, var):
		for r in self.selectedRooms():
			r.roomSubvariant = var
			r.setToolTip()
		mainWindow.dirt()
		mainWindow.scene.update()

	#@pyqtSlot(QAction)
	def changeDifficulty(self, action):
		for r in self.selectedRooms():
		#self.selectedRoom().roomDifficulty = int(action.text())
			r.setDifficulty(int(action.text()))
			r.setToolTip()
		mainWindow.dirt()
		mainWindow.scene.update()

	#@pyqtSlot(QAction)
	def changeWeight(self, action):
		for r in self.selectedRooms():
			r.roomWeight = float(action.text())
			r.setToolTip()
		mainWindow.dirt()
		mainWindow.scene.update()

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
		if rooms == None or len(rooms) == 0:
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
				self.list.takeItem(self.list.row(item))

			self.list.scrollToItem(self.list.currentItem())
			self.list.setCurrentItem(self.list.currentItem(), QItemSelectionModel.Select)
			mainWindow.dirt()

	def duplicateRoom(self):
		"""Duplicates the selected room"""

		rooms = self.selectedRooms()
		if rooms == None or len(rooms) == 0:
			return

		mainWindow.storeEntityList()

		rv = rooms[0].roomVariant
		v = 0

		initialPlace = self.list.currentRow()
		self.selectedRoom().setData(100, False)
		self.list.setCurrentItem(None, QItemSelectionModel.ClearAndSelect)

		for room in rooms:
			v += 1

			r = Room(
				room.data(0x100) + ' (copy)',
				[list(door) for door in room.roomDoors],
				room.roomSpawns,
				room.roomType,
				v + rv,
				room.roomSubvariant,
				room.roomDifficulty,
				room.roomWeight,
				room.roomWidth,
				room.roomHeight,
				room.roomShape
			)

			self.list.insertItem(initialPlace + v, r)
			self.list.setCurrentItem(r, QItemSelectionModel.Select)

		mainWindow.dirt()

	def exportRoom(self):

		# Get a new
		dialogDir = '' if mainWindow.path == '' else os.path.dirname(mainWindow.path)
		target = QFileDialog.getSaveFileName(self, 'Select a new name or an existing STB', dialogDir, 'Stage Bundle (*.stb)', '', QFileDialog.DontConfirmOverwrite)
		mainWindow.restoreEditMenu()

		if len(target) == 0:
			return

		path = target[0]

		# Append these rooms onto the new STB
		if os.path.exists(path):
			rooms = self.selectedRooms()
			oldRooms = mainWindow.open(path)

			oldRooms.extend(rooms)

			mainWindow.save(oldRooms, path)

		# Make a new STB with the selected rooms
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

class EntityItem(QStandardItem):
	"""A single entity, pretty much just an icon and a few params."""

	def __init__(self, name, ID, subtype, variant, iconPath):
		QStandardItem.__init__(self)

		self.name = name
		self.ID = ID
		self.subtype = subtype
		self.variant = variant
		self.icon = QIcon(iconPath)

		self.setToolTip(name)

class EntityGroupModel(QAbstractListModel):
	"""Model containing all the grouped objects in a tileset"""

	def __init__(self, kind):
		self.groups = {}
		self.kind = kind
		self.view = None

		self.filter = ""

		QAbstractListModel.__init__(self)

		global entityXML
		enList = entityXML.findall("entity")

		for en in enList:
			g = en.get('Group')
			k = en.get('Kind')

			if self.kind == k or self.kind == None:
				if g not in self.groups.keys() and g != None:
					self.groups[g] = EntityGroupItem(g)

				e = EntityItem(en.get('Name'), en.get('ID'), en.get('Subtype'), en.get('Variant'), en.get('Image'))

				if g != None:
					self.groups[g].objects.append(e)

		# Special case for mods
		if self.kind == "Mods" or self.kind == None:
			self.addMods()

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

		elif role == Qt.ForegroundRole:
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

	def addMods(self):

		global entityXML

		# Each mod in the mod folder is a Group
		modsPath = findModsPath()

		modsInstalled = os.listdir(modsPath)

		for mod in modsInstalled:
			modPath = os.path.join(modsPath, mod)

			# Make sure we're a mod
			if not os.path.isdir(modPath):
				continue

			# Get the mod name
			tree = ET.parse(os.path.join(modPath, 'metadata.xml'))
			root = tree.getroot()
			name = root.find("name").text


			# Continue if there are no entities
			if not os.path.exists(os.path.join(modPath, 'content/entities2.xml')):
				continue

			# Grab their Entities2.xml
			tree = ET.parse(os.path.join(modPath, 'content/entities2.xml'))
			root = tree.getroot()
			anm2root = root.get("anm2root")

			# Iterate through all the entities
			enList = root.findall("entity")

			# Skip if the mod is empty
			if len(enList) == 0:
				continue

			# Add a group if it's a new mod, handles duplicate mods as well
			if name not in self.groups.keys():
				self.groups[name] = EntityGroupItem(name)

			for en in enList:
				# Get the Pixmap
				pixmap = QPixmap()

				# Grab the anm location
				anmPath = linuxPathSensitivityTraining(os.path.join(modPath, "resources", anm2root, en.get("anm2path")))

				# Grab the first frame of the anm
				anmTree = ET.parse(anmPath)
				spritesheets = anmTree.findall(".Content/Spritesheets/Spritesheet")
				default = anmTree.find("Animations").get("DefaultAnimation")
				layer = anmTree.find("./Animations/Animation[@Name='{0}']".format(default)).find(".//LayerAnimation")
				frame = layer.find("Frame")

				# Here's the anm specs
				x = int(frame.get("XCrop"))
				y = int(frame.get("YCrop"))
				h = int(frame.get("Height"))
				w = int(frame.get("Width"))
				image = os.path.join(modPath, "resources", anm2root, spritesheets[int(layer.get("LayerId"))].get("Path"))

				# Load the Image
				sourceImage = QImage()
				sourceImage.fill(0)
				sourceImage.load(linuxPathSensitivityTraining(image), 'Format_ARGB32')

				# Create the destination
				pixmapImg = QImage(w, h, QImage.Format_ARGB32)
				pixmapImg.fill(0)

				# Transfer the crop area to the pixmap
				cropRect = QRect(x, y, w, h)

				RenderPainter = QPainter(pixmapImg)
				RenderPainter.drawImage(0,0,sourceImage.copy(cropRect))
				RenderPainter.end()

				# Fix some shit
				s = en.get("subtype")
				if s == None:
					s = 0
				v = en.get("variant")
				if v == None:
					v = 0

				# Save it to a Temp file - better than keeping it in memory for user retrieval purposes?
				filename = "resources/Entities/Temp/{0}.{1}.{2} - {3}.png".format(en.get("id"), s, v, en.get("name"))
				pixmapImg.save(filename, "PNG")

				# Pass this to the Entity Item
				e = EntityItem(en.get("name"), en.get("id"), s, v, filename)
				self.groups[name].objects.append(e)

				# Write the modded entity to the entityXML temporarily for runtime
				etmp = ET.Element("entity")
				etmp.set("Name", en.get("name"))
				etmp.set("ID", en.get("id"))
				etmp.set("Subtype", str(s))
				etmp.set("Variant", str(v))
				etmp.set("Image", filename)

				entityXML.append(etmp)

class EntityPalette(QWidget):

	def __init__(self):
		"""Initialises the widget. Remember to call setTileset() on it
		whenever the layer changes."""

		QWidget.__init__(self)

		# Make the layout
		self.layout = QVBoxLayout()
		self.layout.setSpacing(0)

		# Create the tabs for the default and mod entities
		self.tabs = QTabWidget()
		self.populateTabs()
		self.layout.addWidget(self.tabs)

		# Create the hidden search results tab
		self.searchTab = QTabWidget()

		# Funky model setup
		listView = EntityList()
		listView.setModel(EntityGroupModel(None))
		listView.model().view = listView
		listView.clicked.connect(self.objSelected)
		
		# Hide the search results
		self.searchTab.addTab(listView, "Search")
		self.searchTab.hide()

		self.layout.addWidget(self.searchTab)

		# Add the Search bar
		self.searchBar = QLineEdit()
		self.searchBar.setPlaceholderText("Search")
		self.searchBar.textEdited.connect(self.updateSearch)
		self.layout.addWidget(self.searchBar)

		# And Done
		self.setLayout(self.layout)

	def populateTabs(self):

		for group in ["Pickups", "Enemies", "Bosses", "Stage", "Collect", "Mods"]:

			listView = EntityList()

			listView.setModel(EntityGroupModel(group))
			listView.model().view = listView

			listView.clicked.connect(self.objSelected)

			if group == "Bosses":
				listView.setIconSize(QSize(52, 52))

			if group == "Collect":
				listView.setIconSize(QSize(32, 64))

			self.tabs.addTab(listView, group)

		return

	def currentSelectedObject(self):
		"""Returns the currently selected object reference, for painting purposes."""

		if len(self.searchBar.text()) > 0:
			index = self.searchTab.currentWidget().currentIndex().row()
			obj = self.searchTab.currentWidget().model().getItem(index)
		else:
			index = self.tabs.currentWidget().currentIndex().row()
			obj = self.tabs.currentWidget().model().getItem(index)

		return obj

	#@pyqtSlot()
	def objSelected(self):
		"""Throws a signal emitting the current object when changed"""
		if (self.currentSelectedObject()):
			self.objChanged.emit(self.currentSelectedObject())

		# Throws a signal when the selected object is used as a replacement
		if QApplication.keyboardModifiers() == Qt.AltModifier:
			self.objReplaced.emit(self.currentSelectedObject())

	#@pyqtSlot()
	def updateSearch(self, text):
		if len(self.searchBar.text()) > 0:
			self.tabs.hide()
			self.searchTab.widget(0).filter = text
			self.searchTab.widget(0).filterList()
			self.searchTab.show()
		else:
			self.tabs.show()
			self.searchTab.hide()

	objChanged = pyqtSignal(EntityItem)
	objReplaced = pyqtSignal(EntityItem)

class EntityList(QListView):

	def __init__(self):
		QListView.__init__(self)

		self.setFlow(QListView.LeftToRight)
		self.setLayoutMode(QListView.SinglePass)
		self.setMovement(QListView.Static)
		self.setResizeMode(QListView.Adjust)
		self.setWrapping(True)
		self.setIconSize(QSize(26, 26))

		self.setMouseTracking(True)

		self.filter = ""

	def mouseMoveEvent(self, event):

		index = self.indexAt(event.pos()).row()

		if index is not -1:
			item = self.model().getItem(index)

			if isinstance(item, EntityItem):
				QToolTip.showText(event.globalPos(), item.name)

	def filterList(self):
		m = self.model()
		rows = m.rowCount()

		# First loop for entity items
		for row in range(rows):
			item = m.getItem(row)

			if isinstance(item, EntityItem):
				if self.filter.lower() in item.name.lower():
					self.setRowHidden(row, False)
				else:
					self.setRowHidden(row, True)

		# Second loop for Group titles, check to see if all contents are hidden or not
		for row in range(rows):
			item = m.getItem(row)

			if isinstance(item, EntityGroupItem):
				self.setRowHidden(row, True)
				
				for i in range(item.startIndex, item.endIndex):
					if not self.isRowHidden(i):
						self.setRowHidden(row, False)


########################
#      Main Window     #
########################

class MainWindow(QMainWindow):

	defaultMapsDict = {
		"Special Rooms": "00.special rooms.stb",
		"Basement": "01.basement.stb",
		"Cellar": "02.cellar.stb",
		"Caves": "04.caves.stb",
		"Catacombs": "05.catacombs.stb",
		"Depths": "07.depths.stb",
		"Necropolis": "08.necropolis.stb",
		"Womb": "10.womb.stb",
		"Utero": "11.utero.stb",
		"Blue Womb": "13.blue womb.stb",
		"Sheol": "14.sheol.stb",
		"Cathedral": "15.cathedral.stb",
		"Dark Room": "16.dark room.stb",
		"Chest": "17.chest.stb",
		"Special Rooms [Greed]": "18.greed special.stb",
		"Basement [Greed]": "19.greed basement.stb",
		"Caves [Greed]": "20.greed caves.stb",
		"Depths [Greed]": "21.greed depths.stb",
		"Womb [Greed]": "22.greed womb.stb",
		"Sheol [Greed]": "23.greed sheol.stb",
		"The Shop [Greed]": "24.greed the shop.stb",
		"Ultra Greed [Greed]": "25.ultra greed.stb" }

	defaultMapsOrdered = OrderedDict(sorted(defaultMapsDict.items(), key=lambda t: t[0]))

	def __init__(self):
		QMainWindow.__init__(self)

		self.setWindowTitle('Basement Renovator')
		self.setIconSize(QSize(16, 16))

		self.dirty = False

		self.scene = RoomScene()
		self.clipboard = None

		self.editor = RoomEditorWidget(self.scene)
		self.setCentralWidget(self.editor)

		self.setupDocks()
		self.setupMenuBar()

		self.setGeometry(100, 500, 1280, 600)
		self.resetWindow = {"state" : self.saveState(), "geometry" : self.saveGeometry()}

		# Restore Settings
		if not settings.value('GridEnabled', True) or settings.value('GridEnabled', True) == 'false': self.switchGrid()
		if not settings.value('StatusEnabled', True) or settings.value('StatusEnabled', True) == 'false': self.switchInfo()
		if not settings.value('BitfontEnabled', True) or settings.value('BitfontEnabled', True) == 'false': self.switchBitFont()

		self.restoreState(settings.value('MainWindowState', self.saveState()), 0)
		self.restoreGeometry(settings.value('MainWindowGeometry', self.saveGeometry()))

		# Setup a new map
		self.newMap()
		self.clean()

	def setupFileMenuBar(self):
		f = self.fileMenu

		f.clear()
		self.fa = f.addAction('New',                self.newMap, QKeySequence("Ctrl+N"))
		self.fc = f.addAction('Open',          		self.openMap, QKeySequence("Ctrl+O"))
		self.fb = f.addAction('Open by Stage',      self.openMapDefault, QKeySequence("Ctrl+Shift+O"))
		f.addSeparator()
		self.fd = f.addAction('Save',               self.saveMap, QKeySequence("Ctrl+S"))
		self.fe = f.addAction('Save As...',         self.saveMapAs, QKeySequence("Ctrl+Shift+S"))
		f.addSeparator()
		self.fg = f.addAction('Take Screenshot...', self.screenshot, QKeySequence("Ctrl+Alt+S"))
		f.addSeparator()
		self.fh = f.addAction('Set Stage Path',     self.setDefaultStagePath, QKeySequence("Ctrl+Shift+P"))
		self.fi = f.addAction('Reset Stage Path',   self.resetStagePath, QKeySequence("Ctrl+Shift+R"))
		f.addSeparator()

		recent = settings.value("RecentFiles", [])
		for r in recent:
			f.addAction(os.path.normpath(r), self.openRecent).setData(r)

		f.addSeparator()

		self.fj = f.addAction('Exit', self.close, QKeySequence.Quit)

	def setupMenuBar(self):
		mb = self.menuBar()

		self.fileMenu = mb.addMenu('&File')
		self.setupFileMenuBar()

		self.e = mb.addMenu('Edit')
		self.ea = self.e.addAction('Copy',                        self.copy, QKeySequence.Copy)
		self.eb = self.e.addAction('Cut',                         self.cut, QKeySequence.Cut)
		self.ec = self.e.addAction('Paste',                       self.paste, QKeySequence.Paste)
		self.ed = self.e.addAction('Select All',                  self.selectAll, QKeySequence.SelectAll)
		self.ee = self.e.addAction('Deselect',                    self.deSelect, QKeySequence("Ctrl+D"))
		self.e.addSeparator()
		self.ef = self.e.addAction('Clear Filters',               self.roomList.clearAllFilter, QKeySequence("Ctrl+K"))

		v = mb.addMenu('View')
		self.wa = v.addAction('Hide Grid',                        self.switchGrid, QKeySequence("Ctrl+G"))
		self.we = v.addAction('Hide Info',                        self.switchInfo, QKeySequence("Ctrl+I"))
		self.wd = v.addAction('Use Aliased Counter',              self.switchBitFont, QKeySequence("Ctrl+Alt+A"))
		v.addSeparator()
		self.wb = v.addAction('Hide Entity Painter',              self.showPainter, QKeySequence("Ctrl+Alt+P"))
		self.wc = v.addAction('Hide Room List',                   self.showRoomList, QKeySequence("Ctrl+Alt+R"))
		self.wf = v.addAction('Reset Window Defaults',            self.resetWindowDefaults)
		v.addSeparator()

		r = mb.addMenu('Test')
		self.ra = r.addAction('Test Current Room - Basement',     self.testMap, QKeySequence("Ctrl+T"))
		self.ra = r.addAction('Test Current Room - Start',        self.testStartMap, QKeySequence("Ctrl+Shift+T"))

		h = mb.addMenu('Help')
		self.ha = h.addAction('About Basement Renovator',         self.aboutDialog)
		self.hb = h.addAction('Basement Renovator Documentation', self.goToHelp)
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
		if self.path == '':
			effectiveName = 'Untitled Map'
		else:
			if "Windows" in platform.system():
				effectiveName = os.path.normpath(self.path)
			else:
				effectiveName = os.path.basename(self.path)

		self.setWindowTitle('%s - Basement Renovator' % effectiveName)

	def checkDirty(self):
		if self.dirty == False:
			return False

		msgBox = QMessageBox(QMessageBox.Warning,
				"File is not saved", "Completing this operation without saving could cause loss of data.",
				QMessageBox.NoButton, self)
		msgBox.addButton("Continue", QMessageBox.AcceptRole)
		msgBox.addButton("Cancel", QMessageBox.RejectRole)
		if msgBox.exec_() == QMessageBox.AcceptRole:
			self.clean()
			return False

		return True

	def dirt(self):
		self.setWindowIcon(QIcon('resources/UI/BasementRenovator-SmallDirty.png'))
		self.dirty = True

	def clean(self):
		self.setWindowIcon(QIcon('resources/UI/BasementRenovator-Small.png'))
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
			# Save our state
			settings.setValue('MainWindowGeometry', self.saveGeometry())
			settings.setValue('MainWindowState', self.saveState(0))

			event.accept()

			app.quit()


#####################
# Slots for Widgets #
#####################

	#@pyqtSlot(Room, Room)
	def handleSelectedRoomChanged(self, current, prev):

		if current:

			# Encode the current room, just in case there are changes
			if prev:
				self.storeEntityList(prev)

				# Clear the current room mark
				prev.setData(100, False)

			# Clear the room and reset the size
			self.scene.clear()
			self.scene.newRoomSize(current.roomWidth, current.roomHeight, current.roomShape)

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

	#@pyqtSlot(EntityItem)
	def handleObjectChanged(self, entity):
		self.editor.objectToPaint = entity
		self.roomList.setEntityFilter(entity)

	#@pyqtSlot(EntityItem)
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
		self.roomList.changeFilter()

	def setDefaultStagePath(self):
		settings = QSettings('RoomEditor', 'Binding of Isaac Rebirth: Room Editor')
		if not settings.contains("stagepath"):
			settings.setValue("stagepath", self.findResourcePath() + "/rooms")
		stagePath = settings.value("stagepath")
		stagePathDialog = QFileDialog()
		stagePathDialog.setFilter(QDir.Hidden)
		newStagePath = QFileDialog.getExistingDirectory(self, "Select directory", stagePath)

		if newStagePath != "":
			settings.setValue("stagepath", newStagePath)
		else:
			return

	def resetStagePath(self):
		settings = QSettings('RoomEditor', 'Binding of Isaac Rebirth: Room Editor')
		settings.remove("stagepath")
		settings.remove("ResourceFolder")
		settings.setValue("stagepath", self.findResourcePath() + "/rooms")

	def openMapDefault(self):
		settings = QSettings('RoomEditor', 'Binding of Isaac Rebirth: Room Editor')
		if self.checkDirty(): return

		selectedMap, selectedMapOk = QInputDialog.getItem(self, "Map selection", "Select floor", self.defaultMapsOrdered, 0, False)
		self.restoreEditMenu()

		mapFileName = ""
		if selectedMapOk:
			mapFileName = self.defaultMapsDict[selectedMap]
		else:
			return

		if not settings.contains("stagepath"):
			settings.setValue("stagepath", self.findResourcePath() + "/rooms")
		stagePath = settings.value("stagepath")
		if not stagePath:
			QMessageBox.warning(self, "Error", "Could not set default stage path or stage path is empty.")
			return

		roomPath = os.path.expanduser(stagePath) + "/" + mapFileName

		if not QFile.exists(roomPath):
			QMessageBox.warning(self, "Error", "Failed opening stage. Make sure that the stage path is set correctly (see Edit menu) and that the proper STB file is present in the directory.")
			return

		self.openWrapper(roomPath)

	def openMap(self):
		if self.checkDirty(): return

		startPath = ""

		# Get the rooms folder if you can
		try:
			settings = QSettings('RoomEditor', 'Binding of Isaac Rebirth: Room Editor')
			if not settings.contains("stagepath"):
				settings.setValue("stagepath", self.findResourcePath() + "/rooms")
			stagePath = settings.value("stagepath")

			startPath = stagePath
		except:
			pass

		# Get the folder containing the last open file if you can
		try:
			recent = settings.value("RecentFiles", [])
			lastPath = os.path.normpath(recent[0])

			startPath = lastPath
		except:
			pass

		target = QFileDialog.getOpenFileName(
			self, 'Open Map', os.path.expanduser(startPath), 'Stage Bundle (*.stb)')
		self.restoreEditMenu()

		# Looks like nothing was selected
		if len(target[0]) == 0:
			return

		self.openWrapper(target[0])

	def openRecent(self):
		if self.checkDirty(): return

		path = self.sender().data()
		self.restoreEditMenu()

		self.openWrapper(path)

	def openWrapper(self, path=None):
		print (path)
		self.path = path

		rooms = self.open()
		if not rooms:
			QMessageBox.warning(self, "Error", "This is not a valid Afterbirth+ STB file. It may be a Rebirth STB, or it may be one of the prototype STB files accidentally included in the AB+ release.")
			return

		self.roomList.list.clear()
		self.scene.clear()
		self.updateTitlebar()

		for room in rooms:
			self.roomList.list.addItem(room)

		self.clean()
		self.roomList.changeFilter()

	def open(self, path=None):

		if path==None:
			path = self.path

		# Let's read the file and parse it into our list items
		stb = open(path, 'rb').read()

		# Header
		try:
			header = struct.unpack_from('<4s', stb, 0)[0].decode()
			if header != "STB1":
				return
		except:
			return

		off = 4

		# Room count
		rooms = struct.unpack_from('<I', stb, off)[0]
		off += 4
		ret = []

		for room in range(rooms):

			# Room Type, Room Variant, Subvariant, Difficulty, Length of Room Name String
			roomData = struct.unpack_from('<IIIBH', stb, off)
			off += 0xF
			# print ("Room Data: {0}".format(roomData))

			# Room Name
			roomName = struct.unpack_from('<{0}s'.format(roomData[4]), stb, off)[0].decode()
			off += roomData[4]
			#print ("Room Name: {0}".format(roomName))

			# Weight, width, height, shape, number of doors, number of entities
			entityTable = struct.unpack_from('<fBBBBH', stb, off)
			off += 0xA
			#print ("Entity Table: {0}".format(entityTable))

			doors = []
			for door in range(entityTable[-2]):
				# X, Y, exists
				d = struct.unpack_from('<hh?', stb, off)
				doors.append([d[0], d[1], d[2]])
				off += 5

			spawns = [[[] for y in range(26)] for x in range(14)]
			for entity in range(entityTable[-1]):
				# x, y, number of entities at this position
				spawnLoc = struct.unpack_from('<hhB', stb, off)
				off += 5

				if spawnLoc[0] < 0 or spawnLoc[1] < 0:
					print (spawnLoc[1], spawnLoc[0])

				for spawn in range(spawnLoc[2]):
					#  type, variant, subtype, weight
					t = struct.unpack_from('<HHHf', stb, off)
					spawns[spawnLoc[1]][spawnLoc[0]].append([t[0], t[1], t[2], t[3]])
					off += 0xA

			r = Room(roomName, doors, spawns, roomData[0], roomData[1], roomData[2], roomData[3], entityTable[0], entityTable[1], entityTable[2], entityTable[3])
			ret.append(r)

		# Update recent files
		recent = settings.value("RecentFiles", [])
		while recent.count(path) > 0:
			recent.remove(path)

		recent.insert(0, path)
		while len(recent) > 10:
			recent.pop()

		settings.setValue("RecentFiles", recent)
		self.setupFileMenuBar()

		return ret

	def saveMap(self, forceNewName=False):
		target = self.path

		if target == '' or forceNewName:
			dialogDir = '' if target == '' else os.path.dirname(target)
			target = QFileDialog.getSaveFileName(self, 'Save Map', dialogDir, 'Stage Bundle (*.stb)')
			self.restoreEditMenu()

			if len(target) == 0:
				return

			self.path = target[0]
			self.updateTitlebar()

		try:
			self.save(self.roomList.getRooms())
		except:
			QMessageBox.warning(self, "Error", "Saving failed. Try saving to a new file instead.")

		self.clean()
		self.roomList.changeFilter()

	def saveMapAs(self):
		self.saveMap(True)

	def save(self, rooms, path=None):
		if not path:
			path = self.path

		self.storeEntityList()

		stb = open(path, 'wb')

		out = struct.pack('<4s', "STB1".encode())
		out += struct.pack('<I', len(rooms))

		for room in rooms:

			out += struct.pack('<IIIBH{0}sfBBB'.format(len(room.data(0x100))),
							 room.roomType, room.roomVariant, room.roomSubvariant, room.roomDifficulty, len(room.data(0x100)),
							 room.data(0x100).encode(), room.roomWeight, room.roomWidth, room.roomHeight, room.roomShape)

			# Doors and Entities
			out += struct.pack('<BH', len(room.roomDoors), room.getSpawnCount())

			for door in room.roomDoors:
				out += struct.pack('<hh?', door[0], door[1], door[2])

			for y in enumerate(room.roomSpawns):
				for x in enumerate(y[1]):
					if len(x[1]) == 0: continue

					out += struct.pack('<hhB', x[0], y[0], len(x[1]))

					for entity in x[1]:
						out += struct.pack('<HHHf', entity[0], entity[1], entity[2], entity[3])

		stb.write(out)

	#@pyqtSlot()
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

	#@pyqtSlot()
	def testMap(self):
		if self.roomList.selectedRoom() == None:
			QMessageBox.warning(self, "Error", "No room was selected to test.")
			return

		# Auto-tests by adding the room to basement.
		resourcesPath = self.findResourcePath()
		if resourcesPath == "":
			return

		# Set the selected room to max weight
		self.storeEntityList(self.roomList.selectedRoom())
		r = self.roomList.selectedRoom()
		testRoom = Room(r.data(0x100), r.roomDoors, r.roomSpawns, 1, r.roomVariant, r.roomSubvariant, 1, 1000.0, r.roomWidth, r.roomHeight, r.roomShape)

		# Make a new STB with a blank room
		padMe = True
		if testRoom.roomShape not in [2, 3, 5, 7]: # Always pad these rooms
			padMe = False
			for door in testRoom.roomDoors:
				if door[2] == False:
					padMe = True

		# Needs a padded room
		if padMe:
			newRooms = [testRoom, Room(difficulty=10, weight=0.1)]
		else:
			newRooms = [testRoom]

		# Prevent accidental data loss from overwriting the file
		self.dirt()

		# Check for existing files, and backup if necessary
		backupFlagBasement = False
		if QFile.exists(resourcesPath + "/rooms/01.basement.stb"):
			os.replace(resourcesPath + "/rooms/01.basement.stb", resourcesPath + "/rooms/01.basement (backup).stb")
			backupFlagBasement = True

		backupFlagCellar = False
		if QFile.exists(resourcesPath + "/rooms/02.cellar.stb"):
			os.replace(resourcesPath + "/rooms/02.cellar.stb", resourcesPath + "/rooms/02.cellar (backup).stb")
			backupFlagCellar = True

		# Sanity check for saving
		if not QFile.exists(resourcesPath + "/rooms/"):
			os.mkdir(resourcesPath + "/rooms/")

		self.save(newRooms, resourcesPath + "/rooms/01.basement.stb")
		self.save(newRooms, resourcesPath + "/rooms/02.cellar.stb")

		# Launch Isaac
		webbrowser.open('steam://rungameid/250900')

		# Prompt to restore backup
		if padMe:
			message = "As you have a non-standard doors or shape, it's suggested to use the seed 'LABY RNTH' in order to spawn the room semi-regularly. You may have to reset a few times for your room to appear.\n\nPress 'OK' when done testing to restore your original 01.basement.stb/02.cellar.stb"
		else:
			message = "Press 'OK' when done testing to restore your original 01.basement.stb/02.cellar.stb."

		result = QMessageBox.information(self, "Restore Backup", message)

		if result == QMessageBox.Ok:
			if QFile.exists(resourcesPath + "/rooms/01.basement.stb"):
				os.remove(resourcesPath + "/rooms/01.basement.stb")
			if QFile.exists(resourcesPath + "/rooms/02.cellar.stb"):
				os.remove(resourcesPath + "/rooms/02.cellar.stb")
			if backupFlagBasement or backupFlagCellar:
				if backupFlagBasement:
					if QFile.exists(resourcesPath + "/rooms/01.basement (backup).stb"):
						os.replace(resourcesPath + "/rooms/01.basement (backup).stb", resourcesPath + "/rooms/01.basement.stb")
				if backupFlagCellar:
					if QFile.exists(resourcesPath + "/rooms/02.cellar (backup).stb"):
						os.replace(resourcesPath + "/rooms/02.cellar (backup).stb", resourcesPath + "/rooms/02.cellar.stb")

		# Extra warnings
		if self.path == resourcesPath + "/rooms/01.basement.stb" or self.path == resourcesPath + "/rooms/02.cellar.stb" :
			result = QMessageBox.information(self, "Warning", "When testing the basement.stb or cellar.stb from the resources folder, it's recommended you save before quitting or risk losing the currently open STB file completely.")

		# Why not, try catches are good practice, right? rmdir won't kill empty directories, so this will kill rooms dir if it's empty.
		try:
			if QFile.exists(resourcesPath + "/rooms/"):
				os.rmdir(resourcesPath + "/rooms/")
		except:
			pass

		self.killIsaac()

	#@pyqtSlot()
	def testStartMap(self):
		if self.roomList.selectedRoom() == None:
			QMessageBox.warning(self, "Error", "No room was selected to test.")
			return

		# Sanity check for 1x1 room
		self.storeEntityList(self.roomList.selectedRoom())
		testRoom = self.roomList.selectedRoom()

		if testRoom.roomShape in [2, 7, 9] :
			QMessageBox.warning(self, "Error", "Room shapes 2 and 7 (Long and narrow) and 9 (L shaped with upper right corner missing) can't be tested as the Start Room.")
			return

		# Auto-tests by adding the room to basement
		resourcesPath = self.findResourcePath()
		if resourcesPath == "":
			return

		# Parse the special rooms, replace the spawns
		if not QFile.exists("resources/teststart.stb"):
			QMessageBox.warning(self, "Error", "You seem to be missing the teststart.stb from resources. Please redownload Basement Renovator.")

		foundYou = False
		rooms = self.open("resources/teststart.stb")
		for room in rooms:
			if "Start Room" in room.data(0x100):
				room.roomHeight= testRoom.roomHeight
				room.roomWidth= testRoom.roomWidth
				room.roomShape= testRoom.roomShape
				room.roomSpawns = testRoom.roomSpawns
				foundYou = True

		if not foundYou:
			QMessageBox.warning(self, "Error", "teststart.stb has been tampered with, and is no longer a valid STB file.")
			return

		# Dirtify to prevent overwriting and then quitting without saving.
		self.dirt()

		# Backup, parse, find the start room, replace it, resave, restore backup
		backupFlag = False
		if QFile.exists(resourcesPath + "/rooms/00.special rooms.stb"):
			os.replace(resourcesPath + "/rooms/00.special rooms.stb", resourcesPath + "/rooms/00.special rooms (backup).stb")
			backupFlag = True

		# Sanity check for saving
		if not QFile.exists(resourcesPath + "/rooms/"):
			os.mkdir(resourcesPath + "/rooms/")

		# Resave the file
		self.save(rooms, resourcesPath + "/rooms/00.special rooms.stb")

		# Launch Isaac
		webbrowser.open('steam://rungameid/250900')

		# Prompt to restore backup
		result = QMessageBox.information(self, "Restore Backup", "Press 'OK' when done testing to restore your original 00.special rooms.stb.")
		if result == QMessageBox.Ok:
			if QFile.exists(resourcesPath + "/rooms/00.special rooms.stb"):
				os.remove(resourcesPath + "/rooms/00.special rooms.stb")
			if backupFlag:
				if QFile.exists(resourcesPath + "/rooms/00.special rooms (backup).stb"):
					os.replace(resourcesPath + "/rooms/00.special rooms (backup).stb", resourcesPath + "/rooms/00.special rooms.stb")

		# Extra warnings
		if self.path == resourcesPath + "/rooms/00.special rooms.stb":
			result = QMessageBox.information(self, "Warning", "When testing the special rooms.stb from the resources folder, it's recommended you save before quitting or risk losing the currently open stb completely.")

		# Why not, try catches are good practice, right? rmdir won't kill empty directories, so this will kill rooms dir if it's empty.
		try:
			if QFile.exists(resourcesPath + "/rooms/"):
				os.rmdir(resourcesPath + "/rooms/")
		except:
			pass

		self.killIsaac()

	def findResourcePath(self):

		resourcePath = ''

		if QFile.exists(settings.value('ResourceFolder')):
			resourcesPath = settings.value('ResourceFolder')

		else:
			cantFindPath = False
			# Windows path things
			if "Windows" in platform.system():
				basePath = QSettings('HKEY_CURRENT_USER\\Software\\Valve\\Steam', QSettings.NativeFormat).value('SteamPath')
				if not basePath:
					cantFindPath = True

				resourcesPath = basePath + "/steamapps/common/The Binding of Isaac Rebirth/resources"
				if not QFile.exists(resourcesPath):
					cantFindPath = True

			# Mac Path things
			elif "Darwin" in platform.system():
				resourcesPath = os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/The Binding of Isaac Rebirth/The Binding of Isaac Rebirth.app/Contents/Resources/resources")
				if not QFile.exists(resourcesPath):
					cantFindPath = True

			# Linux and others
			elif "Linux" in platform.system():
				resourcesPath = os.path.expanduser("~/.local/share/Steam/steamapps/common/The Binding of Isaac Rebirth/resources")
				if not QFile.exists(resourcesPath):
					cantFindPath = True
			else:
				cantFindPath = True

			# Fallback Resource Folder Locating
			if cantFindPath == True:
				resourcesPathOut = QFileDialog.getExistingDirectory(self, 'Please Locate The Binding of Isaac: Afterbirth+ Resources Folder')
				if not resourcesPathOut:
					QMessageBox.warning(self, "Error", "Couldn't locate resources folder and no folder was selected.")
					return
				else:
					resourcesPath = resourcesPathOut[0]
				if resourcesPath == "":
					QMessageBox.warning(self, "Error", "Couldn't locate resources folder and no folder was selected.")
					return
				if not QDir(resourcesPath).exists:
					QMessageBox.warning(self, "Error", "Selected folder does not exist or is not a folder.")
					return
				if not QDir(resourcesPath + "/rooms/").exists:
					QMessageBox.warning(self, "Error", "Could not find rooms folder in selected directory.")
					return

			# Looks like nothing was selected
			if len(resourcesPath) == 0:
				QMessageBox.warning(self, "Error", "Could not find The Binding of Isaac: Afterbirth+ Resources folder (" + resourcesPath + ")")
				return

			settings.setValue('ResourceFolder', resourcesPath)

		# Make sure 'rooms' exists
		if not QDir(resourcesPath + "/rooms/").exists:
			os.mkdir(resourcesPath + "/rooms/")
		return resourcesPath

	def killIsaac(self):
		for p in psutil.process_iter():
			try:
				if 'isaac' in p.name().lower():
					p.terminate()
			except:
				# This is totally kosher, I'm just avoiding zombies.
				pass

	#@pyqtSlot()
	def testMapInjectionRebirth(self):
		# This was used for antibirth

		room = self.roomList.list.currentItem()
		if not room:
			return
		
		exePath = self.getExecutablePath()
		if not exePath:
			return
		
		path = exePath + "br_output.xml"
		self.storeEntityList()
		
		out = open(path, 'w')
		
		# Floor type
		roomType = [
			('basement', 1, 0),
			('cellar', 1, 1),
			('caves', 3, 0),
			('catacombs', 3, 1),
			('depths', 5, 0),
			('necropolis', 5, 1),
			('womb', 7, 0),
			('utero', 7, 1),
			('sheol', 9, 0),
			('cathedral', 9, 1),
			('dark room', 11, 0),
			('chest', 11, 1),
			('downpour', 1, 2),
			('mines', 3, 2),
			('mausoleum', 5, 2),
			('corpse', 7, 2),
			('forest', 11, 2)
		]
		
		floorInfo = roomType[0]
		for t in roomType:
			if t[0] in mainWindow.path:
				floorInfo = t
		
		# Room header
		out.write('<room type="%d" variant="%d" difficulty="%d" name="%s" weight="%g" width="%d" height="%d">\n' % (
			room.roomType, room.roomVariant, room.roomDifficulty, room.text(),
			room.roomWeight, room.roomWidth, room.roomHeight
		))
		
		# Doors
		for door in room.roomDoors:
			out.write('\t<door x="%d" y="%d" exists="%s" />\n' % (door[0], door[1], "true" if door[2] else "false"))
		
		# Spawns
		for y in enumerate(room.roomSpawns):
			for x in enumerate(y[1]):
				if len(x[1]) == 0: continue
				
				out.write('\t<spawn x="%d" y="%d">\n' % (x[0], y[0]))
				for entity in x[1]:
					out.write('\t\t<entity type="%d" variant="%d" subtype="%d" weight="%g" />\n' % (
						entity[0], entity[1], entity[2], 2.0
					))
				out.write('\t</spawn>\n')
		
		out.write('</room>\n')
		
		exeName = "isaac-ng.exe"
		if QFile.exists(exePath + "/isaac-ng-rebirth.exe"):
			exeName = "isaac-ng-rebirth.exe"
		
		subprocess.Popen([exePath + "/" + exeName, "-room", "br_output.xml", "-floorType", str(floorInfo[1]), "-floorAlt", str(floorInfo[2]), "-console"],
			cwd = exePath
		)

	#@pyqtSlot()
	def testMapInstapreview(self):
		room = self.roomList.list.currentItem()
		if not room:
			return
		
		exePath = self.getExecutablePath()
		if not exePath:
			return
		
		path = exePath + "br_output.xml"
		self.storeEntityList()
		
		out = open(path, 'w')
		
		# Floor type
		roomType = [
			('basement', 1, 0),
			('cellar', 1, 1),
			('caves', 3, 0),
			('catacombs', 3, 1),
			('depths', 5, 0),
			('necropolis', 5, 1),
			('womb', 7, 0),
			('utero', 7, 1),
			('sheol', 9, 0),
			('cathedral', 9, 1),
			('dark room', 11, 0),
			('chest', 11, 1),
			('downpour', 1, 2),
			('mines', 3, 2),
			('mausoleum', 5, 2),
			('corpse', 7, 2),
			('forest', 11, 2)
		]
		
		floorInfo = roomType[0]
		for t in roomType:
			if t[0] in mainWindow.path:
				floorInfo = t
		
		# Room header
		out.write('<room type="%d" variant="%d" difficulty="%d" name="%s" weight="%g" width="%d" height="%d">\n' % (
			room.roomType, room.roomVariant, room.roomDifficulty, room.text(),
			room.roomWeight, room.roomWidth, room.roomHeight
		))
		
		# Doors
		for door in room.roomDoors:
			out.write('\t<door x="%d" y="%d" exists="%s" />\n' % (door[0], door[1], "true" if door[2] else "false"))
		
		# Spawns
		for y in enumerate(room.roomSpawns):
			for x in enumerate(y[1]):
				if len(x[1]) == 0: continue
				
				out.write('\t<spawn x="%d" y="%d">\n' % (x[0], y[0]))
				for entity in x[1]:
					out.write('\t\t<entity type="%d" variant="%d" subtype="%d" weight="%g" />\n' % (
						entity[0], entity[1], entity[2], 2.0
					))
				out.write('\t</spawn>\n')
		
		out.write('</room>\n')
		
		exeName = "isaac-ng.exe"
		if QFile.exists(exePath + "/isaac-ng-rebirth.exe"):
			exeName = "isaac-ng-rebirth.exe"
		
		subprocess.Popen([exePath + "/" + exeName, "-room", "br_output.xml", "-floorType", str(floorInfo[1]), "-floorAlt", str(floorInfo[2]), "-console"],
			cwd = exePath
		)

		# --set-stage-type=0 --set-stage=1 --load-room=superinstapreview.xml

# Edit
########################

	#@pyqtSlot()
	def selectAll(self):

		path = QPainterPath()
		path.addRect(self.scene.sceneRect())
		self.scene.setSelectionArea(path)

	#@pyqtSlot()
	def deSelect(self):
		self.scene.clearSelection()

	#@pyqtSlot()
	def copy(self):
		self.clipboard = []
		for item in self.scene.selectedItems():
			self.clipboard.append([item.entity['X'], item.entity['Y'], item.entity['Type'], item.entity['Variant'], item.entity['Subtype'], item.entity['Weight']])

	#@pyqtSlot()
	def cut(self):
		self.clipboard = []
		for item in self.scene.selectedItems():
			self.clipboard.append([item.entity['X'], item.entity['Y'], item.entity['Type'], item.entity['Variant'], item.entity['Subtype'], item.entity['Weight']])
			item.remove()

	#@pyqtSlot()
	def paste(self):
		if not self.clipboard: return

		self.scene.clearSelection()
		for item in self.clipboard:
			i = Entity(*item)
			self.scene.addItem(i)

		self.dirt()

# Miscellaneous
########################

	#@pyqtSlot()
	def switchGrid(self):
		"""Handle toggling of the grid being showed"""

		self.scene.grid = not self.scene.grid
		settings.setValue('GridEnabled', self.scene.grid)

		if self.scene.grid:
			self.wa.setText("Hide Grid")
		else:
			self.wa.setText("Show Grid")

		self.scene.update()

	#@pyqtSlot()
	def switchInfo(self):
		"""Handle toggling of the grid being showed"""

		self.editor.statusBar = not self.editor.statusBar
		settings.setValue('StatusEnabled', self.editor.statusBar)

		if self.editor.statusBar:
			self.we.setText("Hide Info Bar")
		else:
			self.we.setText("Show Info Bar")

		self.scene.update()

	#@pyqtSlot()
	def switchBitFont(self):
		"""Handle toggling of the bitfont for entity counting"""

		self.scene.bitText = not self.scene.bitText
		settings.setValue('BitfontEnabled', self.scene.bitText)

		if self.scene.bitText:
			self.wd.setText("Use Aliased Counter")
		else:
			self.wd.setText("Use Bitfont Counter")

		self.scene.update()

	#@pyqtSlot()
	def showPainter(self):
		if self.EntityPaletteDock.isVisible():
			self.EntityPaletteDock.hide()
		else:
			self.EntityPaletteDock.show()

		self.updateDockVisibility()

	#@pyqtSlot()
	def showRoomList(self):
		if self.roomListDock.isVisible():
			self.roomListDock.hide()
		else:
			self.roomListDock.show()

		self.updateDockVisibility()

	#@pyqtSlot()
	def updateDockVisibility(self):

		if self.EntityPaletteDock.isVisible():
			self.wb.setText('Hide Entity Painter')
		else:
			self.wb.setText('Show Entity Painter')

		if self.roomListDock.isVisible():
			self.wc.setText('Hide Room List')
		else:
			self.wc.setText('Show Room List')

	#@pyqtSlot()
	def resetWindowDefaults(self):
		self.restoreState(self.resetWindow["state"], 0)
		self.restoreGeometry(self.resetWindow["geometry"])

# Help
########################

	#@pyqtSlot(bool)
	def aboutDialog(self):
		caption = "About the Basement Renovator"

		text = "<big><b>Basement Renovator</b></big><br><br>    The Basement Renovator Editor is an editor for custom rooms, for use with the Binding of Isaac Afterbirth. In order to use it, you must have unpacked the .stb files from Binding of Isaac Afterbirth.<br><br>    The Basement Renovator was programmed by Tempus (u/Chronometrics).<br><br>    Find the source on <a href='https://github.com/Tempus/Basement-Renovator'>github</a>."

		msg = QMessageBox.about(mainWindow, caption, text)

	#@pyqtSlot(bool)
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
	mainWindow.show()

	sys.exit(app.exec_())
