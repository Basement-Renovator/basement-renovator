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
#		Bosscolours for the alternate boss entities
#


from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from collections import OrderedDict
from copy import deepcopy

import struct, os, subprocess, platform, webbrowser, urllib, re, shutil
from pathlib import Path
import xml.etree.ElementTree as ET
import psutil


########################
#       XML Data       #
########################

def getEntityXML():
    tree = ET.parse('resources/EntitiesAfterbirthPlus.xml')
    root = tree.getroot()

    return root

def findInstallPath():
    installPath = ''
    cantFindPath = False

    if QFile.exists(settings.value('InstallFolder')):
        installPath = settings.value('InstallFolder')

    else:
        # Windows path things
        if "Windows" in platform.system():
            basePath = QSettings('HKEY_CURRENT_USER\\Software\\Valve\\Steam', QSettings.NativeFormat).value('SteamPath')
            if not basePath:
                cantFindPath = True

            installPath = os.path.join(basePath, "steamapps", "common", "The Binding of Isaac Rebirth")
            if not QFile.exists(installPath):
                cantFindPath = True

                libconfig = os.path.join(basePath, "steamapps", "libraryfolders.vdf")
                if os.path.isfile(libconfig):
                    libLines = list(open(libconfig, 'r'))
                    matcher = re.compile(r'"\d+"\s*"(.*?)"')
                    installDirs = map(lambda res: os.path.normpath(res.group(1)),
                                        filter(lambda res: res,
                                            map(lambda line: matcher.search(line), libLines)))
                    for root in installDirs:
                        installPath = os.path.join(root, 'steamapps', 'common', 'The Binding of Isaac Rebirth')
                        if QFile.exists(installPath):
                            cantFindPath = False
                            break

        # Mac Path things
        elif "Darwin" in platform.system():
            installPath = os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/The Binding of Isaac Rebirth/The Binding of Isaac Rebirth.app/Contents/Resources")
            if not QFile.exists(installPath):
                cantFindPath = True

        # Linux and others
        elif "Linux" in platform.system():
            installPath = os.path.expanduser("~/.local/share/Steam/steamapps/common/The Binding of Isaac Rebirth")
            if not QFile.exists(installPath):
                cantFindPath = True
        else:
            cantFindPath = True

        # Looks like nothing was selected
        if cantFindPath or installPath == '' or not os.path.isdir(installPath):
            print(f"Could not find The Binding of Isaac: Afterbirth+ install folder ({installPath})")
            return ''

        settings.setValue('InstallFolder', installPath)

    return installPath

def findModsPath(installPath=None):
    modsPath = ''
    cantFindPath = False

    if QFile.exists(settings.value('ModsFolder')):
        modsPath = settings.value('ModsFolder')

    else:
        installPath = installPath or findInstallPath()
        if len(installPath) > 0:
            modd = os.path.join(installPath, "savedatapath.txt")
            if os.path.isfile(modd):
                lines = list(open(modd, 'r'))
                modDirs = list(filter(lambda parts: parts[0] == 'Modding Data Path',
                                map(lambda line: line.split(': '), lines)))
                if len(modDirs) > 0:
                    modsPath = os.path.normpath(modDirs[0][1].strip())

    if modsPath == '' or not os.path.isdir(modsPath):
        cantFindPath = True

    if cantFindPath:
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
        if cantFindPath:
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
        if modsPath == '' or not os.path.isdir(modsPath):
            QMessageBox.warning(None, "Error", f"Could not find The Binding of Isaac: Afterbirth+ Mods folder ({modsPath})")
            return ''

        settings.setValue('ModsFolder', modsPath)

    return modsPath

def linuxPathSensitivityTraining(path):

    path = path.replace("\\", "/")

    directory, file = os.path.split(os.path.normpath(path))

    if not os.path.isdir(directory):
        return None

    contents = os.listdir(directory)

    for item in contents:
        if item.lower() == file.lower():
            return os.path.normpath(os.path.join(directory, item))

    return os.path.normpath(path)

def loadFromModXML(modPath, name, entRoot, resourcePath, fixIconFormat=False):

    anm2root = entRoot.get("anm2root")

    # Iterate through all the entities
    enList = entRoot.findall("entity")

    # Skip if the mod is empty
    if len(enList) == 0:
        return

    print('-----------------------\nLoading entities from "%s"' % name)

    def mapEn(en):
        # Fix some shit
        i = int(en.get("id"))
        if i == 1000: i = 999
        s = en.get("subtype") or '0'
        v = en.get("variant") or '0'

        if i >= 1000 or i in (0, 1, 3, 7, 8, 9):
            print('Skipping: Invalid entity type %d: %s' % (i, en.get("name")))
            return None

        # Grab the anm location
        anmPath = linuxPathSensitivityTraining(os.path.join(modPath, "resources", anm2root, en.get("anm2path"))) or ''
        print('LOADING: %s' % anmPath)
        if not os.path.isfile(anmPath):
            anmPath = linuxPathSensitivityTraining(os.path.join(resourcePath, anm2root, en.get('anm2path'))) or ''

            print('REDIRECT LOADING: %s' % anmPath)
            if not os.path.isfile(anmPath):
                print('Skipping: Invalid anm2!')
                return None

        anm2Dir, anm2File = os.path.split(anmPath)

        # Grab the first frame of the anm
        anmTree = ET.parse(anmPath)
        spritesheets = anmTree.findall(".Content/Spritesheets/Spritesheet")
        layers = anmTree.findall(".Content/Layers/Layer")
        default = anmTree.find("Animations").get("DefaultAnimation")

        anim = anmTree.find(f"./Animations/Animation[@Name='{default}']")
        framelayers = anim.findall(".//LayerAnimation[Frame]")

        imgs = []
        ignoreCount = 0
        for layer in framelayers:
            if layer.get('Visible') == 'false':
                ignoreCount += 1
                continue

            frame = layer.find('Frame')
            if frame.get('Visible') == 'false':
                ignoreCount += 1
                continue

            sheetPath = spritesheets[int(layers[int(layer.get("LayerId"))].get("SpritesheetId"))].get("Path")
            image = os.path.abspath(os.path.join(anm2Dir, sheetPath))
            imgPath = linuxPathSensitivityTraining(image)
            if not (imgPath and os.path.isfile(imgPath)):
                image = re.sub(r'.*resources', resourcePath, image)
                imgPath = linuxPathSensitivityTraining(image)
                
            if imgPath and os.path.isfile(imgPath):
                # Here's the anm specs
                xp = -int(frame.get("XPivot")) # applied before rotation
                yp = -int(frame.get("YPivot"))
                r = int(frame.get("Rotation"))
                x = int(frame.get("XPosition")) # applied after rotation
                y = int(frame.get("YPosition"))
                xc = int(frame.get("XCrop"))
                yc = int(frame.get("YCrop"))
                #xs = float(frame.get("XScale")) / 100
                #ys = float(frame.get("YScale")) / 100
                xs, ys = 1, 1 # this ended up being a bad idea since it's usually used for squash and stretch
                w = int(frame.get("Width"))
                h = int(frame.get("Height"))

                imgs.append([imgPath, x, y, xc, yc, w, h, xs, ys, r, xp, yp])

        filename = "resources/Entities/questionmark.png"
        if len(imgs) == 0:
            print(f'Entity Icon could not be generated due to {ignoreCount > 0 and "visibility" or "missing files"}')
        else:

            # Fetch each layer and establish the needed dimensions for the final image
            finalRect = QRect()
            for img in imgs:
                imgPath, x, y, xc, yc, w, h, xs, ys, r, xp, yp = img
                cropRect = QRect(xc, yc, w, h)

                mat = QTransform()
                mat.rotate(r)
                mat.scale(xs, ys)
                mat.translate(xp, yp)

                # Load the Image
                qimg = QImage(imgPath)
                sourceImage = qimg.copy(cropRect).transformed(mat)
                img.append(sourceImage)

                if fixIconFormat:
                    qimg.save(imgPath)

                cropRect.moveTopLeft(QPoint())
                cropRect = mat.mapRect(cropRect)
                cropRect.translate(QPoint(x, y))
                finalRect = finalRect.united(cropRect)
                img.append(cropRect)

            # Create the destination
            pixmapImg = QImage(finalRect.width(), finalRect.height(), QImage.Format_ARGB32)
            pixmapImg.fill(0)

            # Paint all the layers to it
            RenderPainter = QPainter(pixmapImg)
            for imgPath, x, y, xc, yc, w, h, xs, ys, r, xp, yp, sourceImage, boundingRect in imgs:
                # Transfer the crop area to the pixmap
                boundingRect.translate(-finalRect.topLeft())
                RenderPainter.drawImage(boundingRect, sourceImage)
            RenderPainter.end()

            # Save it to a Temp file - better than keeping it in memory for user retrieval purposes?
            resDir = f'resources/Entities/ModTemp/{name}/'
            if not os.path.isdir(resDir): os.mkdir(resDir)
            filename = os.path.join(resDir, f'{en.get("id")}.{v}.{s} - {en.get("name")}.png')
            pixmapImg.save(filename, "PNG")

        # Write the modded entity to the entityXML temporarily for runtime
        etmp = ET.Element("entity")
        etmp.set("Name", en.get("name"))
        etmp.set("ID", str(i))
        etmp.set("Subtype", s)
        etmp.set("Variant", v)
        etmp.set("Image", filename)
        etmp.set("BaseHP", en.get("baseHP"))

        i = int(i)
        etmp.set("Group", "(Mod) %s" % name)
        etmp.set("Kind", "Mods")
        if i == 5: # pickups
            if v == 100: # collectible
                return None
            etmp.set("Kind", "Pickup")
        elif i in (2, 4, 6): # tears, live bombs, machines
            etmp.set("Kind", "Stage")
        elif en.get("boss") == '1':
            etmp.set("Kind", "Bosses")
        else:
            etmp.set("Kind", "Enemies")

        return etmp

    return list(filter(lambda x: x != None, map(mapEn, enList)))

def loadFromMod(modPath, name, entRoot, fixIconFormat=False):

    brPath = os.path.join(modPath, 'basementrenovator')
    if not os.path.isdir(brPath):
        return

    entFile = os.path.join(brPath, 'EntitiesMod.xml')
    if not os.path.isfile(entFile):
        return

    tree = ET.parse(entFile)
    root = tree.getroot()

    enList = root.findall('entity')
    if len(enList) == 0:
        return

    print('-----------------------\nLoading entities from "%s"' % name)

    def mapEn(en):
        imgPath = linuxPathSensitivityTraining(os.path.join(brPath, en.get('Image')))

        i = en.get('ID')
        v = en.get('Variant') or '0'
        s = en.get('Subtype') or '0'

        entXML = None

        if en.get('Metadata') != '1':
            adjustedId = i == 999 and 1000 or i
            query = f"entity[@id='{adjustedId}'][@variant='{v}']"

            entXML = entRoot.find(query + f"[@subtype='{s}']")
            if entXML is None and s == '0':
                entXML = entRoot.find(query)

            if entXML == None:
                print('Loading invalid entity (no entry in entities2 xml): ' + str(en.attrib))
                en.set('Invalid', '1')

        # Write the modded entity to the entityXML temporarily for runtime
        if not en.get('Group'):
            en.set('Group', '(Mod) %s' % name)
        en.set("Image", imgPath)

        if fixIconFormat:
            formatFix = QImage(imgPath)
            formatFix.save(imgPath)

        en.set("Subtype", s)
        en.set("Variant", v)

        en.set('BaseHP', entXML and entXML.get('baseHP') or en.get('BaseHP'))

        return en

    return list(map(mapEn, enList))

def loadMods(autogenerate, installPath, resourcePath):
    global entityXML

    # Each mod in the mod folder is a Group
    modsPath = findModsPath(installPath)
    if not os.path.isdir(modsPath):
        print('Could not find Mods Folder! Skipping mod content!')
        return

    modsInstalled = os.listdir(modsPath)

    fixIconFormat = settings.value('FixIconFormat') == '1'

    autogenPath = 'resources/Entities/ModTemp'
    if autogenerate and not os.path.exists(autogenPath):
        os.mkdir(autogenPath)

    print('LOADING MOD CONTENT')
    for mod in modsInstalled:
        modPath = os.path.join(modsPath, mod)

        # Make sure we're a mod
        if not os.path.isdir(modPath) or os.path.isfile(os.path.join(modPath, 'disable.it')):
            continue

        # simple workaround for now
        if not autogenerate and not os.path.exists(os.path.join(modPath, 'basementrenovator', 'EntitiesMod.xml')):
            continue

        # Get the mod name
        name = mod
        try:
            tree = ET.parse(os.path.join(modPath, 'metadata.xml'))
            root = tree.getroot()
            name = root.find("name").text
        except ET.ParseError:
            print('Failed to parse mod metadata "%s", falling back on default name' % name)

        # add dedicated entities
        entPath = os.path.join(modPath, 'content/entities2.xml')
        if os.path.exists(entPath):
            # Grab their Entities2.xml
            entRoot = None
            try:
                entRoot = ET.parse(entPath).getroot()
            except ET.ParseError as e:
                print(f'ERROR parsing entities2 xml for mod "{name}": {e}')
                continue

            ents = None
            if autogenerate:
                ents = loadFromModXML(modPath, name, entRoot, resourcePath, fixIconFormat=fixIconFormat)
            else:
                ents = loadFromMod(modPath, name, entRoot, fixIconFormat=fixIconFormat)

            if ents:
                for ent in ents:
                    name, i, v, s = ent.get('Name'), int(ent.get('ID')), int(ent.get('Variant')), int(ent.get('Subtype'))

                    if i >= 1000:
                        print('Entity "%s" has a type outside the 0 - 999 range! (%d) It will not load properly from rooms!' % (name, i))
                    if v >= 4096:
                        print('Entity "%s" has a variant outside the 0 - 4095 range! (%d)' % (name, v))
                    if s >= 256:
                        print('Entity "%s" has a subtype outside the 0 - 255 range! (%d)' % (name, s))

                    existingEn = entityXML.find(f"entity[@ID='{i}'][@Subtype='{s}'][@Variant='{v}']")
                    if existingEn != None:
                        print(f'Entity "{name}" has the same id, variant, and subtype ({i}.{v}.{s}) as "{existingEn.get("Name")}" from "{existingEn.get("Kind")}" > "{existingEn.get("Group")}"!')

                    entityXML.append(ent)

    settings.setValue('FixIconFormat', '0')

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
            "13_burningbasement", "14_floodedcaves", "15_dankdepths", "16_scarredwomb",
            "18_bluewomb",
            "0a_library", "0b_shop", "0c_isaacsroom", "0d_barrenroom",
            "0e_arcade", "0e_diceroom", "0f_secretroom"
        ]
        self.grid = True

        # Make the bitfont
        q = QImage()
        q.load('resources/UI/Bitfont.png')

        self.bitfont = [ QPixmap.fromImage(q.copy(i * 12, j * 12, 12, 12)) for j in range(int(q.height() / 12)) for i in range(int(q.width() / 12)) ]
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
            b = QBrush(QColor(255, 255, 255, 100))
            painter.setPen(Qt.white)
            painter.setBrush(b)

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

        x = int(x / 26)
        y = int(y / 26)

        xmax, ymax = self.scene().roomWidth, self.scene().roomHeight

        # TODO fix for weird rooms and out of bounds

        x = min(max(x, 0), xmax - 1)
        y = min(max(y, 0), ymax - 1)

        for i in self.scene().items():
            if isinstance(i, Entity):
                if i.entity.x == x and i.entity.y == y:
                    if i.stackDepth == EntityStack.MAX_STACK_DEPTH:
                        return

                    i.hideWeightPopup()

                    # Don't stack multiple grid entities
                    if int(i.entity.Type) > 999 and int(self.objectToPaint.ID) > 999:
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
        # not calling this for right click + adding items to the scene causes crashes
        QGraphicsView.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        if self.lastTile:
            if mainWindow.roomList.selectedRoom() is not None:
                self.tryToPaint(event)
                event.accept()
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
            painter.drawText(8, 30, f"Difficulty: {room.roomDifficulty}, Weight: {room.roomWeight}, Subtype: {room.roomSubvariant}")

        # Display the currently selected entity in a text overlay
        selectedEntities = self.scene().selectedItems()

        if len(selectedEntities) == 1:
            e = selectedEntities[0]
            r = event.rect()

            # Entity Icon
            i = QIcon()
            painter.drawPixmap(QRect(r.right() - 32, 2, 32, 32), e.entity.pixmap)

            # Top Text
            font = painter.font()
            font.setPixelSize(13)
            painter.setFont(font)
            painter.drawText(r.right() - 34 - 400, 2, 400, 16, Qt.AlignRight | Qt.AlignBottom,
                                f'{e.entity.Type}.{e.entity.Variant}.{e.entity.Subtype} - {e.entity.name}')

            # Bottom Text
            font = painter.font()
            font.setPixelSize(10)
            painter.setFont(font)
            painter.drawText(r.right() - 34 - 200, 20, 200, 12, Qt.AlignRight | Qt.AlignBottom, f"Base HP : {e.entity.baseHP}")

        elif len(selectedEntities) > 1:
            e = selectedEntities[0]
            r = event.rect()

            # Case Two: more than one type of entity
            # Entity Icon
            i = QIcon()
            painter.drawPixmap(QRect(r.right() - 32, 2, 32, 32), e.entity.pixmap)

            # Top Text
            font = painter.font()
            font.setPixelSize(13)
            painter.setFont(font)
            painter.drawText(r.right() - 34 - 200, 2, 200, 16, Qt.AlignRight | Qt.AlignBottom, f"{len(selectedEntities)} Entities Selected" )

            # Bottom Text
            font = painter.font()
            font.setPixelSize(10)
            painter.setFont(font)
            painter.drawText(r.right() - 34 - 200, 20, 200, 12, Qt.AlignRight | Qt.AlignBottom, ", ".join(set([x.entity.name for x in selectedEntities])) )

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
                tiles[e.entity.y][e.entity.x] += 1

        if not self.scene().bitText:
            painter.setPen(Qt.white)
            painter.font().setPixelSize(5)

        for y, row in enumerate(tiles):
            yc = (y + 1) * 26 - 12

            for x, count in enumerate(row):
                if count <= 1: continue

                if self.scene().bitText:
                    xc = (x + 1) * 26 - 12

                    digits = [ int(i) for i in str(count) ]

                    fontrow = count == EntityStack.MAX_STACK_DEPTH and 1 or 0

                    numDigits = len(digits) - 1
                    for i, digit in enumerate(digits):
                        painter.drawPixmap( xc - 12 * (numDigits - i), yc, self.scene().bitfont[digit + fontrow * 10] )
                else:
                    if count == EntityStack.MAX_STACK_DEPTH: painter.setPen(Qt.red)

                    painter.drawText( x * 26, y * 26, 26, 26, Qt.AlignBottom | Qt.AlignRight, str(count) )

                    if count == EntityStack.MAX_STACK_DEPTH: painter.setPen(Qt.white)

class Entity(QGraphicsItem):
    SNAP_TO = 26

    class Info:
        def __init__(self, x, y, t, v, s, weight, changeAtStart=True):
            # Supplied entity info
            self.x = x
            self.y = y
            self.weight = weight

            if changeAtStart:
                self.changeTo(t, v, s)

        def changeTo(self, t, v, s):
            self.Type = t
            self.Variant = v
            self.Subtype = s

            # Derived Entity Info
            self.name = None
            self.isGridEnt = False
            self.baseHP = None
            self.boss = None
            self.champion = None
            self.pixmap = None
            self.known = False
            self.invalid = False
            self.placeVisual = None

            self.getEntityInfo(t, v, s)

        def getEntityInfo(self, t, variant, subtype):

            en = None
            try:
                global entityXML
                en = entityXML.find(f"entity[@ID='{t}'][@Subtype='{subtype}'][@Variant='{variant}']")
            except:
                print (f"Entity {t}, Variant {variant}, Subtype {subtype} expected, but was not found")
                en = None

            if en == None:
                self.pixmap = QPixmap("resources/Entities/questionmark.png")
                return

            self.name = en.get('Name')
            self.isGridEnt = en.get('Kind') == 'Stage' and \
                            en.get('Group') in [ 'Grid', 'Poop', 'Fireplaces', 'Other', 'Props', 'Special Exits', 'Broken' ]

            self.baseHP = en.get('BaseHP')
            self.boss = en.get('Boss')
            self.champion = en.get('Champion')
            self.placeVisual = en.get('PlaceVisual')

            if t == 5 and variant == 100:
                i = QImage()
                i.load('resources/Entities/5.100.0 - Collectible.png')
                i = i.convertToFormat(QImage.Format_ARGB32)

                d = QImage()
                d.load(en.get('Image'))

                p = QPainter(i)
                p.drawImage(0, 0, d)
                p.end()

                self.pixmap = QPixmap.fromImage(i)

            else:
                self.pixmap = QPixmap(en.get('Image'))

            def checkNum(s):
                try:
                    float(s)
                    return True
                except ValueError:
                    return False

            if self.placeVisual:
                parts = list(map(lambda x: x.strip(), self.placeVisual.split(',')))
                if len(parts) == 2 and checkNum(parts[0]) and checkNum(parts[1]):
                    self.placeVisual = (float(parts[0]), float(parts[1]))
                else:
                    self.placeVisual = parts[0]

            self.invalid = en.get('Invalid') == '1'
            self.known = True


    def __init__(self, x, y, mytype, variant, subtype, weight):
        QGraphicsItem.__init__(self)
        self.setFlags(
            self.ItemSendsGeometryChanges |
            self.ItemIsSelectable |
            self.ItemIsMovable
        )

        self.stackDepth = 1
        self.popup = None
        mainWindow.scene.selectionChanged.connect(self.hideWeightPopup)

        self.entity = Entity.Info(x, y, mytype, variant, subtype, weight)
        self.updateTooltip()

        self.updatePosition()
        if self.entity.Type < 999:
            self.setZValue(1)
        else:
            self.setZValue(0)

        if not hasattr(Entity, 'SELECTION_PEN'):
            Entity.SELECTION_PEN = QPen(Qt.green, 1, Qt.DashLine)
            Entity.OFFSET_SELECTION_PEN = QPen(Qt.red, 1, Qt.DashLine)
            Entity.INVALID_ERROR_IMG = QPixmap('resources/UI/ent-error.png')
            Entity.OUT_OF_RANGE_WARNING_IMG = QPixmap('resources/UI/ent-warning.png')

        self.setAcceptHoverEvents(True)

    def setData(self, t, v, s):
        self.entity.changeTo(t, v, s)
        self.updateTooltip()

    def updateTooltip(self):
        e = self.entity
        tooltipStr = f"{e.name} @ {e.x} x {e.y} - {e.Type}.{e.Variant}.{e.Subtype}; HP: {e.baseHP}"
        
        if e.Type >= 1000 and not e.isGridEnt:
            tooltipStr += '\nType is outside the valid range of 0 - 999! This will not load properly in-game!'
        if e.Variant >= 4096:
            tooltipStr += '\nVariant is outside the valid range of 0 - 4095!'
        if e.Subtype >= 255:
            tooltipStr += '\nSubtype is outside the valid range of 0 - 255!'
        if e.invalid:
            tooltipStr += '\nMissing entities2.xml entry! Trying to spawn this WILL CRASH THE GAME!!'

        self.setToolTip(tooltipStr)

    def itemChange(self, change, value):

        if change == self.ItemPositionChange:

            currentX, currentY = self.x(), self.y()

            x, y = value.x(), value.y()

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
                self.entity.x = int(x / self.SNAP_TO)
                self.entity.y = int(y / self.SNAP_TO)
                
                self.updateTooltip()
                if self.isSelected():
                    mainWindow.dirt()

            value.setX(x)
            value.setY(y)

            self.getStack()
            if self.popup: self.popup.update(self.stack)


            return value

        return QGraphicsItem.itemChange(self, change, value)

    def boundingRect(self):

        #if self.entity.pixmap:
        #	return QRectF(self.entity.pixmap.rect())
        #else:
        return QRectF(0.0, 0.0, 26.0, 26.0)

    def updatePosition(self):
        self.setPos(self.entity.x * 26, self.entity.y * 26)

    def paint(self, painter, option, widget):

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        painter.setBrush(Qt.Dense5Pattern)
        painter.setPen(QPen(Qt.white))

        if self.entity.pixmap:
            w, h = self.entity.pixmap.width(), self.entity.pixmap.height()
            xc, yc = 0, 0

            typ, var, sub = self.entity.Type, self.entity.Variant, self.entity.Subtype

            def WallSnap():
                rw = self.scene().roomWidth
                rh = self.scene().roomHeight
                ex = self.entity.x
                ey = self.entity.y

                shape = self.scene().roomShape
                if shape == 9:
                    if ex < 13:
                        ey -= 7
                        rh = 7
                    elif ey < 7:
                        ex -= 13
                        rw = 13
                elif shape == 10:
                    if ex >= 13:
                        ey -= 7
                        rh = 7
                    elif ey < 7:
                        rw = 13
                elif shape == 11:
                    if ex < 13:
                        rh = 7
                    elif ey >= 7:
                        ex -= 13
                        rw = 13
                elif shape == 12:
                    if ex > 13:
                        rh = 7
                    elif ey >= 7:
                        rw = 13

                distances = [rw - ex - 1, ex, ey, rh - ey - 1]
                closest = min(distances)
                direction = distances.index(closest)

                wx, wy = 0, 0
                if direction == 0: # Right
                    wx, wy = 2 * closest + 1, 0

                elif direction == 1: # Left
                    wx, wy = -2 * closest - 1, 0

                elif direction == 2: # Top
                    wx, wy = 0, -closest - 1

                elif direction == 3: # Bottom
                    wx, wy = 0, closest

                return wx, wy

            customPlaceVisuals = {
                'WallSnap': WallSnap
            }

            recenter = self.entity.placeVisual
            if recenter:
                if isinstance(recenter, str):
                    recenter = customPlaceVisuals.get(recenter, None)
                    if recenter:
                        xc, yc = recenter()
                else:
                    xc, yc = recenter

            xc += 1
            yc += 1
            x = (xc * 26 - w) / 2
            y = (yc * 26 - h)

            def drawGridBorders():
                painter.drawLine(0, 0, 0, 4)
                painter.drawLine(0, 0, 4, 0)

                painter.drawLine(26, 0, 26, 4)
                painter.drawLine(26, 0, 22, 0)

                painter.drawLine(0, 26, 4, 26)
                painter.drawLine(0, 26, 0, 22)

                painter.drawLine(26, 26, 22, 26)
                painter.drawLine(26, 26, 26, 22)

            # Curse room special case
            if typ == 5 and var == 50 and mainWindow.roomList.selectedRoom().roomType == 10:
                self.entity.pixmap = QPixmap('resources/Entities/5.360.0 - Red Chest.png')

            painter.drawPixmap(x, y, self.entity.pixmap)

            # if the offset is high enough, draw an indicator of the actual position
            if abs(1 - yc) > 0.5 or abs(1 - xc) > 0.5:
                painter.setPen(self.OFFSET_SELECTION_PEN)
                painter.setBrush(Qt.NoBrush)
                painter.drawLine(13, 13, x + w / 2, y + h - 13)
                drawGridBorders()
                painter.fillRect(x + w / 2 - 3, y + h - 13 - 3, 6, 6, Qt.red)

            if self.isSelected():
                painter.setPen(self.SELECTION_PEN)
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(x, y, w, h)

                # Grid space boundary
                painter.setPen(Qt.green)
                drawGridBorders()

        if not self.entity.known:
            painter.setFont(QFont("Arial", 6))

            painter.drawText(2, 26, "%d.%d.%d" % (typ, var, sub))
        
        warningIcon = None
        # applies to entities that do not have a corresponding entities2 entry
        if self.entity.invalid:
            warningIcon = Entity.INVALID_ERROR_IMG
        # entities have 12 bits for type and variant, 8 for subtype
        # common mod error is to make them outside that range
        elif var >= 4096 or sub >= 256 or (typ >= 1000 and not self.entity.isGridEnt):
            warningIcon = Entity.OUT_OF_RANGE_WARNING_IMG
        
        if warningIcon:
            painter.drawPixmap(18, -8, warningIcon)

    def remove(self):
        if self.popup:
            self.popup.remove()
            self.scene().views()[0].canDelete = True
        self.scene().removeItem(self)

    def mouseReleaseEvent(self, event):
        self.hideWeightPopup()
        QGraphicsItem.mouseReleaseEvent(self, event)

    def hoverEnterEvent(self, event):
        self.createWeightPopup()

    def hoverLeaveEvent(self, event):
        self.hideWeightPopup()

    def getStack(self):
        # Get the stack
        stack = self.collidingItems(Qt.IntersectsItemBoundingRect)
        stack.append(self)

        # Make sure there are no doors or popups involved
        self.stack = [x for x in stack if isinstance(x,Entity)]

        # 1 is not a stack.
        self.stackDepth = len(self.stack)

    def createWeightPopup(self):
        self.getStack()
        if self.stackDepth <= 1 or any(x.popup and x != self and x.popup.isVisible() for x in self.stack):
            self.hideWeightPopup()
            return

        # If there's no popup, make a popup
        if self.popup:
            if self.popup.activeSpinners != self.stackDepth:
                self.popup.update(self.stack)
            self.popup.setVisible(True)
            return

        self.scene().views()[0].canDelete = False
        self.popup = EntityStack(self.stack)
        self.scene().addItem(self.popup)

    def hideWeightPopup(self):
        if self.popup and self not in mainWindow.scene.selectedItems():
            self.popup.setVisible(False)
            if self.scene(): self.scene().views()[0].canDelete = True

class EntityStack(QGraphicsItem):
    MAX_STACK_DEPTH = 25

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

        self.spinners = []
        self.activeSpinners = 0
        self.update(items)

    def update(self, items):
        activeSpinners = len(items)

        for i in range(activeSpinners - len(self.spinners)):
            weight = self.WeightSpinner()
            weight.valueChanged.connect(lambda: self.weightChanged(i))
            self.spinners.append(self.Proxy(weight, self))

        for i in range(activeSpinners, len(self.spinners)):
            self.spinners[i].setVisible(False)

        if activeSpinners > 1:
            for i, item in enumerate(items):
                spinner = self.spinners[i]
                spinner.widget().setValue(item.entity.weight)
                spinner.setVisible(True)
        else:
            self.setVisible(False)

        # it's very important that this happens AFTER setting up the spinners
        # it greatly increases the odds of races with weightChanged if items are updated first
        self.items = items
        self.activeSpinners = activeSpinners

    def weightChanged(self, idx):
        if idx < self.activeSpinners:
            self.items[idx].entity.weight = self.spinners[idx].widget().value()

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
        painter.setFont(QFont("Arial", 8))

        w = 0
        for i, item in enumerate(self.items):
            pix = item.entity.pixmap
            self.spinners[i].setPos(w-8, r.bottom()-26)
            w += 4
            painter.drawPixmap(w, r.bottom()-20-pix.height(), pix)

            # painter.drawText(w, r.bottom()-16, pix.width(), 8, Qt.AlignCenter, "{:.1f}".format(item.entity.weight))
            w += pix.width()

    def boundingRect(self):
        width = 0
        height = 0

        # Calculate the combined size
        for item in self.items:
            dx, dy = 26, 26
            pix = item.entity.pixmap
            if pix:
                dx, dy = pix.rect().width(), pix.rect().height()
            width = width + dx
            height = max(height, dy)

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
        del self.spinners

        self.scene().removeItem(self)

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

        self.setData(0x100, name)

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
        self.setForeground(QColor.fromHsvF(1, 1, min(max(d / 15, 0), 1), 1))

    ########## SHAPE DEFINITIONS
        # w x h
        # 1 = 1x1, 2 = 1x0.5, 3 = 0.5x1, 4 = 2x1, 5 = 2x0.5, 6 = 1x2, 7 = 0.5x2, 8 = 2x2
        # 9 = DR corner, 10 = DL corner, 11 = UR corner, 12 = UL corner
    ShapeDoors = {
        1: [[6, -1, True], [-1, 3, True], [13, 3, True], [6, 7, True]],
        2: [[-1, 3, True], [13, 3, True]],
        3: [[6, -1, True], [6, 7, True]],
        4: [[6, -1, True], [13, 3, True], [-1, 3, True], [13, 10, True], [-1, 10, True], [6, 14, True]],
        5: [[6, -1, True], [6, 14, True]],
        6: [[6, -1, True], [-1, 3, True], [6, 7, True], [19, 7, True], [26, 3, True], [19, -1, True]],
        7: [[-1, 3, True], [26, 3, True]],
        8: [[6, -1, True], [-1, 3, True], [-1, 10, True], [19, -1, True], [6, 14, True], [19, 14, True], [26, 3, True], [26, 10, True]],
        9: [[19, -1, True], [26, 3, True], [6, 14, True], [19, 14, True], [12, 3, True], [-1, 10, True], [26, 10, True], [6, 6, True]],
        10: [[-1, 3, True], [13, 3, True], [6, -1, True], [19, 6, True], [6, 14, True], [19, 14, True], [-1, 10, True], [26, 10, True]],
        11: [[-1, 3, True], [6, 7, True], [6, -1, True], [12, 10, True], [19, -1, True], [26, 3, True], [19, 14, True], [26, 10, True]],
        12: [[-1, 3, True], [6, -1, True], [19, -1, True], [13, 10, True], [26, 3, True], [6, 14, True], [-1, 10, True], [19, 7, True]]
    }
    DoorSortKey = lambda door: (door[0], door[1])

    def makeNewDoors(self):
        self.roomDoors = [ door[:] for door in Room.ShapeDoors.get(self.roomShape, []) ]

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

    def getDesc(rtype, rvariant, rsubtype, width, height, difficulty, weight, shape):
        return f'{rtype}.{rvariant}.{rsubtype} ({width}x{height}) - Difficulty: {difficulty}, Weight: {weight}, Shape: {shape}'

    def setToolTip(self):
        self.setText("{0} - {1}".format(self.roomVariant, self.data(0x100)))
        tip = Room.getDesc(self.roomType, self.roomVariant, self.roomSubvariant, self.roomWidth, self.roomHeight, self.roomDifficulty, self.roomWeight, self.roomShape)
        QListWidgetItem.setToolTip(self, tip)

    def renderDisplayIcon(self):
        """Renders the mini-icon for display."""

        q = QImage()
        q.load('resources/UI/RoomIcons.png')

        i = QIcon(QPixmap.fromImage(q.copy(self.roomType * 16, 0, 16, 16)))

        self.setIcon(i)

    def setRoomBG(self):
        roomType = ['basement', 'cellar',
                    'caves','catacombs',
                    'depths', 'necropolis',
                    'womb', 'utero',
                    'sheol', 'cathedral',
                    'chest', 'dark room',
                    'burning basement', 'flooded caves',
                    'dank depths', 'scarred womb',
                    'blue womb']

        self.roomBG = 1

        for i in range(len(roomType)):
            if roomType[i] in mainWindow.path:
                self.roomBG = i + 1

        c = self.roomType

        if c == 12:
            self.roomBG = 18
        elif c == 2:
            self.roomBG = 19
        elif c == 18:
            self.roomBG = 20
        elif c == 19:
            self.roomBG = 21
        elif c == 9:
            self.roomBG = 22
        elif c == 21:
            self.roomBG = 23
        elif c == 7:
            self.roomBG = 24

        elif c in [10, 11, 13, 14, 17, 22]:
            self.roomBG = 9
        elif c in [15]:
            self.roomBG = 10
        elif c in [20]:
            self.roomBG = 11
        elif c in [3, 16]:
            self.roomBG = 12

        elif c in [8]:
            if self.roomVariant in [0, 11, 15]:
                self.roomBG = 7
            elif self.roomVariant in [1, 12, 16]:
                self.roomBG = 10
            elif self.roomVariant in [2, 13, 17]:
                self.roomBG = 9
            elif self.roomVariant in [3]:
                self.roomBG = 4
            elif self.roomVariant in [4]:
                self.roomBG = 2
            elif self.roomVariant in [5, 19]:
                self.roomBG = 1
            elif self.roomVariant in [6]:
                self.roomBG = 18
            elif self.roomVariant in [7]:
                self.roomBG = 12
            elif self.roomVariant in [8]:
                self.roomBG = 13
            elif self.roomVariant in [9]:
                self.roomBG = 14
            elif self.roomVariant in [14, 18]:
                self.roomBG = 19
            else:
                self.roomBG = 12
        # grave rooms
        elif c == 1 and self.roomVariant > 2 and 'special rooms' in mainWindow.path:
            self.roomBG = 12

    def mirrorX(self):
        # Flip Spawns
        for column in self.roomSpawns:
            column[:self.roomWidth] = column[:self.roomWidth][::-1]

            # Flip Directional Entities
            for row in column:
                for spawn in row:
                    # 40  - Guts 			(1,3)
                    if spawn[0] == 40:
                        if spawn[2] == 1:
                            spawn[2] = 3
                        elif spawn[2] == 3:
                            spawn[2] = 1

                    # 202 - Stone Shooter 	(0,2)
                    elif spawn[0] == 202:
                        if spawn[2] == 0:
                            spawn[2] = 2
                        elif spawn[2] == 2:
                            spawn[2] = 0

                    # 203 - Brim Head 		(0,2)
                    elif spawn[0] == 203:
                        if spawn[2] == 0:
                            spawn[2] = 2
                        elif spawn[2] == 2:
                            spawn[2] = 0

                    # 218 - Wall Hugger 	(1,3)
                    elif spawn[0] == 218:
                        if spawn[2] == 1:
                            spawn[2] = 3
                        elif spawn[2] == 3:
                            spawn[2] = 1

        # To flip, just reverse the signs then offset by room width (-1 for the indexing)
        # Flip Doors
        for door in self.roomDoors:
            door[0] = -door[0] + (self.roomWidth-1)

        # Flip Shape
        if self.roomShape is 9:
            self.roomShape = 10
        elif self.roomShape is 10:
            self.roomShape = 9
        elif self.roomShape is 11:
            self.roomShape = 12
        elif self.roomShape is 12:
            self.roomShape = 11

    def mirrorY(self):
        # To flip, just reverse the signs then offset by room width (-1 for the indexing)

        # Flip Spawns
        self.roomSpawns[:self.roomHeight] = self.roomSpawns[:self.roomHeight][::-1]

        # Flip Directional Entities
        for column in self.roomSpawns:
            for row in column:
                for spawn in row:
                    # 40  - Guts 			(0,2)
                    if spawn[0] == 40:
                        if spawn[2] == 0:
                            spawn[2] = 2
                        elif spawn[2] == 2:
                            spawn[2] = 0

                    # 202 - Stone Shooter 	(1,3)
                    elif spawn[0] == 202:
                        if spawn[2] == 1:
                            spawn[2] = 3
                        elif spawn[2] == 3:
                            spawn[2] = 1

                    # 203 - Brim Head 		(1,3)
                    elif spawn[0] == 203:
                        if spawn[2] == 1:
                            spawn[2] = 3
                        elif spawn[2] == 3:
                            spawn[2] = 1

                    # 218 - Wall Hugger 	(2,4)
                    elif spawn[0] == 218:
                        if spawn[2] == 2:
                            spawn[2] = 4
                        elif spawn[2] == 4:
                            spawn[2] = 2

        # Flip Doors
        for door in self.roomDoors:
            door[1] = -door[1] + (self.roomHeight-1)

        # Flip Shape
        if self.roomShape is 9:
            self.roomShape = 11
        elif self.roomShape is 11:
            self.roomShape = 9
        elif self.roomShape is 10:
            self.roomShape = 12
        elif self.roomShape is 12:
            self.roomShape = 10

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
            painter.drawPixmap(rect.right() / 2 - 12, rect.top() - 2, act.icon().pixmap(24, 24))

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

        self.mirror = False
        self.mirrorY = False
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

        # Type
        Type = QWidgetAction(menu)
        c = QComboBox()

        types= [
            "Null Room", "Normal Room", "Shop", "Error Room", "Treasure Room", "Boss Room",
            "Mini-Boss Room", "Secret Room", "Super Secret Room", "Arcade", "Curse Room", "Challenge Room",
            "Library", "Sacrifice Room", "Devil Room", "Angel Room", "Item Dungeon", "Boss Rush Room",
            "Isaac's Room", "Barren Room", "Chest Room", "Dice Room", "Black Market", "Greed Mode Descent"
        ]

        q = QImage()
        q.load('resources/UI/RoomIcons.png')

        for i, t in enumerate(types):
            c.addItem(QIcon(QPixmap.fromImage(q.copy(i * 16, 0, 16, 16))), t)
        c.setCurrentIndex(self.selectedRoom().roomType)
        c.currentIndexChanged.connect(self.changeType)
        Type.setDefaultWidget(c)
        menu.addAction(Type)

        # Variant
        Variant = QWidgetAction(menu)
        s = QSpinBox()
        s.setRange(0, 65534)
        s.setPrefix("ID - ")

        s.setValue(self.selectedRoom().roomVariant)

        Variant.setDefaultWidget(s)
        s.valueChanged.connect(self.changeVariant)
        menu.addAction(Variant)

        menu.addSeparator()

        # Difficulty
        Difficulty = QWidgetAction(menu)
        dv = QSpinBox()
        dv.setRange(0, 15)
        dv.setPrefix("Difficulty - ")

        dv.setValue(self.selectedRoom().roomDifficulty)

        Difficulty.setDefaultWidget(dv)
        dv.valueChanged.connect(self.changeDifficulty)
        menu.addAction(Difficulty)

        # Weight
        weight = QWidgetAction(menu)
        s = QDoubleSpinBox()
        s.setPrefix("Weight - ")

        s.setValue(self.selectedRoom().roomWeight)

        weight.setDefaultWidget(s)
        s.valueChanged.connect(self.changeWeight)
        menu.addAction(weight)

        # SubVariant
        Subvariant = QWidgetAction(menu)
        sv = QSpinBox()
        sv.setRange(0, 256)
        sv.setPrefix("Sub - ")

        sv.setValue(self.selectedRoom().roomSubvariant)

        Subvariant.setDefaultWidget(sv)
        sv.valueChanged.connect(self.changeSubvariant)
        menu.addAction(Subvariant)

        menu.addSeparator()

        # Room shape
        Shape = QWidgetAction(menu)
        c = QComboBox()

        q = QImage()
        q.load('resources/UI/ShapeIcons.png')

        for shapeName in range(1, 13):
            c.addItem(QIcon(QPixmap.fromImage(q.copy((shapeName - 1) * 16, 0, 16, 16))), str(shapeName))
        c.setCurrentIndex(self.selectedRoom().roomShape - 1)
        c.currentIndexChanged.connect(self.changeSize)
        Shape.setDefaultWidget(c)
        menu.addAction(Shape)

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
    def changeSize(self, shapeIdx):

        # Set the Size - gotta lotta shit to do here
        s = shapeIdx + 1

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

        for y, row in enumerate(self.selectedRoom().roomSpawns):
            for x, entStack in enumerate(row):
                if (x >= w or y >= h) and len(entStack) > 0:
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
        for y, row in enumerate(self.selectedRoom().roomSpawns):
            for x, entStack in enumerate(row):
                for entity in entStack:
                    if x >= w or y >= h: continue

                    e = Entity(x, y, entity[0], entity[1], entity[2], entity[3])
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
    def changeDifficulty(self, var):
        for r in self.selectedRooms():
            r.setDifficulty(var)
            r.setToolTip()
        mainWindow.dirt()
        mainWindow.scene.update()

    #@pyqtSlot(QAction)
    def changeWeight(self, action):
        for r in self.selectedRooms():
            #r.roomWeight = float(action.text())
            r.roomWeight = action
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

        initialPlace = self.list.currentRow()
        self.selectedRoom().setData(100, False)
        self.list.setCurrentItem(None, QItemSelectionModel.ClearAndSelect)

        for room in rooms:
            if self.mirrorY:
                v = 20000
            elif self.mirror:
                v = 10000
            else:
                v = 1

            r = Room(
                deepcopy(room.data(0x100) + ' (copy)'),
                deepcopy([list(door) for door in room.roomDoors]),
                deepcopy(room.roomSpawns),
                deepcopy(room.roomType),
                deepcopy(room.roomVariant+v),
                deepcopy(room.roomSubvariant),
                deepcopy(room.roomDifficulty),
                deepcopy(room.roomWeight),
                deepcopy(room.roomWidth),
                deepcopy(room.roomHeight),
                deepcopy(room.roomShape)
            )

            if self.mirror:
                # Change the name to mirrored.
                flipName = ' (flipped X)'
                if self.mirrorY:
                    flipName = ' (flipped Y)'
                r.setData(0x100, room.data(0x100) + flipName)
                r.setText("{0} - {1}".format(r.roomVariant, room.data(0x100) + flipName))

                # Mirror the room
                if self.mirrorY:
                    r.mirrorY()
                else:
                    r.mirrorX()

            self.list.insertItem(initialPlace + v, r)
            self.list.setCurrentItem(r, QItemSelectionModel.Select)

        mainWindow.dirt()

    def mirrorButtonOn(self):
        self.mirror = True
        self.duplicateRoomButton.setText("Mirror X")

    def mirrorButtonOff(self):
        self.mirror = False
        self.mirrorY = False
        self.duplicateRoomButton.setText("Duplicate")

    def mirrorYButtonOn(self):
        if self.mirror:
            self.mirrorY = True
            self.duplicateRoomButton.setText("Mirror Y")

    def mirrorYButtonOff(self):
        if self.mirror:
            self.mirrorY = False
            self.duplicateRoomButton.setText("Mirror X")

    def exportRoom(self):

        dialogDir = mainWindow.path
        if dialogDir == "":
            dialogDir = findModsPath()

        target, match = QFileDialog.getSaveFileName(self, 'Select a new name or an existing STB', dialogDir, 'Stage Bundle (*.stb)', '', QFileDialog.DontConfirmOverwrite)
        mainWindow.restoreEditMenu()

        if len(target) == 0:
            return

        path = target

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
                if g and g not in self.groups:
                    self.groups[g] = EntityGroupItem(g)

                e = EntityItem(en.get('Name'), en.get('ID'), en.get('Subtype'), en.get('Variant'), en.get('Image'))

                if g != None:
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

        groups = ["Pickups", "Enemies", "Bosses", "Stage", "Collect" ]
        if settings.value('ModAutogen') == '1':
            groups.append("Mods")

        for group in groups:

            listView = EntityList()

            listView.setModel(EntityGroupModel(group))
            listView.model().view = listView

            listView.clicked.connect(self.objSelected)

            if group == "Bosses":
                listView.setIconSize(QSize(52, 52))

            if group == "Collect":
                listView.setIconSize(QSize(32, 64))

            self.tabs.addTab(listView, group)

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


class ReplaceDialog(QDialog):

    class EntSpinners(QWidget):

        def __init__(self):
            super(QWidget, self).__init__()
            layout = QFormLayout()

            self.type = QSpinBox()
            self.type.setRange(1, 2**31-1)
            self.variant = QSpinBox()
            self.variant.setRange(-1, 2**31-1)
            self.subtype = QSpinBox()
            self.subtype.setRange(-1, 2**8-1)

            layout.addRow('&Type:', self.type)
            layout.addRow('&Variant:', self.variant)
            layout.addRow('&Subtype:', self.subtype)

            self.entity = Entity.Info(0,0,0,0,0,0,changeAtStart=False)

            self.type.valueChanged.connect(self.resetEnt)
            self.variant.valueChanged.connect(self.resetEnt)
            self.subtype.valueChanged.connect(self.resetEnt)

            self.setLayout(layout)

        def getEnt(self):
            return (self.type.value(),
                    self.variant.value(),
                    self.subtype.value())

        def setEnt(self, t, v, s):
            self.type.setValue(t)
            self.variant.setValue(v)
            self.subtype.setValue(s)
            self.entity.changeTo(t, v, s)

        valueChanged = pyqtSignal()

        def resetEnt(self):
            self.entity.changeTo(*self.getEnt())
            self.valueChanged.emit()

    def __init__(self):
        super(QDialog, self).__init__()
        self.setWindowTitle("Replace Entities")
    
        layout = QVBoxLayout()
    
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
    
        cols = QHBoxLayout()

        def genEnt(name):
            spinners = ReplaceDialog.EntSpinners()
            info = QVBoxLayout()
            info.addWidget(QLabel(name))
            icon = QLabel()
            spinners.valueChanged.connect(lambda: icon.setPixmap(spinners.entity.pixmap))
            info.addWidget(icon)
            infoWidget = QWidget()
            infoWidget.setLayout(info)
            return infoWidget, spinners

        fromInfo, self.fromEnt = genEnt("From")
        toInfo, self.toEnt = genEnt("To")

        selection = mainWindow.scene.selectedItems()
        if len(selection) > 0:
            selection = selection[0].entity
            self.fromEnt.setEnt(int(selection.Type), int(selection.Variant), int(selection.Subtype))
        else:
            self.fromEnt.resetEnt()
    
        paint = mainWindow.editor.objectToPaint
        if paint:
            self.toEnt.setEnt(int(paint.ID), int(paint.variant), int(paint.subtype))
        else:
            self.toEnt.resetEnt()

        cols.addWidget(fromInfo)
        cols.addWidget(self.fromEnt)
        cols.addWidget(toInfo)
        cols.addWidget(self.toEnt)

        layout.addLayout(cols)
        layout.addWidget(buttonBox)
        self.setLayout(layout)


class HooksDialog(QDialog):

    class HookItem(QListWidgetItem):
        def __init__(self, text, setting, tooltip):
            super(QListWidgetItem, self).__init__(text)
            self.setWindowTitle("Set Hooks")
            self.setToolTip(tooltip)
            self.setting = setting

        @property
        def val(self):
            settings =  QSettings('settings.ini', QSettings.IniFormat)
            return settings.value(self.setting, [])

        @val.setter
        def val(self, v):
            settings =  QSettings('settings.ini', QSettings.IniFormat)
            res = v
            settings.setValue(self.setting, res)

    def __init__(self, parent):
        super(QDialog, self).__init__(parent)

        self.layout = QHBoxLayout()

        hookTypes = [
            ('On Save File', 'HooksSave', 'Runs on saved room files whenever a full save is performed'),
            ('On Test Room', 'HooksTest', 'Runs on output room xmls when preparing to test the current room')
        ]

        self.hooks = QListWidget()
        for hook in hookTypes:
            self.hooks.addItem(HooksDialog.HookItem(*hook))
        self.layout.addWidget(self.hooks)

        pane = QVBoxLayout()
        pane.setContentsMargins(0,0,0,0)
        paneWidget = QWidget()
        paneWidget.setLayout(pane)

        self.content = QListWidget()
        pane.addWidget(self.content)

        addButton = QPushButton("Add")
        editButton = QPushButton("Edit")
        deleteButton = QPushButton("Delete")

        buttons = QHBoxLayout()
        buttons.addWidget(addButton)
        buttons.addWidget(editButton)
        buttons.addWidget(deleteButton)
        pane.addLayout(buttons)
        
        self.layout.addWidget(paneWidget, 1)

        self.hooks.currentItemChanged.connect(self.displayHook)

        addButton.clicked.connect(self.addPath)
        editButton.clicked.connect(self.editPath)
        deleteButton.clicked.connect(self.deletePath)

        self.setLayout(self.layout)

    def contentPaths(self):
        return [ self.content.item(i).text() for i in range(self.content.count()) ]

    def setPaths(self, val):
        self.content.clear()
        self.content.addItems(val)

    def displayHook(self, new, old):
        if old: old.val = self.contentPaths()
        self.setPaths(new.val)

    def insertPath(self, path=None):
        path = path or findModsPath()

        target, _ = QFileDialog.getOpenFileName(self, 'Select script', os.path.normpath(path), 'All files (*)')
        return target

    def addPath(self):
        path = self.insertPath()
        if path != '':
            self.content.addItem(path)

    def editPath(self):
        item = self.content.currentItem()
        if not item: return
            
        path = self.insertPath(item.text())
        if path != '':
            item.setText(path)

    def deletePath(self):
        if self.content.currentItem():
            self.content.takeItem(self.content.currentRow())

    def closeEvent(self, evt):
        curr = self.hooks.currentItem()
        if curr: curr.val = self.contentPaths()
        QWidget.closeEvent(self, evt)

########################
#      Main Window     #
########################

class MainWindow(QMainWindow):

    def keyPressEvent(self, event):
        QMainWindow.keyPressEvent(self, event)
        if event.key() == Qt.Key_Alt:
            self.roomList.mirrorButtonOn()
        if event.key() == Qt.Key_Shift:
            self.roomList.mirrorYButtonOn()

    def keyReleaseEvent(self, event):
        QMainWindow.keyReleaseEvent(self, event)
        if event.key() == Qt.Key_Alt:
            self.roomList.mirrorButtonOff()
        if event.key() == Qt.Key_Shift:
            self.roomList.mirrorYButtonOff()

    defaultMapsDict = {
        "Special Rooms": "00.special rooms.stb",
        "Basement": "01.basement.stb",
        "Cellar": "02.cellar.stb",
        "Burning Basement": "03.burning basement.stb",
        "Caves": "04.caves.stb",
        "Catacombs": "05.catacombs.stb",
        "Flooded Caves": "06.flooded caves.stb",
        "Depths": "07.depths.stb",
        "Necropolis": "08.necropolis.stb",
        "Dank Depths": "09.dank depths.stb",
        "Womb": "10.womb.stb",
        "Utero": "11.utero.stb",
        "Scarred Womb": "12.scarred womb.stb",
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
        super(QMainWindow, self).__init__()

        self.setWindowTitle('Basement Renovator')
        self.setIconSize(QSize(16, 16))

        self.dirty = False
        self.wroteModFolder = False

        self.scene = RoomScene()
        self.clipboard = None

        self.editor = RoomEditorWidget(self.scene)
        self.setCentralWidget(self.editor)

        self.setupDocks()
        self.setupMenuBar()

        self.setGeometry(100, 500, 1280, 600)

        # Restore Settings
        if not settings.value('GridEnabled', True) or settings.value('GridEnabled', True) == 'false': self.switchGrid()
        if not settings.value('StatusEnabled', True) or settings.value('StatusEnabled', True) == 'false': self.switchInfo()
        if not settings.value('BitfontEnabled', True) or settings.value('BitfontEnabled', True) == 'false': self.switchBitFont()

        self.restoreState(settings.value('MainWindowState', self.saveState()), 0)
        self.restoreGeometry(settings.value('MainWindowGeometry', self.saveGeometry()))

        self.resetWindow = {"state" : self.saveState(), "geometry" : self.saveGeometry()}

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
        self.fh = f.addAction('Set Resources Path',   self.setDefaultResourcesPath, QKeySequence("Ctrl+Shift+P"))
        self.fi = f.addAction('Reset Resources Path', self.resetResourcesPath, QKeySequence("Ctrl+Shift+R"))
        f.addSeparator()
        self.fj = f.addAction('Set Hooks', self.showHooksMenu)
        self.fl = f.addAction('Autogenerate mod content (discouraged)', self.toggleModAutogen)
        self.fl.setCheckable(True)
        self.fl.setChecked(settings.value('ModAutogen') == '1')
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
        self.e.addSeparator()
        self.eg = self.e.addAction('Bulk Replace Entities',       self.showReplaceDialog, QKeySequence("Ctrl+R"))
        self.eg = self.e.addAction('Sort Rooms by ID',            self.sortRoomIDs)
        self.eg = self.e.addAction('Sort Rooms by Name',          self.sortRoomNames)
        self.eg = self.e.addAction('Recompute Room IDs',          self.recomputeRoomIDs)

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
        self.ra = r.addAction('Test Current Room - InstaPreview',  self.testMapInstapreview, QKeySequence("Ctrl+P"))
        self.ra = r.addAction('Test Current Room - Replace Stage', self.testMap,             QKeySequence("Ctrl+T"))
        self.ra = r.addAction('Test Current Room - Replace Start', self.testStartMap,        QKeySequence("Ctrl+Shift+T"))

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
        room = room or self.roomList.selectedRoom()
        if not room: return

        eList = self.scene.items()

        spawns = [[[] for y in range(26)] for x in range(14)]
        doors = []

        for e in eList:
            if isinstance(e, Door):
                doors.append(e.doorItem)

            elif isinstance(e, Entity):
                spawns[e.entity.y][e.entity.x].append([e.entity.Type, e.entity.Variant, e.entity.Subtype, e.entity.weight])

        room.roomSpawns = spawns
        room.roomDoors = doors

    def closeEvent(self, event):
        """Handler for the main window close event"""

        if self.checkDirty():
            event.ignore()
        else:
            settings = QSettings('settings.ini', QSettings.IniFormat)

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

        if not current: return

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
        for y, row in enumerate(current.roomSpawns):
            for x, entStack in enumerate(row):
                for entity in entStack:
                    e = Entity(x, y, entity[0], entity[1], entity[2], entity[3])
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
            item.setData(int(entity.ID), int(entity.variant), int(entity.subtype))
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

    def setDefaultResourcesPath(self):
        settings = QSettings('settings.ini', QSettings.IniFormat)
        if not settings.contains("ResourceFolder"):
            settings.setValue("ResourceFolder", self.findResourcePath())
        resPath = settings.value("ResourceFolder")
        resPathDialog = QFileDialog()
        resPathDialog.setFilter(QDir.Hidden)
        newResPath = QFileDialog.getExistingDirectory(self, "Select directory", resPath)

        if newResPath != "":
            settings.setValue("ResourceFolder", newResPath)

    def resetResourcesPath(self):
        settings = QSettings('settings.ini', QSettings.IniFormat)
        settings.remove("ResourceFolder")
        settings.setValue("ResourceFolder", self.findResourcePath())

    def showHooksMenu(self):
        hooks = HooksDialog(self)
        hooks.show()

    def toggleModAutogen(self):
        settings = QSettings('settings.ini', QSettings.IniFormat)
        settings.setValue('ModAutogen', settings.value('ModAutogen') == '1' and '0' or '1')

    def openMapDefault(self):
        if self.checkDirty(): return

        selectedMap, selectedMapOk = QInputDialog.getItem(self, "Map selection", "Select floor", self.defaultMapsOrdered, 0, False)
        self.restoreEditMenu()

        if not selectedMapOk: return

        mapFileName = self.defaultMapsDict[selectedMap]
        roomPath = os.path.join(os.path.expanduser(self.findResourcePath()), "rooms", mapFileName)

        if not QFile.exists(roomPath):
            self.setDefaultResourcesPath()
            roomPath = os.path.join(os.path.expanduser(self.findResourcePath()), "rooms", mapFileName)
            if not QFile.exists(roomPath):
                QMessageBox.warning(self, "Error", "Failed opening stage. Make sure that the resources path is set correctly (see File menu) and that the proper STB file is present in the rooms directory.")
                return

        self.openWrapper(roomPath)

    def getRecentFolder(self):
        startPath = ""

        settings = QSettings('settings.ini', QSettings.IniFormat)

        # Get the folder containing the last open file if you can
        # and it's not a default stage
        stagePath = os.path.join(settings.value("ResourceFolder", ''), 'rooms')
        recent = settings.value("RecentFiles", [])
        for recPath in recent:
            lastPath, file = os.path.split(recPath)
            if lastPath != stagePath:
                startPath = lastPath
                break

        # Get the mods folder if you can, no sense looking in rooms for explicit open
        if startPath == "":
            modPath = findModsPath()
            if os.path.isdir(modPath):
                startPath = modPath

        return os.path.expanduser(startPath)

    def updateRecent(self, path):
        recent = settings.value("RecentFiles", [])
        while recent.count(path) > 0:
            recent.remove(path)

        recent.insert(0, path)
        while len(recent) > 10:
            recent.pop()

        settings.setValue("RecentFiles", recent)
        self.setupFileMenuBar()

    def openMap(self):
        if self.checkDirty(): return

        target = QFileDialog.getOpenFileName(
            self, 'Open Map', self.getRecentFolder(), 'Stage Binary (*.stb)')
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

    def open(self, path=None, addToRecent=True):
        path = path or self.path

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

        seenSpawns = {}
        for room in range(rooms):

            # Room Type, Room Variant, Subtype, Difficulty, Length of Room Name String
            roomData = struct.unpack_from('<IIIBH', stb, off)
            rtype, rvariant, rsubtype, difficulty, nameLen = roomData
            off += 0xF
            # print ("Room Data: {0}".format(roomData))

            # Room Name
            roomName = struct.unpack_from('<{0}s'.format(nameLen), stb, off)[0].decode()
            off += nameLen
            #print ("Room Name: {0}".format(roomName))

            # Weight, width, height, shape, number of doors, number of entities
            entityTable = struct.unpack_from('<fBBBBH', stb, off)
            rweight, width, height, shape, numDoors, numEnts = entityTable
            off += 0xA
            #print ("Entity Table: {0}".format(entityTable))

            doors = []
            for door in range(numDoors):
                # X, Y, exists
                doorX, doorY, exists = struct.unpack_from('<hh?', stb, off)
                doors.append([ doorX, doorY, exists ])
                off += 5

            def sameDoorLocs(a, b):
                for ad, bd in zip(a, b):
                    if ad[0] != bd[0] or ad[1] != bd[1]:
                        return False
                return True

            def getRoomPrefix():
                return Room.getDesc(rtype, rvariant, rsubtype, width, height, difficulty, rweight, shape)

            normalDoors = sorted(Room.ShapeDoors[shape], key=Room.DoorSortKey)
            sortedDoors = sorted(doors, key=Room.DoorSortKey)
            if len(normalDoors) != numDoors or not sameDoorLocs(normalDoors, sortedDoors):
                print (f'Invalid doors in room {getRoomPrefix()}: Expected {normalDoors}, Got {sortedDoors}')

            spawns = [[[] for y in range(26)] for x in range(14)]
            for entity in range(numEnts):
                # x, y, number of entities at this position
                ex, ey, stackedEnts = struct.unpack_from('<hhB', stb, off)
                off += 5

                if ex < 0 or ex >= width or ey < 0 or ey >= height:
                    print (f'Found entity with out of bounds spawn loc in room {getRoomPrefix()}: {ex}, {ey}')

                for spawn in range(stackedEnts):
                    #  type, variant, subtype, weight
                    etype, evariant, esubtype, eweight = struct.unpack_from('<HHHf', stb, off)
                    spawns[ey][ex].append([ etype, evariant, esubtype, eweight ])

                    if (etype, esubtype, evariant) not in seenSpawns:
                        global entityXML
                        en = entityXML.find(f"entity[@ID='{etype}'][@Subtype='{esubtype}'][@Variant='{evariant}']")
                        if en == None or en.get('Invalid') == '1':
                            print(f"Room has invalid entity '{en is None and 'UNKNOWN' or en.get('Name')}'! ({etype}.{evariant}.{esubtype})")
                        seenSpawns[(etype, esubtype, evariant)] = en == None or en.get('Invalid') == '1'

                    off += 0xA

            r = Room(roomName, doors, spawns, rtype, rvariant, rsubtype, difficulty, rweight, width, height, shape)
            ret.append(r)

        # Update recent files
        if addToRecent:
            self.updateRecent(path)

        return ret

    def saveMap(self, forceNewName=False):
        target = self.path

        if target == '' or forceNewName:
            dialogDir = target == '' and self.getRecentFolder() or os.path.dirname(target)
            target = QFileDialog.getSaveFileName(self, 'Save Map', dialogDir, 'Stage Binary (*.stb)')
            self.restoreEditMenu()

            if len(target) == 0:
                return

            self.path = target[0]
            self.updateTitlebar()

        try:
            self.save(self.roomList.getRooms())
        except Exception as e:
            print(e)
            QMessageBox.warning(self, "Error", "Saving failed. Try saving to a new file instead.")

        self.clean()
        self.roomList.changeFilter()

    def saveMapAs(self):
        self.saveMap(True)

    def save(self, rooms, path=None, updateRecent=True):
        path = path or self.path

        self.storeEntityList()

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

        with open(path, 'wb') as stb:
            stb.write(out)

        if updateRecent:
            self.updateRecent(path)

            # if a save doesn't update the recent list, it's probably not a real save
            # so only do hooks in this case
            settings = QSettings('settings.ini', QSettings.IniFormat)
            saveHooks = settings.value('HooksSave')
            if saveHooks:
                stbPath = os.path.abspath(path)
                for hook in saveHooks:
                    path, name = os.path.split(hook)
                    try:
                        subprocess.run([hook, stbPath, '--save'], cwd = path, timeout=60)
                    except Exception as e:
                        print('Save hook failed! Reason:', e)


    def replaceEntities(self, replaced, replacement):
        self.storeEntityList()

        numEnts = 0
        numRooms = 0

        def checkEq(a, b):
            return a[0] == b[0] \
              and (b[1] < 0 or a[1] == b[1]) \
              and (b[2] < 0 or a[2] == b[2])

        def fixEnt(a, b):
            a[0] = b[0]
            if b[1] >= 0: a[1] = b[1]
            if b[2] >= 0: a[2] = b[2]

        for i in range(self.roomList.list.count()):
            currRoom = self.roomList.list.item(i)

            n = 0
            for row in currRoom.roomSpawns:
                for entStack in row:
                    for ent in entStack:
                        if checkEq(ent, replaced):
                            fixEnt(ent, replacement)
                            n += 1
            if n > 0:
                numRooms += 1
                numEnts += n

        room = self.roomList.selectedRoom()
        if room:
            self.handleSelectedRoomChanged(room, None)
            self.scene.update()

        self.dirt()
        QMessageBox.information(None, "Replace",
            numEnts > 0 and f"Replaced {numEnts} entities in {numRooms} rooms"
                        or "No entities to replace!")

    def sortRoomIDs(self):
        self.sortRoomsByKey(lambda x: (x.roomType,x.roomVariant))

    def sortRoomNames(self):
        self.sortRoomsByKey(lambda x: (x.roomType,x.data(0x100),x.roomVariant))

    def sortRoomsByKey(self, key):
        roomList = self.roomList.list
        selection = roomList.currentItem()
        roomList.setCurrentItem(None, QItemSelectionModel.ClearAndSelect)

        rooms = sorted([ roomList.takeItem(roomList.count() - 1) for x in range(roomList.count()) ], key=key)

        for room in rooms:
            roomList.addItem(room)

        self.dirt()
        roomList.setCurrentItem(selection, QItemSelectionModel.ClearAndSelect)
        roomList.scrollToItem(selection)


    def recomputeRoomIDs(self):
        roomsByType = {}
        
        roomList = self.roomList.list

        for i in range(roomList.count()):
            room = roomList.item(i)

            if room.roomType not in roomsByType:
                roomsByType[room.roomType] = room.roomVariant

            room.roomVariant = roomsByType[room.roomType]
            room.setToolTip()

            roomsByType[room.roomType] += 1

        self.dirt()
        self.scene.update()

    #@pyqtSlot()
    def screenshot(self):
        fn = QFileDialog.getSaveFileName(self, 'Choose a new filename', 'untitled.png', 'Portable Network Graphics (*.png)')[0]
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

    def makeTestMod(self):
        modFolder = findModsPath()

        name = 'basement-renovator-helper'
        folder = os.path.join(modFolder, name)
        roomPath = os.path.join(folder, 'resources', 'rooms')

        if not mainWindow.wroteModFolder and os.path.isdir(folder):
            try:
                shutil.rmtree(folder)
            except Exception as e:
                print('Error clearing old mod data: ', e)

        # delete the old files
        if os.path.isdir(folder):
            dis = os.path.join(folder, 'disable.it')
            if os.path.isfile(dis): os.unlink(dis)

            for f in os.listdir(roomPath):
                f = os.path.join(roomPath, f)
                try:
                    if os.path.isfile(f): os.unlink(f)
                except:
                    pass
        # otherwise, make it fresh
        else:
            try:
                shutil.copytree('./resources/modtemplate', folder)
                os.makedirs(roomPath)
                mainWindow.wroteModFolder = True
            except Exception as e:
                print('Could not copy mod template!', e)
                return '', e

        return folder, roomPath

    def writeTestData(self, folder, testType, floorInfo, testRoom):
        with open(os.path.join(folder, 'roomTest.lua'), 'w') as testData:

            testData.write(f'''return {{
    TestType = '{testType}',
    Stage = {floorInfo[1]},
    StageType = {floorInfo[2]},
    Type = {testRoom.roomType},
    Variant = {testRoom.roomVariant},
    Subtype = {testRoom.roomSubvariant},
    Shape = {testRoom.roomShape}
}}
''')

    # Test by replacing the rooms in the relevant floor
    def testMap(self):
        def setup(modPath, roomsPath, floorInfo, room):
            if floorInfo[1] == 9:
                QMessageBox.warning(self, "Error", "Blue Womb cannot be tested with Stage Replacement, since it doesn't have normal room generation.")
                raise

            # Set the selected room to max weight
            testRoom = Room(room.data(0x100), room.roomDoors, room.roomSpawns, 1, room.roomVariant, room.roomSubvariant, 1, 1000.0, room.roomWidth, room.roomHeight, room.roomShape)

            # Make a new STB with a blank room
            padMe = True
            if testRoom.roomShape not in [2, 3, 5, 7]: # Always pad these rooms
                padMe = False
                for door in testRoom.roomDoors:
                    if not door[2]:
                        padMe = True

            # Needs a padded room
            newRooms = [testRoom]
            if padMe:
                newRooms.append(Room(difficulty=10, weight=0.1))

            path = os.path.join(roomsPath, floorInfo[0])
            self.save(newRooms, path, updateRecent=False)

            # Prompt to restore backup
            message = ""
            if padMe:
                message += "As the room has a non-standard shape and/or missing doors, the floor is forced to XL to try and make it spawn. You may have to reset a few times for your room to appear.\n\n"
            message += 'This method will not work properly if you have other mods that add rooms to the floor.\n\n'

            return [], testRoom, message
        
        self.testMapCommon('StageReplace', setup)

    # Test by replacing the starting room
    def testStartMap(self):
        def setup(modPath, roomsPath, floorInfo, testRoom):
            # Sanity check for 1x1 room
            if testRoom.roomShape in [2, 7, 9] :
                QMessageBox.warning(self, "Error", "Room shapes 2 and 7 (Long and narrow) and 9 (L shaped with upper right corner missing) can't be tested as the Start Room.")
                raise

            resourcePath = self.findResourcePath()
            if resourcePath == "":
                QMessageBox.warning(self, "Error", "The resources folder could not be found. Please try reselecting it.")
                raise

            roomPath = os.path.join(resourcePath, "rooms", "00.special rooms.stb")

            # Parse the special rooms, replace the spawns
            if not QFile.exists(roomPath):
                QMessageBox.warning(self, "Error", "Missing 00.special rooms.stb from resources. Please unpack your resource files.")
                raise

            startRoom = None
            rooms = self.open(roomPath, False)
            for room in rooms:
                if "Start Room" in room.data(0x100):
                    room.roomHeight = testRoom.roomHeight
                    room.roomWidth  = testRoom.roomWidth
                    room.roomShape  = testRoom.roomShape
                    room.roomSpawns = testRoom.roomSpawns
                    startRoom = room
                    break

            if not startRoom:
                QMessageBox.warning(self, "Error", "00.special rooms.stb has been tampered with, and is no longer a valid STB file.")
                raise

            path = os.path.join(roomsPath, "00.special rooms.stb")

            # Resave the file
            self.save(rooms, path, updateRecent=False)

            return [], startRoom, ""

        self.testMapCommon('StartingRoom', setup)

    # Test by launching the game directly into the test room, skipping the menu
    def testMapInstapreview(self):
        def setup(modPath, roomPath, floorInfo, room):
            testfile = "instapreview.xml"
            path = Path(modPath) / testfile
            path = path.resolve()

            self.writeRoomXML(path, room, isPreview = True)

            return [ f"--load-room={path}",
                     f"--set-stage={floorInfo[1]}",
                     f"--set-stage-type={floorInfo[2]}" ], None, ""

        self.testMapCommon('InstaPreview', setup)

    def findExecutablePath(self):
        installPath = findInstallPath()
        if len(installPath) > 0:
            exeName = "isaac-ng.exe"
            if QFile.exists(os.path.join(installPath, "isaac-ng-rebirth.exe")):
                exeName = "isaac-ng-rebirth.exe"
            return os.path.join(installPath, exeName)

    def findResourcePath(self):

        resourcesPath = ''

        if QFile.exists(settings.value('ResourceFolder')):
            resourcesPath = settings.value('ResourceFolder')

        else:
            installPath = findInstallPath()

            if len(installPath) != 0:
                resourcesPath = os.path.join(installPath, 'resources')
            # Fallback Resource Folder Locating
            else:
                resourcesPathOut = QFileDialog.getExistingDirectory(self, 'Please Locate The Binding of Isaac: Afterbirth+ Resources Folder')
                if not resourcesPathOut:
                    QMessageBox.warning(self, "Error", "Couldn't locate resources folder and no folder was selected.")
                    return
                else:
                    resourcesPath = resourcesPathOut
                if resourcesPath == "":
                    QMessageBox.warning(self, "Error", "Couldn't locate resources folder and no folder was selected.")
                    return
                if not QDir(resourcesPath).exists:
                    QMessageBox.warning(self, "Error", "Selected folder does not exist or is not a folder.")
                    return
                if not QDir(os.path.join(resourcesPath, "rooms")).exists:
                    QMessageBox.warning(self, "Error", "Could not find rooms folder in selected directory.")
                    return

            # Looks like nothing was selected
            if len(resourcesPath) == 0:
                QMessageBox.warning(self, "Error", "Could not find The Binding of Isaac: Afterbirth+ Resources folder (%s)" % resourcesPath)
                return ''

            settings.setValue('ResourceFolder', resourcesPath)

        # Make sure 'rooms' exists
        roomsdir = os.path.join(resourcesPath, "rooms")
        if not QDir(roomsdir).exists:
            os.mkdir(roomsdir)
        return resourcesPath

    def killIsaac(self):
        for p in psutil.process_iter():
            try:
                if 'isaac' in p.name().lower():
                    p.terminate()
            except:
                # This is totally kosher, I'm just avoiding zombies.
                pass

    def writeRoomXML(self, path, room, isPreview = False):
        includeRooms = not isPreview
        with open(path, 'w') as out:
            if includeRooms:
                #out.write('<?xml version="1.0"?>\n<rooms>\n') # TODO restore this when BR has its own xml converter
                out.write('<stage>\n')
            # Room header
            out.write('<room type="%d" variant="%d" subtype="%d" name="%s" difficulty="%d" weight="%g" width="%d" height="%d" shape="%d">\n' % (
                room.roomType, room.roomVariant, room.roomSubvariant, room.text(), room.roomDifficulty,
                room.roomWeight, room.roomWidth, room.roomHeight, room.roomShape
            ))

            # Doors
            for x, y, exists in room.roomDoors:
                out.write(f'\t<door x="{x}" y="{y}" exists="{exists and "true" or "false"}" />\n')

            # Spawns
            for y, row in enumerate(room.roomSpawns):
                for x, entStack in enumerate(row):
                    if len(entStack) == 0: continue

                    out.write(f'\t<spawn x="{x}" y="{y}">\n')
                    for t, v, s, weight in entStack:
                        out.write(f'\t\t<entity type="{t}" variant="{v}" subtype="{s}" weight="{weight}" />\n')
                    out.write('\t</spawn>\n')

            out.write('</room>\n')
            if includeRooms:
                #out.write('</rooms>\n') # TODO same here
                out.write('</stage>\n')

    def testMapCommon(self, testType, setupFunc):
        room = self.roomList.selectedRoom()
        if not room:
            QMessageBox.warning(self, "Error", "No room was selected to test.")
            return

        # Floor type
        roomType = [
            # filename, stage, stage type
            ('01.basement.stb', 1, 0),
            ('02.cellar.stb', 1, 1),
            ('03.burning basement.stb', 1, 2),
            ('04.caves.stb', 3, 0),
            ('05.catacombs.stb', 3, 1),
            ('06.flooded caves.stb', 3, 2),
            ('07.depths.stb', 5, 0),
            ('08.necropolis.stb', 5, 1),
            ('09.dank depths.stb', 5, 2),
            ('10.womb.stb', 7, 0),
            ('11.utero.stb', 7, 1),
            ('12.scarred womb', 7, 2),
            ('13.blue womb.stb', 9, 0),
            ('14.sheol.stb', 10, 0),
            ('15.cathedral.stb', 10, 1),
            ('16.dark room.stb', 11, 0),
            ('17.chest.stb', 11, 1),
            # TODO update when repentance comes out
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

        modPath, roomPath = self.makeTestMod()
        if modPath == "":
            QMessageBox.warning(self, "Error", "The basement renovator mod folder could not be copied over: " + str(roomPath))
            return

        # Dirtify to prevent overwriting and then quitting without saving
        self.dirt()
        # Ensure that the room data is up to date before writing
        self.storeEntityList(room)

        # Call unique code for the test method
        launchArgs, extraMessage = None, None
        try:
            # setup raises an exception if it can't continue
            launchArgs, roomOverride, extraMessage = setupFunc(modPath, roomPath, floorInfo, room) or ([], None, '')
        except Exception as e:
            print('Problem setting up test:', e)
            return

        room = roomOverride or room
        self.writeTestData(modPath, testType, floorInfo, room)

        testfile = 'testroom.xml'
        testPath = Path(modPath) / testfile
        testPath = testPath.resolve()
        self.writeRoomXML(testPath, room)

         # Trigger test hooks
        settings = QSettings('settings.ini', QSettings.IniFormat)
        testHooks = settings.value('HooksTest')
        if testHooks:
            tp = str(testPath)
            for hook in testHooks:
                wd, script = os.path.split(hook)
                try:
                    subprocess.run([hook, tp, '--test'], cwd = wd, timeout=30)
                except Exception as e:
                    print('Test hook failed! Reason:', e)

        # Launch Isaac
        installPath = findInstallPath()
        try:
            if installPath == '':
                args = ' '.join(map(lambda x: ' ' in x and f'"{x}"' or x, launchArgs))
                webbrowser.open(f'steam://rungameid/250900//{urllib.parse.quote(args)}')
            else:
                exePath = self.findExecutablePath()
                if not QFile.exists(exePath):
                    QMessageBox.warning(self, "Error", "The game executable could not be found in your install path! You may have the wrong directory, reconfigure in settings.ini")
                    return

                subprocess.run([exePath] + launchArgs, cwd = installPath)
        except Exception as e:
             QMessageBox.warning(self, "Error", f'Failed to test with {testType}: {e}')
             return

        # Prompt to disable mod and perform cleanup
        # for some reason, if the dialog blocks on the button click,
        # e.g. QMessageBox.information() or msg.exec(), isaac crashes on launch.
        # This is probably a bug in python or Qt
        msg = QMessageBox(QMessageBox.Information,
            'Disable BR', extraMessage +
            'Press "OK" when done testing to disable the BR helper mod.'
            , QMessageBox.Ok, self)

        def fin(button):
            result = msg.standardButton(button)
            if result == QMessageBox.Ok:
                if os.path.isdir(modPath):
                    with open(os.path.join(modPath, 'disable.it'), 'w'):
                        pass

            self.killIsaac()

        msg.buttonClicked.connect(fin)
        msg.open()

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
            self.clipboard.append([item.entity.x, item.entity.y, item.entity.Type, item.entity.Variant, item.entity.Subtype, item.entity.weight])

    #@pyqtSlot()
    def cut(self):
        self.clipboard = []
        for item in self.scene.selectedItems():
            self.clipboard.append([item.entity.x, item.entity.y, item.entity.Type, item.entity.Variant, item.entity.Subtype, item.entity.weight])
            item.remove()

    #@pyqtSlot()
    def paste(self):
        if not self.clipboard: return

        self.scene.clearSelection()
        for item in self.clipboard:
            i = Entity(*item)
            self.scene.addItem(i)

        self.dirt()

    def showReplaceDialog(self):
        replaceDialog = ReplaceDialog()
        if replaceDialog.exec() != QDialog.Accepted: return

        self.replaceEntities(replaceDialog.fromEnt.getEnt(), replaceDialog.toEnt.getEnt())

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

    # Application
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('resources/UI/BasementRenovator.png'))

    cmdParser = QCommandLineParser()
    cmdParser.setApplicationDescription('Basement Renovator is a room editor for The Binding of Isaac: Afterbirth[+]')
    cmdParser.addHelpOption()

    cmdParser.process(app)

    settings = QSettings('settings.ini', QSettings.IniFormat)

    # XML Globals
    entityXML = getEntityXML()
    if settings.value('DisableMods') != '1':
        loadMods(settings.value('ModAutogen') == '1', findInstallPath(), settings.value('ResourceFolder', ''))

    mainWindow = MainWindow()
    recent = settings.value("RecentFiles", [])
    if len(recent) > 0 and os.path.exists(recent[0]):
        mainWindow.openWrapper(recent[0])

    mainWindow.show()

    sys.exit(app.exec())
