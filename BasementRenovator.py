#!/usr/bin/python3

###########################################
#
#    Binding of Isaac: Rebirth Stage Editor
# 		by Colin Noga
# 		   Chronometrics / Tempus
#
#
#
# 		UI Elements
# 			Main Scene: Click to select, right click to paint. Auto resizes to match window zoom. Renders background.
# 			Entity: A QGraphicsItem to be added to the scene for drawing.
# 			Room List: Shows a list of rooms with mini-renders as icons. Needs add and remove buttons. Should drag and drop re-sort.
# 			Entity Palette: A palette from which to choose entities to draw.
# 			Properties: Possibly a contextual menu thing?
#
#
#
#   Afterbirth Todo:
# 		Fix up Rebirth/Afterbirth detection
#
# 	Low priority
# 		Clear Corner Rooms Grid
# 		Fix icon for win_setup.py
# 		Bosscolours for the alternate boss entities
#

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from copy import deepcopy

import traceback
import sys
import os
import subprocess
import platform
import webbrowser
import re
import shutil
import datetime
import random
import urllib.parse
import urllib.request
from pathlib import Path
import xml.etree.cElementTree as ET
import psutil

import src.roomconvert as StageConvert
from src.core import Room as RoomData, Entity as EntityData
from src.lookup import EntityLookup, MainLookup
import src.anm2 as anm2
from src.constants import *
from src.util import *

########################
#       XML Data       #
########################


def getGameVersion():
    """
    Returns the current compatibility mode, and the sub version if it exists
    """
    # default mode if not set
    mode = settings.value("CompatibilityMode", "Repentance")

    return mode


STEAM_PATH = None


def getSteamPath():
    global STEAM_PATH
    if not STEAM_PATH:
        STEAM_PATH = QSettings(
            "HKEY_CURRENT_USER\\Software\\Valve\\Steam", QSettings.NativeFormat
        ).value("SteamPath")
    return STEAM_PATH


def findInstallPath():
    version = getGameVersion()
    if version == "Antibirth" and settings.value("AntibirthPath"):
        return settings.value("AntibirthPath")

    installPath = ""
    cantFindPath = False

    if QFile.exists(settings.value("InstallFolder")):
        installPath = settings.value("InstallFolder")

    else:
        # Windows path things
        if "Windows" in platform.system():
            basePath = getSteamPath()
            if not basePath:
                cantFindPath = True
            else:
                installPath = os.path.join(
                    basePath, "steamapps", "common", "The Binding of Isaac Rebirth"
                )
                if not QFile.exists(installPath):
                    cantFindPath = True

                    libconfig = os.path.join(
                        basePath, "steamapps", "libraryfolders.vdf"
                    )
                    if os.path.isfile(libconfig):
                        libLines = list(open(libconfig, "r"))
                        matcher = re.compile(r'"\d+"\s*"(.*?)"')
                        installDirs = map(
                            lambda res: os.path.normpath(res.group(1)),
                            filter(
                                lambda res: res,
                                map(lambda line: matcher.search(line), libLines),
                            ),
                        )
                        for root in installDirs:
                            installPath = os.path.join(
                                root,
                                "steamapps",
                                "common",
                                "The Binding of Isaac Rebirth",
                            )
                            if QFile.exists(installPath):
                                cantFindPath = False
                                break

        # Mac Path things
        elif "Darwin" in platform.system():
            installPath = os.path.expanduser(
                "~/Library/Application Support/Steam/steamapps/common/The Binding of Isaac Rebirth/The Binding of Isaac Rebirth.app/Contents/Resources"
            )
            if not QFile.exists(installPath):
                cantFindPath = True

        # Linux and others
        elif "Linux" in platform.system():
            installPath = os.path.expanduser(
                "~/.local/share/Steam/steamapps/common/The Binding of Isaac Rebirth"
            )
            if not QFile.exists(installPath):
                cantFindPath = True
        else:
            cantFindPath = True

        # Looks like nothing was selected
        if cantFindPath or installPath == "" or not os.path.isdir(installPath):
            printf(
                f"Could not find The Binding of Isaac: {version} install folder ({installPath})"
            )
            return ""

        settings.setValue("InstallFolder", installPath)

    return installPath


def findModsPath(installPath=None):
    modsPath = ""
    cantFindPath = False

    if QFile.exists(settings.value("ModsFolder")):
        modsPath = settings.value("ModsFolder")

    else:
        installPath = installPath or findInstallPath()
        if len(installPath) > 0:
            modDirectory = os.path.join(installPath, "savedatapath.txt")
            if os.path.isfile(modDirectory):
                lines = list(open(modDirectory, "r"))
                modDirs = list(
                    filter(
                        lambda parts: parts[0] == "Modding Data Path",
                        map(lambda line: line.split(": "), lines),
                    )
                )
                if len(modDirs) > 0:
                    modsPath = os.path.normpath(modDirs[0][1].strip())

    if modsPath == "" or not os.path.isdir(modsPath):
        cantFindPath = True

    version = getGameVersion()

    if version not in ["Afterbirth+", "Repentance"]:
        printf(f"INFO: {version} does not support mod folders")
        return ""

    if cantFindPath:
        cantFindPath = False
        # Windows path things
        if "Windows" in platform.system():
            modsPath = os.path.join(
                os.path.expanduser("~"),
                "Documents",
                "My Games",
                f"Binding of Isaac {version} Mods",
            )
            if not QFile.exists(modsPath):
                cantFindPath = True

        # Mac Path things
        elif "Darwin" in platform.system():
            modsPath = os.path.expanduser(
                f"~/Library/Application Support/Binding of Isaac {version} Mods"
            )
            if not QFile.exists(modsPath):
                cantFindPath = True

        # Linux and others
        else:
            modsPath = os.path.expanduser(
                f"~/.local/share/binding of isaac {version.lower()} mods/"
            )
            if not QFile.exists(modsPath):
                cantFindPath = True

        # Fallback Resource Folder Locating
        if cantFindPath:
            modsPathOut = QFileDialog.getExistingDirectory(
                None, f"Please Locate The Binding of Isaac: {version} Mods Folder"
            )
            if not modsPathOut:
                QMessageBox.warning(
                    None,
                    "Error",
                    "Couldn't locate Mods folder and no folder was selected.",
                )
                return
            else:
                modsPath = modsPathOut
            if modsPath == "":
                QMessageBox.warning(
                    None,
                    "Error",
                    "Couldn't locate Mods folder and no folder was selected.",
                )
                return
            if not QDir(modsPath).exists:
                QMessageBox.warning(
                    None, "Error", "Selected folder does not exist or is not a folder."
                )
                return

        # Looks like nothing was selected
        if modsPath == "" or not os.path.isdir(modsPath):
            QMessageBox.warning(
                None,
                "Error",
                f"Could not find The Binding of Isaac: {version} Mods folder ({modsPath})",
            )
            return ""

        settings.setValue("ModsFolder", modsPath)

    return modsPath


def loadMods(autogenerate, installPath, resourcePath):
    global xmlLookups

    # Each mod in the mod folder is a Group
    modsPath = findModsPath(installPath)
    if not os.path.isdir(modsPath):
        printf("Could not find Mods Folder! Skipping mod content!")
        return

    modsInstalled = os.listdir(modsPath)

    autogenPath = "resources/Entities/ModTemp"
    if autogenerate and not os.path.exists(autogenPath):
        os.mkdir(autogenPath)

    printSectionBreak()
    printf("LOADING MOD CONTENT")
    for mod in modsInstalled:
        modPath = os.path.join(modsPath, mod)
        brPath = os.path.join(modPath, "basementrenovator")

        # Make sure we're a mod
        if not os.path.isdir(modPath) or os.path.isfile(
            os.path.join(modPath, "disable.it")
        ):
            continue

        # simple workaround for now
        if not (autogenerate or os.path.exists(brPath)):
            continue

        # Get the mod name
        modName = mod
        try:
            tree = ET.parse(os.path.join(modPath, "metadata.xml"))
            root = tree.getroot()
            modName = root.find("name").text
        except ET.ParseError:
            printf(
                f'Failed to parse mod metadata "{modName}", falling back on default name'
            )

        xmlLookups.loadFromMod(modPath, brPath, modName, autogenerate)


########################
#      Scene/View      #
########################


class RoomScene(QGraphicsScene):
    def __init__(self, parent):
        QGraphicsScene.__init__(self, 0, 0, 0, 0)
        self.newRoomSize(1)

        # Make the bitfont
        q = QImage()
        q.load("resources/UI/Bitfont.png")

        self.bitfont = [
            QPixmap.fromImage(q.copy(i * 12, j * 12, 12, 12))
            for j in range(int(q.height() / 12))
            for i in range(int(q.width() / 12))
        ]
        self.bitText = True

        self.roomDoorRoot = None
        self.clearDoors()

        self.bgState = []
        self.framecache = {}

        self.floorAnim = anm2.Config(
            "resources/Backgrounds/FloorBackdrop.anm2", "resources"
        )
        self.floorImg = None
        self.wallAnim = anm2.Config(
            "resources/Backgrounds/WallBackdrop.anm2", "resources"
        )
        self.wallImg = None

    def newRoomSize(self, shape):
        self.roomInfo = Room.Info(shape=shape)
        if not self.roomInfo.shapeData:
            return

        self.roomWidth, self.roomHeight = self.roomInfo.dims
        self.entCache = [[] for i in range(self.roomWidth * self.roomHeight)]

        self.roomRows = [QGraphicsWidget() for i in range(self.roomHeight)]
        for _, row in enumerate(self.roomRows):
            self.addItem(row)

        self.setSceneRect(
            -1 * 26, -1 * 26, (self.roomWidth + 2) * 26, (self.roomHeight + 2) * 26
        )

    def updateRoomDepth(self, room):
        if room.roomBG.get("InvertDepth") != "1":
            for i, row in enumerate(self.roomRows):
                row.setZValue(i)
        else:
            last = len(self.roomRows) - 1
            for i, row in enumerate(self.roomRows):
                row.setZValue(last - i)

    def getAdjacentEnts(self, x, y, useCache=False):
        width, height = self.roomWidth, self.roomHeight

        # [ L, R, U, D, UL, DL, UR, DR ]
        lookup = {
            -1: [4, 2, 6],
            0: [0, None, 1],
            1: [5, 3, 7],
        }

        res = [[] for i in range(8)]
        if useCache:
            for i in range(-1, 2):
                for j in range(-1, 2):
                    spot = lookup[i][j + 1]
                    if spot is not None:
                        idx = Room.Info.gridIndex(x + j, y + i, width)
                        if idx < 0 or idx >= width * height:
                            continue
                        res[spot] = self.entCache[idx]
            return res

        for yc in [y - 1, y, y + 1]:
            if yc < 0 or yc >= height:
                continue

            for item in self.roomRows[yc].childItems():
                xc = item.entity.x
                i = (xc - x) + 1
                if i > -1 and i < 3:
                    spots = lookup[yc - y]
                    if spots[i] is not None:
                        res[spots[i]].append(item)

        return res

    def getFrame(self, key, anm2):
        cache = self.framecache.get(key)
        if not cache:
            cache = {}
            self.framecache[key] = cache

        frame = cache.get(anm2.frame)
        if frame is None:
            frame = anm2.render()
            cache[anm2.frame] = frame

        return frame

    def clearDoors(self):
        if self.roomDoorRoot:
            # wrap if the underlying object is deleted
            try:
                self.roomDoorRoot.remove()
            except RuntimeError:
                pass

        self.roomDoorRoot = QGraphicsWidget()
        self.roomDoorRoot.setZValue(-1000)  # make sure doors display under entities
        self.addItem(self.roomDoorRoot)

    def drawForeground(self, painter, rect):
        # Bitfont drawing: moved to the RoomEditorWidget.drawForeground for easier anti-aliasing

        # Grey out the screen to show it's inactive if there are no rooms selected
        if mainWindow.roomList.selectedRoom() is None:
            b = QBrush(QColor(255, 255, 255, 100))
            painter.setPen(Qt.white)
            painter.setBrush(b)

            painter.fillRect(rect, b)
            return

        if settings.value("GridEnabled") == "0":
            return

        gs = 26

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        white = QColor.fromRgb(255, 255, 255, 100)
        bad = QColor.fromRgb(100, 255, 255, 100)

        showOutOfBounds = settings.value("BoundsGridEnabled") == "1"
        showGridIndex = settings.value("ShowGridIndex") == "1"
        showCoordinates = settings.value("ShowCoordinates") == "1"
        for y in range(self.roomHeight):
            for x in range(self.roomWidth):
                if self.roomInfo.isInBounds(x, y):
                    painter.setPen(QPen(white, 1, Qt.DashLine))
                else:
                    if not showOutOfBounds:
                        continue
                    painter.setPen(QPen(bad, 1, Qt.DashLine))

                painter.drawLine(x * gs, y * gs, (x + 1) * gs, y * gs)
                painter.drawLine(x * gs, (y + 1) * gs, (x + 1) * gs, (y + 1) * gs)
                painter.drawLine(x * gs, y * gs, x * gs, (y + 1) * gs)
                painter.drawLine((x + 1) * gs, y * gs, (x + 1) * gs, (y + 1) * gs)

                if showGridIndex:
                    painter.drawText(
                        x * gs + 2,
                        y * gs + 13,
                        f"{Room.Info.gridIndex(x, y, self.roomWidth)}",
                    )
                if showCoordinates:
                    painter.drawText(x * gs + 2, y * gs + 24, f"{x - 1},{y - 1}")

        # Draw Walls (Debug)
        # painter.setPen(QPen(Qt.green, 5, Qt.SolidLine))
        # h = gs / 2
        # walls = self.roomInfo.shapeData['Walls']
        # for wMin, wMax, wLvl, wDir in walls['X']:
        #     painter.drawLine(wMin * gs + h, wLvl * gs + h, wMax * gs + h, wLvl * gs + h)
        # for wMin, wMax, wLvl, wDir in walls['Y']:
        #     painter.drawLine(wLvl * gs + h, wMin * gs + h, wLvl * gs + h, wMax * gs + h)

        QGraphicsScene.drawForeground(self, painter, rect)

    def loadBackground(self):
        roomBG = None
        currentRoom = mainWindow.roomList.selectedRoom()
        if currentRoom:
            roomBG = currentRoom.roomBG
            roomShape = currentRoom.info.shape
        else:
            roomShape = 1

        bgState = [roomBG, roomShape]
        if bgState == self.bgState[:1]:
            return

        self.bgState = bgState

        gfxData = xmlLookups.getGfxData(roomBG)
        self.bgState.append(gfxData)

        roomBG = gfxData["Paths"]

        mainBG = roomBG.get("OuterBG") or "resources/none.png"
        overrideBG = roomBG.get("BigOuterBG")

        if roomShape != 1 and overrideBG:
            self.floorAnim.spritesheets[0] = overrideBG
        else:
            self.floorAnim.spritesheets[0] = mainBG

        self.floorAnim.spritesheets[1] = roomBG.get("LFloor") or "resources/none.png"
        self.floorAnim.spritesheets[2] = roomBG.get("NFloor") or "resources/none.png"

        self.wallAnim.spritesheets[0] = mainBG
        self.wallAnim.spritesheets[1] = roomBG.get("InnerBG") or "resources/none.png"

        self.floorAnim.setAnimation(str(roomShape))
        self.wallAnim.setAnimation(str(roomShape))

        self.floorImg = self.floorAnim.render()
        self.wallImg = self.wallAnim.render()

        self.roomShape = roomShape

    def getBGGfxData(self):
        return self.bgState[2] if self.bgState else None

    def drawBackground(self, painter, rect):
        self.loadBackground()

        xOff, yOff = 0, 0
        shapeData = RoomData.Shapes[self.roomShape]
        if shapeData.get("TopLeft"):
            xOff, yOff = RoomData.Info.coords(
                shapeData["TopLeft"], shapeData["Dims"][0]
            )

        gs = 26
        painter.drawImage((1 + xOff) * gs, (1 + yOff) * gs, self.floorImg)
        painter.drawImage((-1 + xOff) * gs, (-1 + yOff) * gs, self.wallImg)

        for stack in self.entCache:
            stack.clear()

        for item in self.items():
            if isinstance(item, Entity):
                xc = item.entity.x
                yc = item.entity.y
                self.entCache[Room.Info.gridIndex(xc, yc, self.roomWidth)].append(item)

        # have to set rock tiling ahead of time due to render order not being guaranteed left to right
        room = mainWindow.roomList.selectedRoom()
        if room:
            seed = room.seed
            for i, stack in enumerate(self.entCache):
                for ent in stack:
                    if ent.entity.config.renderRock and ent.entity.rockFrame is None:
                        ent.setRockFrame(seed + i)

        QGraphicsScene.drawBackground(self, painter, rect)


class RoomEditorWidget(QGraphicsView):
    def __init__(self, scene, parent=None):
        super(RoomEditorWidget, self).__init__(parent)

        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorViewCenter)
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.setAcceptDrops(True)

        self.assignNewScene(scene)

        self.canDelete = True

    def dragEnterEvent(self, evt):
        if evt.mimeData().hasFormat("text/uri-list"):
            evt.setAccepted(True)
            self.update()

    # if this is unimplemented, warnings are spewed
    def dragLeaveEvent(self, evt):
        pass

    # if this is unimplemented, drop does not work
    def dragMoveEvent(self, evt):
        pass

    def dropEvent(self, evt):
        if evt.mimeData().hasFormat("text/uri-list"):
            mainWindow.dropEvent(evt)

    def assignNewScene(self, scene):
        self.setScene(scene)
        self.centerOn(0, 0)

        self.objectToPaint = None
        self.lastTile = None

    def tryToPaint(self, event):
        """Called when a paint attempt is initiated"""

        paint = self.objectToPaint
        if paint is None:
            return

        clicked = self.mapToScene(event.x(), event.y())
        x, y = clicked.x(), clicked.y()

        x = int(x / 26)
        y = int(y / 26)

        xMax, yMax = self.scene().roomWidth, self.scene().roomHeight

        x = min(max(x, 0), xMax - 1)
        y = min(max(y, 0), yMax - 1)

        if settings.value("SnapToBounds") == "1":
            x, y = self.scene().roomInfo.snapToBounds(x, y)

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
        if (x, y) in self.lastTile:
            return
        self.lastTile.add((x, y))

        selection = self.scene().selectedItems()
        paintID, paintVariant, paintSubtype = paint.ID, paint.variant, paint.subtype
        if paint.config.hasBitfields and len(selection) == 1:
            selectedEntity = selection[0]
            if selectedEntity.entity.config == paint.config:
                paintID = selectedEntity.entity.Type
                paintVariant = selectedEntity.entity.Variant
                paintSubtype = selectedEntity.entity.Subtype

        en = Entity(x, y, int(paintID), int(paintVariant), int(paintSubtype), 1.0)
        if en.entity.config.hasTag("Grid"):
            en.updateCoords(x, y, depth=0)

        mainWindow.dirt()

    def mousePressEvent(self, event):
        if event.buttons() == Qt.RightButton:
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
        if self.canDelete and (event.key() == Qt.Key_Delete):
            scene = self.scene()
            selection = scene.selectedItems()

            if len(selection) > 0:
                for obj in selection:
                    obj.setSelected(False)
                    obj.remove()
                scene.update()
                self.update()
                mainWindow.dirt()

        QGraphicsView.keyPressEvent(self, event)

    def drawBackground(self, painter, rect):
        painter.fillRect(rect, QColor(0, 0, 0))

        QGraphicsView.drawBackground(self, painter, rect)

    def resizeEvent(self, event):
        QGraphicsView.resizeEvent(self, event)

        w = self.scene().roomWidth
        h = self.scene().roomHeight

        xScale = (event.size().width() - 2) / (26 * (w + 2))
        yScale = (event.size().height() - 2) / (26 * (h + 2))
        newScale = min([xScale, yScale])

        tr = QTransform()
        tr.scale(newScale, newScale)

        self.setTransform(tr)

        if newScale == yScale:
            self.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        else:
            self.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

    def calculateTotalHP(self, baseHP, stageHP, stageNum):
        totalHP = round(
            baseHP
            + ((min(4, stageNum) + (0.8 * max(0, min(stageNum - 5, 5)))) * stageHP),
            2,
        )
        if totalHP.is_integer():
            return int(totalHP)
        else:
            return totalHP

    def paintEvent(self, event):
        # Purely handles the status overlay text
        QGraphicsView.paintEvent(self, event)

        if settings.value("StatusEnabled") == "0":
            return

        # Display the room status in a text overlay
        painter = QPainter()
        painter.begin(self.viewport())

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setPen(QPen(Qt.white, 1, Qt.SolidLine))

        room = mainWindow.roomList.selectedRoom()
        if room:
            # Room Type Icon
            roomTypes = xmlLookups.roomTypes.lookup(room=room, showInMenu=True)
            if len(roomTypes) > 0:
                q = QPixmap(roomTypes[0].get("Icon"))
                painter.drawPixmap(2, 3, q)
            else:
                printf("Warning: Unknown room type during paintEvent:", room.getDesc())

            # Top Text
            font = painter.font()
            font.setPixelSize(13)
            painter.setFont(font)
            painter.drawText(20, 16, f"{room.info.variant} - {room.name}")

            # Bottom Text
            font = painter.font()
            font.setPixelSize(10)
            painter.setFont(font)
            painter.drawText(
                8,
                30,
                f"Type: {room.info.type}, Variant: {room.info.variant}, Subtype: {room.info.subtype}, Difficulty: {room.difficulty}, Weight: {room.weight}",
            )

        # Display the currently selected entity in a text overlay
        selectedEntities = self.scene().selectedItems()

        if len(selectedEntities) == 1:
            e = selectedEntities[0]
            r = event.rect()

            # Entity Icon
            painter.drawPixmap(QRect(r.right() - 32, 2, 32, 32), e.entity.iconpixmap)

            # Top Text
            font = painter.font()
            font.setPixelSize(13)
            painter.setFont(font)
            painter.drawText(
                r.right() - 34 - 400,
                2,
                400,
                16,
                int(Qt.AlignRight | Qt.AlignBottom),
                f"{e.entity.Type}.{e.entity.Variant}.{e.entity.Subtype} - {e.entity.config.name}",
            )

            # Bottom Text
            font = painter.font()
            font.setPixelSize(10)
            painter.setFont(font)
            textY = 20
            tags = e.entity.config.tagsString
            if tags != "[]":
                painter.drawText(
                    r.right() - 34 - 400,
                    textY,
                    400,
                    12,
                    int(Qt.AlignRight | Qt.AlignBottom),
                    "Tags: " + tags,
                )
                textY += 16

            painter.drawText(
                r.right() - 34 - 200,
                textY,
                200,
                12,
                int(Qt.AlignRight | Qt.AlignBottom),
                f"Base HP : {e.entity.config.baseHP}",
            )
            textY += 16

            if e.entity.config.stageHP is not None and e.entity.config.stageHP != "0":
                painter.drawText(
                    r.right() - 34 - 200,
                    textY,
                    200,
                    12,
                    int(Qt.AlignRight | Qt.AlignBottom),
                    f"Stage HP : {e.entity.config.stageHP}",
                )
                textY += 16

                stageHPNum = mainWindow.floorInfo.get(
                    "StageHPNum"
                ) or mainWindow.floorInfo.get("Stage")
                totalHP = self.calculateTotalHP(
                    float(e.entity.config.baseHP),
                    float(e.entity.config.stageHP),
                    float(stageHPNum),
                )

                painter.drawText(
                    r.right() - 34 - 200,
                    textY,
                    200,
                    12,
                    int(Qt.AlignRight | Qt.AlignBottom),
                    f"Total HP : {totalHP}",
                )
                textY += 16

            if e.entity.config.armor is not None and e.entity.config.armor != "0":
                painter.drawText(
                    r.right() - 34 - 200,
                    textY,
                    200,
                    12,
                    int(Qt.AlignRight | Qt.AlignBottom),
                    f"Armor : {e.entity.config.armor}",
                )

        elif len(selectedEntities) > 1:
            e = selectedEntities[0]
            r = event.rect()

            # Case Two: more than one type of entity
            # Entity Icon
            painter.drawPixmap(QRect(r.right() - 32, 2, 32, 32), e.entity.pixmap)

            # Top Text
            font = painter.font()
            font.setPixelSize(13)
            painter.setFont(font)
            painter.drawText(
                r.right() - 34 - 200,
                2,
                200,
                16,
                int(Qt.AlignRight | Qt.AlignBottom),
                f"{len(selectedEntities)} Entities Selected",
            )

            # Bottom Text
            font = painter.font()
            font.setPixelSize(10)
            painter.setFont(font)
            painter.drawText(
                r.right() - 34 - 200,
                20,
                200,
                12,
                int(Qt.AlignRight | Qt.AlignBottom),
                ", ".join(
                    set([x.entity.config.name or "INVALID" for x in selectedEntities])
                ),
            )

            pass

        painter.end()

    def drawForeground(self, painter, rect):
        QGraphicsView.drawForeground(self, painter, rect)

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        # Display the number of entities on a given tile, in bitFont or regular font
        tiles = [
            [0 for x in range(self.scene().roomWidth)]
            for y in range(self.scene().roomHeight)
        ]
        for e in self.scene().items():
            if isinstance(e, Entity):
                tiles[e.entity.y][e.entity.x] += 1

        useAliased = settings.value("BitfontEnabled") == "0"

        if useAliased:
            painter.setPen(Qt.white)
            painter.font().setPixelSize(5)

        for y, row in enumerate(tiles):
            yc = (y + 1) * 26 - 12

            for x, count in enumerate(row):
                if count <= 1:
                    continue

                if not useAliased:
                    xc = (x + 1) * 26 - 12

                    digits = [int(i) for i in str(count)]

                    fontrow = count == EntityStack.MAX_STACK_DEPTH and 1 or 0

                    numDigits = len(digits) - 1
                    for i, digit in enumerate(digits):
                        painter.drawPixmap(
                            xc - 12 * (numDigits - i),
                            yc,
                            self.scene().bitfont[digit + fontrow * 10],
                        )
                else:
                    if count == EntityStack.MAX_STACK_DEPTH:
                        painter.setPen(Qt.red)

                    painter.drawText(
                        x * 26,
                        y * 26,
                        26,
                        26,
                        int(Qt.AlignBottom | Qt.AlignRight),
                        str(count),
                    )

                    if count == EntityStack.MAX_STACK_DEPTH:
                        painter.setPen(Qt.white)


class Entity(QGraphicsItem):
    GRID_SIZE = 26

    class Info:
        def __init__(self, x=0, y=0, t=0, v=0, s=0, weight=0, changeAtStart=True):
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
            self.config = None
            self.rockFrame = None
            self.placeVisual = None
            self.imgPath = None
            self.pixmap = None
            self.iconpixmap = None
            self.overlaypixmap = None
            self.known = False

            self.getEntityInfo(t, v, s)

        def getEntityInfo(self, entitytype, variant, subtype):
            self.config = xmlLookups.entities.lookupOne(entitytype, variant, subtype)
            if self.config is None:
                printf(
                    f"'Could not find Entity {entitytype}.{variant}.{subtype} for in-editor, using ?"
                )

                self.pixmap = QPixmap("resources/Entities/questionmark.png")
                self.iconpixmap = self.pixmap
                self.config = xmlLookups.entities.EntityConfig()
                return

            if self.config.hasBitfields:
                for bitfield in self.config.bitfields:
                    self.validateBitfield(bitfield)

            self.rockFrame = None
            self.imgPath = self.config.editorImagePath or self.config.imagePath

            if (
                entitytype == EntityType["PICKUP"]
                and variant == PickupVariant["COLLECTIBLE"]
            ):
                i = QImage()
                i.load("resources/Entities/5.100.0 - Collectible.png")
                i = i.convertToFormat(QImage.Format_ARGB32)

                d = QImage()
                d.load(self.imgPath)

                p = QPainter(i)
                p.drawImage(0, 0, d)
                p.end()

                self.pixmap = QPixmap.fromImage(i)

            else:
                self.pixmap = QPixmap(self.imgPath)

            if self.imgPath != self.config.imagePath:
                self.iconpixmap = QPixmap(self.config.imagePath)
            else:
                self.iconpixmap = self.pixmap

            if self.config.placeVisual:
                parts = list(
                    map(lambda x: x.strip(), self.config.placeVisual.split(","))
                )
                if len(parts) == 2 and checkFloat(parts[0]) and checkFloat(parts[1]):
                    self.placeVisual = (float(parts[0]), float(parts[1]))
                else:
                    self.placeVisual = parts[0]

            if self.config.overlayImagePath:
                self.overlaypixmap = QPixmap(self.config.overlayImagePath)

            self.known = True

        def validateBitfield(self, bitfield):
            value = self.getBitfieldValue(bitfield)
            if not isinstance(value, int):
                printf(
                    f"Entity {self.config.name} ({self.config.type}.{self.config.variant}.{self.config.subtype}) has an invalid bitfield Key {bitfield.key}"
                )
                self.config.invalidBitfield = True
            else:
                value = bitfield.clampValues(value)
                setattr(self, bitfield.key, value)

        def getBitfieldValue(self, bitfield):
            return getattr(self, bitfield.key)

        def setBitfieldElementValue(self, bitfieldElement, value):
            setattr(
                self,
                bitfieldElement.bitfield.key,
                bitfieldElement.setRawValue(
                    self.getBitfieldValue(bitfieldElement.bitfield), int(value)
                ),
            )

    def __init__(self, x, y, myType, variant, subtype, weight, respawning=False):
        super(QGraphicsItem, self).__init__()

        # used when the ent is coming in from a previous state and should not update permanent things,
        # e.g. door enablement
        self.respawning = respawning

        self.setFlags(
            self.ItemSendsGeometryChanges | self.ItemIsSelectable | self.ItemIsMovable
        )

        self.stackDepth = 1
        self.popup = None
        mainWindow.scene.selectionChanged.connect(self.hideWeightPopup)

        self.entity = Entity.Info(x, y, myType, variant, subtype, weight)
        self.updateCoords(x, y)
        self.updateTooltip()

        self.updatePosition()

        if not hasattr(Entity, "SELECTION_PEN"):
            Entity.SELECTION_PEN = QPen(Qt.green, 1, Qt.DashLine)
            Entity.OFFSET_SELECTION_PEN = QPen(Qt.red, 1, Qt.DashLine)
            Entity.INVALID_ERROR_IMG = QPixmap("resources/UI/ent-error.png")
            Entity.OUT_OF_RANGE_WARNING_IMG = QPixmap("resources/UI/ent-warning.png")

        self.setAcceptHoverEvents(True)

        self.respawning = False

    def setData(self, t, v, s):
        self.entity.changeTo(t, v, s)
        self.updateTooltip()

    def updateTooltip(self):
        e = self.entity
        tooltipStr = ""
        if e.known:
            tooltipStr = f"{e.config.name} @ {e.x-1} x {e.y-1} - {e.Type}.{e.Variant}.{e.Subtype}; HP: {e.config.baseHP}"
            tooltipStr += e.config.getEditorWarnings()
        else:
            tooltipStr = (
                f"Missing @ {e.x-1} x {e.y-1} - {e.Type}.{e.Variant}.{e.Subtype}"
            )
            tooltipStr += (
                "\nMissing BR entry! Trying to spawn this entity might CRASH THE GAME!!"
            )

        self.setToolTip(tooltipStr)

    def updateCoords(self, x, y, depth=-1):
        scene = mainWindow.scene

        def entsInCoord(x, y):
            return filter(
                lambda e: e.entity.x == x and e is not self,
                scene.roomRows[y].childItems(),
            )

        adding = self.parentItem() is None
        if adding:
            self.setParentItem(scene.roomRows[y])

            if self.entity.config.gfx is not None:
                currentRoom = mainWindow.roomList.selectedRoom()
                if currentRoom:
                    currentRoom.setRoomBG(self.entity.config.gfx)

            self.updateBlockedDoor(False, countOnly=self.respawning)
            return

        z = self.zValue()
        moving = self.entity.x != x or self.entity.y != y

        if (depth < 0 and moving) or depth != z:
            topOfStack = False
            if depth < 0:
                depth = sum(1 for _ in entsInCoord(x, y))
                topOfStack = True

            if not topOfStack:
                for entity in entsInCoord(x, y):
                    z2 = entity.zValue()
                    if z2 >= depth:
                        entity.setZValue(z2 + 1)

            if moving:
                for entity in entsInCoord(self.entity.x, self.entity.y):
                    z2 = entity.zValue()
                    if z2 > z:
                        entity.setZValue(z2 - 1)

            self.setParentItem(scene.roomRows[y])
            self.setZValue(depth)

        if moving:
            self.updateBlockedDoor(True)

        self.entity.x = x
        self.entity.y = y

        if moving:
            self.updateBlockedDoor(False)

    def updateBlockedDoor(self, val, countOnly=False):
        if not self.entity.config.hasTag("NoBlockDoors"):
            blockedDoor = self.scene().roomInfo.inFrontOfDoor(
                self.entity.x, self.entity.y
            )
            if blockedDoor:
                for door in self.scene().roomDoorRoot.childItems():
                    if door.doorItem[:2] == blockedDoor[:2]:
                        doorFollowsBlockRule = (door.blockingCount == 0) == door.exists
                        door.blockingCount += val and -1 or 1
                        if doorFollowsBlockRule and door.exists and not countOnly:
                            # if the door was already following the blocking rules
                            # AND it was open (do not open closed doors) then close it
                            door.exists = door.blockingCount == 0
                        break

    PitAnm2 = anm2.Config("resources/Backgrounds/PitGrid.anm2", "resources")
    PitAnm2.setAnimation()

    RockAnm2 = anm2.Config("resources/Backgrounds/RockGrid.anm2", "resources")
    RockAnm2.setAnimation()

    def getPitFrame(self, pitImg, rendered):
        def matchInStack(stack):
            for ent in stack:
                img = ent.getCurrentImg()

                if img == pitImg:
                    return True

            return False

        adjEnts = self.scene().getAdjacentEnts(
            self.entity.x, self.entity.y, useCache=True
        )

        [L, R, U, D, UL, DL, UR, DR] = list(map(matchInStack, adjEnts))
        hasExtraFrames = rendered.height() > 260

        # copied from stageapi
        # Words were shortened to make writing code simpler.
        F = 0  # Sprite frame to set

        # First bitwise frames (works for all combinations of just left up right and down)
        if L:
            F = F | 1
        if U:
            F = F | 2
        if R:
            F = F | 4
        if D:
            F = F | 8

        # Then a bunch of other combinations
        if U and L and not UL and not R and not D:
            F = 17
        if U and R and not UR and not L and not D:
            F = 18
        if L and D and not DL and not U and not R:
            F = 19
        if R and D and not DR and not L and not U:
            F = 20
        if L and U and R and D and not UL:
            F = 21
        if L and U and R and D and not UR:
            F = 22
        if U and R and D and not L and not UR:
            F = 25
        if L and U and D and not R and not UL:
            F = 26
        if hasExtraFrames:
            if U and L and D and UL and not DL:
                F = 35
            if U and R and D and UR and not DR:
                F = 36

        if L and U and R and D and not DL and not DR:
            F = 24
        if L and U and R and D and not UR and not UL:
            F = 23
        if L and U and R and UL and not UR and not D:
            F = 27
        if L and U and R and UR and not UL and not D:
            F = 28
        if L and U and R and not D and not UR and not UL:
            F = 29
        if L and R and D and DL and not U and not DR:
            F = 30
        if L and R and D and DR and not U and not DL:
            F = 31
        if L and R and D and not U and not DL and not DR:
            F = 32

        if hasExtraFrames:
            if U and R and D and not L and not UR and not DR:
                F = 33
            if U and L and D and not R and not UL and not DL:
                F = 34
            if U and R and D and L and UL and UR and DL and not DR:
                F = 37
            if U and R and D and L and UL and UR and DR and not DL:
                F = 38
            if U and R and D and L and not UL and not UR and not DR and not DL:
                F = 39
            if U and R and D and L and DL and DR and not UL and not UR:
                F = 40
            if U and R and D and L and DL and UR and not UL and not DR:
                F = 41
            if U and R and D and L and UL and DR and not DL and not UR:
                F = 42
            if U and R and D and L and UL and not DL and not UR and not DR:
                F = 43
            if U and R and D and L and UR and not UL and not DL and not DR:
                F = 44
            if U and R and D and L and DL and not UL and not UR and not DR:
                F = 45
            if U and R and D and L and DR and not UL and not UR and not DL:
                F = 46
            if U and R and D and L and DL and DR and not UL and not UR:
                F = 47
            if U and R and D and L and DL and UL and not UR and not DR:
                F = 48
            if U and R and D and L and DR and UR and not UL and not DL:
                F = 49

        return F

    def setRockFrame(self, seed):
        if settings.value("RandomizeRocks") == "0":
            seed = 0

        random.seed(seed)
        self.entity.rockFrame = random.randint(0, 2)
        self.entity.placeVisual = (0, 3 / 26)

        if seed & 3 != 0:
            return

        rockImg = self.getCurrentImg()

        def findMatchInStack(stack):
            for ent in stack:
                img = ent.getCurrentImg()

                if img == rockImg:
                    return ent
            return None

        [_, right, _, down, _, _, _, downRight] = self.scene().getAdjacentEnts(
            self.entity.x, self.entity.y, useCache=True
        )

        candidates = []

        R = findMatchInStack(right)
        if R is not None and R.entity.rockFrame is None:
            candidates.append("2x1")

        D = findMatchInStack(down)
        if D is not None and D.entity.rockFrame is None:
            candidates.append("1x2")

        DR = None
        if len(candidates) == 2:
            DR = findMatchInStack(downRight)
            if DR is not None and DR.entity.rockFrame is None:
                candidates.append("2x2")

        if not candidates:
            return

        g = 6 / 26
        h = 0.21  # 3/26 rounded
        nh = -0.235  # -3/26 rounded, weird asymmetric offset issues

        choice = random.choice(candidates)
        if choice == "2x1":
            self.entity.rockFrame = 3
            self.entity.placeVisual = (nh, 0)
            R.entity.rockFrame = 4
            R.entity.placeVisual = (h, 0)
        elif choice == "1x2":
            self.entity.rockFrame = 5
            self.entity.placeVisual = (0, 0)
            D.entity.rockFrame = 6
            D.entity.placeVisual = (0, g)
        elif choice == "2x2":
            self.entity.rockFrame = 7
            self.entity.placeVisual = (nh, 0)
            R.entity.rockFrame = 8
            R.entity.placeVisual = (h, 0)
            D.entity.rockFrame = 9
            D.entity.placeVisual = (nh, g)
            DR.entity.rockFrame = 10
            DR.entity.placeVisual = (h, g)

    def itemChange(self, change, value):
        if change == self.ItemPositionChange:
            currentX, currentY = self.entity.x, self.entity.y

            xc, yc = value.x(), value.y()

            # TODO fix this hack, this is only needed because we don't have a scene on init
            w, h = 28, 16
            if self.scene():
                w = self.scene().roomWidth
                h = self.scene().roomHeight

            # should be round, but python is dumb and
            # arbitrarily decides when it wants to be
            # a normal programming language
            x = int(xc / Entity.GRID_SIZE + 0.5)
            y = int(yc / Entity.GRID_SIZE + 0.5)

            x = min(max(x, 0), w - 1)
            y = min(max(y, 0), h - 1)

            if x != currentX or y != currentY:
                # TODO above hack is here too
                if settings.value("SnapToBounds") == "1" and self.scene():
                    x, y = self.scene().roomInfo.snapToBounds(x, y)

                self.updateCoords(x, y)

                self.updateTooltip()
                if self.isSelected():
                    mainWindow.dirt()

            xc = x * Entity.GRID_SIZE
            yc = y * Entity.GRID_SIZE

            value.setX(xc)
            value.setY(yc)

            self.getStack()
            if self.popup:
                self.popup.update(self.stack)

            return value

        return QGraphicsItem.itemChange(self, change, value)

    def boundingRect(self):
        # if self.entity.pixmap:
        # 	return QRectF(self.entity.pixmap.rect())
        # else:
        return QRectF(0.0, 0.0, 26.0, 26.0)

    def updatePosition(self):
        self.setPos(self.entity.x * 26, self.entity.y * 26)

    def getGfxOverride(self):
        gfxData = self.scene().getBGGfxData()
        if gfxData is None:
            return None

        variant = self.entity.Variant
        subtype = self.entity.Subtype

        if self.entity.config.hasBitfields:
            if self.entity.config.hasBitfieldKey("Subtype"):
                subtype = 0

            if self.entity.config.hasBitfieldKey("Variant"):
                variant = 0

        entID = f"{self.entity.Type}.{variant}.{subtype}"

        return gfxData["Entities"].get(entID)

    def getCurrentImg(self):
        override = self.getGfxOverride()
        return self.entity.imgPath if override is None else override.get("Image")

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        painter.setBrush(Qt.Dense5Pattern)
        painter.setPen(QPen(Qt.white))

        if self.entity.pixmap:
            xc, yc = 0, 0

            typ, var, sub = self.entity.Type, self.entity.Variant, self.entity.Subtype

            def WallSnap():
                ex = self.entity.x
                ey = self.entity.y

                shape = self.scene().roomInfo.shapeData

                walls = shape["Walls"]
                distancesY = [
                    ((ex < w[0] or ex > w[1]) and 100000 or abs(ey - w[2]), w)
                    for w in walls["X"]
                ]
                distancesX = [
                    ((ey < w[0] or ey > w[1]) and 100000 or abs(ex - w[2]), w)
                    for w in walls["Y"]
                ]

                closestY = min(distancesY, key=lambda w: w[0])
                closestX = min(distancesX, key=lambda w: w[0])

                # TODO match up with game when distances are equal
                wx, wy = 0, 0
                if closestY[0] < closestX[0]:
                    w = closestY[1]
                    wy = w[2] - ey
                else:
                    w = closestX[1]
                    wx = (w[2] - ex) * 2

                return wx, wy

            customPlaceVisuals = {"WallSnap": WallSnap}

            recenter = self.entity.placeVisual

            imgPath = self.entity.imgPath

            rendered = self.entity.pixmap
            renderFunc = painter.drawPixmap

            override = self.getGfxOverride()

            if override is not None:
                img = override.get("Image")
                if img:
                    rendered = QPixmap(img)
                    imgPath = img

                    placeVisual = override.get("PlaceVisual")
                    if placeVisual is not None:
                        parts = list(map(lambda x: x.strip(), placeVisual.split(",")))
                        if (
                            len(parts) == 2
                            and checkFloat(parts[0])
                            and checkFloat(parts[1])
                        ):
                            placeVisual = (float(parts[0]), float(parts[1]))
                        else:
                            placeVisual = parts[0]
                        recenter = placeVisual

                if override.get("InvertDepth") == "1":
                    self.setZValue(-1 * self.entity.y)

            if recenter:
                if isinstance(recenter, str):
                    recenter = customPlaceVisuals.get(recenter, None)
                    if recenter:
                        xc, yc = recenter()
                else:
                    xc, yc = recenter

            xc += 1
            yc += 1

            def drawGridBorders():
                painter.drawLine(0, 0, 0, 4)
                painter.drawLine(0, 0, 4, 0)

                painter.drawLine(26, 0, 26, 4)
                painter.drawLine(26, 0, 22, 0)

                painter.drawLine(0, 26, 4, 26)
                painter.drawLine(0, 26, 0, 22)

                painter.drawLine(26, 26, 22, 26)
                painter.drawLine(26, 26, 26, 22)

            if self.entity.config.renderPit:
                Entity.PitAnm2.frame = self.getPitFrame(imgPath, rendered)
                Entity.PitAnm2.spritesheets[0] = rendered
                rendered = self.scene().getFrame(imgPath + " - pit", Entity.PitAnm2)
                renderFunc = painter.drawImage
            elif self.entity.config.renderRock and self.entity.rockFrame is not None:
                Entity.RockAnm2.frame = self.entity.rockFrame
                Entity.RockAnm2.spritesheets[0] = rendered
                rendered = self.scene().getFrame(imgPath + " - rock", Entity.RockAnm2)
                renderFunc = painter.drawImage

                # clear frame after rendering to reset for next frame
                self.entity.rockFrame = None

            width, height = rendered.width(), rendered.height()

            x = int((xc * 26 - width) / 2)
            y = int(yc * 26 - height)

            renderFunc(x, y, rendered)

            # if the offset is high enough, draw an indicator of the actual position
            if not self.entity.config.disableOffsetIndicator and (
                abs(1 - yc) > 0.5 or abs(1 - xc) > 0.5
            ):
                painter.setPen(self.OFFSET_SELECTION_PEN)
                painter.setBrush(Qt.NoBrush)
                painter.drawLine(13, 13, int(x + width / 2), y + height - 13)
                drawGridBorders()
                painter.fillRect(
                    int(x + width / 2 - 3), y + height - 13 - 3, 6, 6, Qt.red
                )

            if self.isSelected():
                painter.setPen(self.SELECTION_PEN)
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(x, y, width, height)

                # Grid space boundary
                painter.setPen(Qt.green)
                drawGridBorders()

            if self.entity.overlaypixmap:
                painter.drawPixmap(0, 0, self.entity.overlaypixmap)

        if not self.entity.known:
            painter.setFont(QFont("Arial", 6))

            painter.drawText(2, 26, "%d.%d.%d" % (typ, var, sub))

        warningIcon = None
        # applies to entities that do not have a corresponding entities2 entry
        if not self.entity.known or self.entity.config.invalid:
            warningIcon = Entity.INVALID_ERROR_IMG
        # entities have 12 bits for type, variant, and subtype (?)
        # common mod error is to make them outside that range
        elif self.entity.config.isOutOfRange():
            warningIcon = Entity.OUT_OF_RANGE_WARNING_IMG

        if warningIcon:
            painter.drawPixmap(18, -8, warningIcon)

    def remove(self):
        if self.popup:
            self.popup.remove()
            self.scene().views()[0].canDelete = True
        self.updateBlockedDoor(True)
        self.setParentItem(None)
        self.scene().removeItem(self)

    def mouseReleaseEvent(self, event):
        e = self.entity
        if (
            event.button() == Qt.MiddleButton
            and e.config.hasBitfields
            and not e.config.invalidBitfield
        ):
            EntityMenu(e)
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
        self.stack = [x for x in stack if isinstance(x, Entity)]

        # 1 is not a stack.
        self.stackDepth = len(self.stack)

    def createWeightPopup(self):
        self.getStack()
        if self.stackDepth <= 1 or any(
            x.popup and x != self and x.popup.isVisible() for x in self.stack
        ):
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
            if self.scene():
                self.scene().views()[0].canDelete = True


class EntityMenu(QWidget):
    def __init__(self, entity):
        """Initializes the widget."""

        QWidget.__init__(self)

        self.layout = QVBoxLayout()

        self.entity = entity
        self.setupList()

        self.layout.addWidget(self.list)
        self.setLayout(self.layout)

    def setupList(self):
        self.list = QListWidget()
        self.list.setViewMode(self.list.ListMode)
        self.list.setSelectionMode(self.list.ExtendedSelection)
        self.list.setResizeMode(self.list.Adjust)
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)

        cursor = QCursor()
        self.customContextMenu(cursor.pos())

    def changeProperty(self, bitfieldElement, value):
        self.entity.setBitfieldElementValue(bitfieldElement, value)

        mainWindow.dirt()
        mainWindow.scene.update()

    def updateLabel(self, label, bitfieldElement):
        label.setText(
            f"{bitfieldElement.name}: {self.getDisplayValue(bitfieldElement)} {bitfieldElement.unit}"
        )

    def connectBitfieldElement(self, widget, bitfieldElement, label=None):
        def changeValue(x):
            value = bitfieldElement.getRawValueFromWidgetValue(x)
            self.changeProperty(bitfieldElement, value)

            if label:
                self.updateLabel(label, bitfieldElement)

        if bitfieldElement.widget == "dropdown":
            widget.currentIndexChanged.connect(changeValue)
        elif bitfieldElement.widget == "checkbox":
            widget.stateChanged.connect(lambda: changeValue(widget.isChecked()))
        elif bitfieldElement.widget == "bitmap":
            layout = widget.layout()
            for x in range(0, bitfieldElement.gridwidth):
                for y in range(
                    0, math.ceil(bitfieldElement.length / bitfieldElement.gridwidth)
                ):
                    checkbox = layout.itemAtPosition(y, x).widget()
                    checkbox.stateChanged.connect(
                        lambda: changeValue(
                            self.readBitmapWidget(widget, bitfieldElement)
                        )
                    )
        else:
            widget.valueChanged.connect(changeValue)

        if label:
            self.updateLabel(label, bitfieldElement)

    def readBitmapWidget(self, widget: QGroupBox, bitfieldElement):
        layout = widget.layout()
        value = 0
        for x in range(0, bitfieldElement.gridwidth):
            for y in range(
                0, math.ceil(bitfieldElement.length / bitfieldElement.gridwidth)
            ):
                bit = y * bitfieldElement.gridwidth + x
                checkbox = layout.itemAtPosition(y, x).widget()
                if checkbox.isChecked():
                    value = bitSet(value, 1, bit, 1)

        return value

    def getWidgetValue(self, bitfieldElement):
        return bitfieldElement.getWidgetValue(
            self.entity.getBitfieldValue(bitfieldElement.bitfield)
        )

    def getDisplayValue(self, bitfieldElement):
        return bitfieldElement.getDisplayValue(
            self.entity.getBitfieldValue(bitfieldElement.bitfield)
        )

    WIDGETS_WITH_LABELS = ("slider", "dial")

    # @pyqtSlot(QPoint)
    def customContextMenu(self, pos):
        menu = QMenu(self.list)

        for bitfieldElement in self.entity.config.getBitfieldElements():
            if not hasattr(self.entity, bitfieldElement.bitfield.key):
                continue

            label = None
            if bitfieldElement.widget in EntityMenu.WIDGETS_WITH_LABELS:
                action = QWidgetAction(menu)
                label = QLabel("")
                action.setDefaultWidget(label)
                menu.addAction(action)

            action = QWidgetAction(menu)
            widget = None
            if bitfieldElement.widget == "spinner":
                widget = QSpinBox()
                minimum, maximum = bitfieldElement.getWidgetRange()
                widget.setRange(minimum, maximum)
                widget.setValue(self.getWidgetValue(bitfieldElement))
                widget.setPrefix(bitfieldElement.name + ": ")
                if bitfieldElement.floatvalueoffset != 0:
                    widget.setSuffix(
                        f"{str(bitfieldElement.floatvalueoffset)[1:]} {bitfieldElement.unit}"
                    )
                else:
                    widget.setSuffix(f" {bitfieldElement.unit}")
            elif bitfieldElement.widget == "dropdown":
                widget = QComboBox()
                for item in bitfieldElement.dropdownkeys:
                    widget.addItem(item)
                widget.setCurrentIndex(self.getWidgetValue(bitfieldElement))
            elif bitfieldElement.widget == "slider":
                widget = QSlider(Qt.Horizontal)
                minimum, maximum = bitfieldElement.getWidgetRange()
                widget.setRange(minimum, maximum)
                widget.setValue(self.getWidgetValue(bitfieldElement))
            elif bitfieldElement.widget == "dial":
                widget = QDial()
                minimum, maximum = bitfieldElement.getWidgetRange()
                widget.setRange(minimum, maximum)
                widget.setValue(self.getWidgetValue(bitfieldElement))
                widget.setNotchesVisible(True)
                widget.setWrapping(True)
            elif bitfieldElement.widget == "checkbox":
                widget = QCheckBox()
                widget.setText(bitfieldElement.name)
                widget.setChecked(self.getWidgetValue(bitfieldElement))
            elif bitfieldElement.widget == "bitmap":
                widget = QGroupBox(bitfieldElement.name)
                layout = QGridLayout()
                bitmap = self.getWidgetValue(bitfieldElement)
                for i in range(0, bitfieldElement.length):
                    checkbox = QCheckBox()
                    checked = bitGet(bitmap, i, 1)
                    checkbox.setChecked(checked)
                    x = i % bitfieldElement.gridwidth
                    y = math.floor(i / bitfieldElement.gridwidth)
                    layout.addWidget(checkbox, y, x)

                widget.setLayout(layout)

            if bitfieldElement.tooltip:
                widget.setToolTip(bitfieldElement.tooltip)

            action.setDefaultWidget(widget)
            self.connectBitfieldElement(widget, bitfieldElement, label)
            menu.addAction(action)

        # End it
        menu.exec(self.list.mapToGlobal(pos))


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
            weight.valueChanged.connect((lambda v: lambda: self.weightChanged(v))(i))
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

        brush = QBrush(QColor(0, 0, 0, 80))
        painter.setPen(QPen(Qt.transparent))
        painter.setBrush(brush)

        r = self.boundingRect().adjusted(0, 0, 0, -16)

        path = QPainterPath()
        path.addRoundedRect(r, 4, 4)
        path.moveTo(r.center().x() - 6, r.bottom())
        path.lineTo(r.center().x() + 6, r.bottom())
        path.lineTo(r.center().x(), r.bottom() + 12)
        painter.drawPath(path)

        painter.setPen(QPen(Qt.white))
        painter.setFont(QFont("Arial", 8))

        w = 0
        for i, item in enumerate(self.items):
            pix = item.entity.iconpixmap
            self.spinners[i].setPos(w - 8, r.bottom() - 26)
            w += 4
            painter.drawPixmap(int(w), int(r.bottom() - 20 - pix.height()), pix)

            # painter.drawText(w, r.bottom()-16, pix.width(), 8, Qt.AlignCenter, "{:.1f}".format(item.entity.weight))
            w += pix.width()

    def boundingRect(self):
        width = 0
        height = 0

        # Calculate the combined size
        for item in self.items:
            dx, dy = 26, 26
            pix = item.entity.iconpixmap
            if pix is not None:
                dx, dy = pix.rect().width(), pix.rect().height()
            width = width + dx
            height = max(height, dy)

        # Add in buffers
        height = height + 8 + 8 + 8 + 16  # Top, bottom, weight text, and arrow
        width = width + 4 + len(self.items) * 4  # Left and right and the middle bits

        self.setX(self.items[-1].x() - width / 2 + 13)
        self.setY(self.items[-1].y() - height)

        return QRectF(0.0, 0.0, width, height)

    def remove(self):
        # Fix for the null pointer left by the scene parent of the widget, avoids a segfault from the dangling pointer
        for spin in self.spinners:
            # spin.widget().setParent(None)
            spin.setWidget(
                None
            )  # Turns out this function calls the above commented out function
            self.scene().removeItem(spin)
        # del self.spinners # causes crashes

        self.scene().removeItem(self)


class Door(QGraphicsItem):
    Image = None
    DisabledImage = None

    def __init__(self, doorItem):
        QGraphicsItem.__init__(self)

        # Supplied entity info
        self.doorItem = doorItem

        self.blockingCount = 0

        self.setPos(self.doorItem[0] * 26 - 13, self.doorItem[1] * 26 - 13)
        self.setParentItem(mainWindow.scene.roomDoorRoot)

        tr = QTransform()
        if doorItem[0] in [0, 13]:
            tr.rotate(270)
            self.moveBy(-13, 0)
        elif doorItem[0] in [14, 27]:
            tr.rotate(90)
            self.moveBy(13, 0)
        elif doorItem[1] in [8, 15]:
            tr.rotate(180)
            self.moveBy(0, 13)
        else:
            self.moveBy(0, -13)

        if not Door.Image:
            Door.Image = QImage("resources/Backgrounds/Door.png")
            Door.DisabledImage = QImage("resources/Backgrounds/DisabledDoor.png")

        self.image = Door.Image.transformed(tr)
        self.disabledImage = Door.DisabledImage.transformed(tr)

    @property
    def exists(self):
        return self.doorItem[2]

    @exists.setter
    def exists(self, val):
        self.doorItem[2] = val

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
        self.exists = not self.exists

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
    # contains concrete room information necessary for examining a room's game qualities
    # such as type, variant, subtype, and shape information
    class Info:
        ########## SHAPE DEFINITIONS
        # w x h
        # 1 = 1x1, 2 = 1x0.5, 3 = 0.5x1, 4 = 1x2, 5 = 0.5x2, 6 = 2x1, 7 = 2x0.5, 8 = 2x2
        # 9 = DR corner, 10 = DL corner, 11 = UR corner, 12 = UL corner
        # all coords must be offset -1, -1 when saving
        Shapes = {
            1: {  # 1x1
                "Doors": [[7, 0], [0, 4], [14, 4], [7, 8]],
                # format: min, max on axis, cross axis coord, normal direction along cross axis
                "Walls": {
                    "X": [(0, 14, 0, 1), (0, 14, 8, -1)],
                    "Y": [(0, 8, 0, 1), (0, 8, 14, -1)],
                },
                "Dims": (15, 9),
            },
            2: {  # horizontal closet (1x0.5)
                "Doors": [[0, 4], [14, 4]],
                "Walls": {
                    "X": [(0, 14, 2, 1), (0, 14, 6, -1)],
                    "Y": [(2, 6, 0, 1), (2, 6, 14, -1)],
                },
                "TopLeft": 30,  # Grid coord
                "BaseShape": 1,  # Base Room shape this is rendered over
                "Dims": (15, 5),
            },
            3: {  # vertical closet (0.5x1)
                "Doors": [[7, 0], [7, 8]],
                "Walls": {
                    "X": [(4, 10, 0, 1), (4, 10, 8, -1)],
                    "Y": [(0, 8, 4, 1), (0, 8, 10, -1)],
                },
                "TopLeft": 4,
                "BaseShape": 1,
                "Dims": (7, 9),
            },
            4: {  # 1x2 room
                "Doors": [[7, 0], [14, 4], [0, 4], [14, 11], [0, 11], [7, 15]],
                "Walls": {
                    "X": [(0, 14, 0, 1), (0, 14, 15, -1)],
                    "Y": [(0, 15, 0, 1), (0, 15, 14, -1)],
                },
                "Dims": (15, 16),
            },
            5: {  # tall closet (0.5x2)
                "Doors": [[7, 0], [7, 15]],
                "Walls": {
                    "X": [(4, 10, 0, 1), (4, 10, 15, -1)],
                    "Y": [(0, 15, 4, 1), (0, 15, 10, -1)],
                },
                "TopLeft": 4,
                "BaseShape": 4,
                "Dims": (7, 16),
            },
            6: {  # 2x1 room
                "Doors": [[7, 0], [0, 4], [7, 8], [20, 8], [27, 4], [20, 0]],
                "Walls": {
                    "X": [(0, 27, 0, 1), (0, 27, 8, -1)],
                    "Y": [(0, 8, 0, 1), (0, 8, 27, -1)],
                },
                "Dims": (28, 9),
            },
            7: {  # wide closet (2x0.5)
                "Doors": [[0, 4], [27, 4]],
                "Walls": {
                    "X": [(0, 27, 2, 1), (0, 27, 6, -1)],
                    "Y": [(2, 6, 0, 1), (2, 6, 27, -1)],
                },
                "TopLeft": 56,
                "BaseShape": 6,
                "Dims": (28, 5),
            },
            8: {  # 2x2 room
                "Doors": [
                    [7, 0],
                    [0, 4],
                    [0, 11],
                    [20, 0],
                    [7, 15],
                    [20, 15],
                    [27, 4],
                    [27, 11],
                ],
                "Walls": {
                    "X": [(0, 27, 0, 1), (0, 27, 15, -1)],
                    "Y": [(0, 15, 0, 1), (0, 15, 27, -1)],
                },
                "Dims": (28, 16),
            },
            9: {  # mirrored L room
                "Doors": [
                    [20, 0],
                    [27, 4],
                    [7, 15],
                    [20, 15],
                    [13, 4],
                    [0, 11],
                    [27, 11],
                    [7, 7],
                ],
                "Walls": {
                    "X": [(0, 13, 7, 1), (13, 27, 0, 1), (0, 27, 15, -1)],
                    "Y": [(7, 15, 0, 1), (0, 7, 13, 1), (0, 15, 27, -1)],
                },
                "BaseShape": 8,
                "MirrorX": 10,
                "MirrorY": 11,
                "Dims": (28, 16),
            },
            10: {  # L room
                "Doors": [
                    [0, 4],
                    [14, 4],
                    [7, 0],
                    [20, 7],
                    [7, 15],
                    [20, 15],
                    [0, 11],
                    [27, 11],
                ],
                "Walls": {
                    "X": [(0, 14, 0, 1), (14, 27, 7, 1), (0, 27, 15, -1)],
                    "Y": [(0, 15, 0, 1), (0, 7, 14, -1), (7, 15, 27, -1)],
                },
                "BaseShape": 8,
                "MirrorX": 9,
                "MirrorY": 12,
                "Dims": (28, 16),
            },
            11: {  # mirrored r room
                "Doors": [
                    [0, 4],
                    [7, 8],
                    [7, 0],
                    [13, 11],
                    [20, 0],
                    [27, 4],
                    [20, 15],
                    [27, 11],
                ],
                "Walls": {
                    "X": [(0, 27, 0, 1), (0, 13, 8, -1), (13, 27, 15, -1)],
                    "Y": [(0, 8, 0, 1), (8, 15, 13, 1), (0, 15, 27, -1)],
                },
                "BaseShape": 8,
                "MirrorX": 12,
                "MirrorY": 9,
                "Dims": (28, 16),
            },
            12: {  # r room
                "Doors": [
                    [0, 4],
                    [7, 0],
                    [20, 0],
                    [14, 11],
                    [27, 4],
                    [7, 15],
                    [0, 11],
                    [20, 8],
                ],
                "Walls": {
                    "X": [(0, 27, 0, 1), (14, 27, 8, -1), (0, 14, 15, -1)],
                    "Y": [(0, 15, 0, 1), (8, 15, 14, -1), (0, 8, 27, -1)],
                },
                "BaseShape": 8,
                "MirrorX": 11,
                "MirrorY": 10,
                "Dims": (28, 16),
            },
        }

        for shape in Shapes.values():
            doorWalls = shape["DoorWalls"] = []
            for door in shape["Doors"]:
                door.append(True)
                for wall in shape["Walls"]["X"]:
                    if door[0] >= wall[0] and door[0] <= wall[1] and door[1] == wall[2]:
                        doorWalls.append((door, wall, "X"))
                        break
                for wall in shape["Walls"]["Y"]:
                    if door[1] >= wall[0] and door[1] <= wall[1] and door[0] == wall[2]:
                        doorWalls.append((door, wall, "Y"))

        def __init__(self, t=0, v=0, s=0, shape=1):
            self.type = t
            self.variant = v
            self.subtype = s
            self.shape = shape

        @property
        def shape(self):
            return self._shape

        @shape.setter
        def shape(self, val):
            self._shape = val
            self.shapeData = Room.Info.Shapes[self.shape]
            bs = self.shapeData.get("BaseShape")
            self.baseShapeData = bs and Room.Info.Shapes[bs]
            self.makeNewDoors()

        # represents the actual dimensions of the room, including out of bounds
        @property
        def dims(self):
            return (self.baseShapeData or self.shapeData)["Dims"]

        @property
        def width(self):
            return self.shapeData["Dims"][0]

        @property
        def height(self):
            return self.shapeData["Dims"][1]

        def makeNewDoors(self):
            self.doors = [door[:] for door in self.shapeData["Doors"]]

        def gridLen(self):
            dims = self.dims
            return dims[0] * dims[1]

        def gridIndex(x, y, w):
            return y * w + x

        def inFrontOfDoor(self, x, y):
            for door, wall, axis in self.shapeData["DoorWalls"]:
                if axis == "X" and door[0] == x and y - door[1] == wall[3]:
                    return door
                if axis == "Y" and door[1] == y and x - door[0] == wall[3]:
                    return door
            return None

        def _axisBounds(a, c, w):
            wMin, wMax, wLvl, wDir = w
            return a < wMin or a > wMax or ((c > wLvl) - (c < wLvl)) == wDir

        def isInBounds(self, x, y):
            return all(
                Room.Info._axisBounds(x, y, w) for w in self.shapeData["Walls"]["X"]
            ) and all(
                Room.Info._axisBounds(y, x, w) for w in self.shapeData["Walls"]["Y"]
            )

        def snapToBounds(self, x, y, dist=1):
            for w in self.shapeData["Walls"]["X"]:
                if not Room.Info._axisBounds(x, y, w):
                    y = w[2] + w[3] * dist

            for w in self.shapeData["Walls"]["Y"]:
                if not Room.Info._axisBounds(y, x, w):
                    x = w[2] + w[3] * dist

            return (x, y)

    def __init__(
        self,
        name="New Room",
        spawns=[],
        palette=None,
        difficulty=1,
        weight=1.0,
        myType=1,
        variant=0,
        subtype=0,
        shape=1,
        doors=None,
    ):
        """Initializes the room item."""

        QListWidgetItem.__init__(self)

        self.name = name

        self.info = Room.Info(myType, variant, subtype, shape)
        if doors:
            if len(self.info.doors) != len(doors):
                printf(f"{name} ({variant}): Invalid doors!", doors)
            self.info.doors = doors

        self.gridSpawns = spawns or [[] for x in range(self.info.gridLen())]
        if self.info.gridLen() != len(self.gridSpawns):
            printf(f"{name} ({variant}): Invalid grid spawns!")

        self.palette = palette or {}

        self.difficulty = difficulty
        self.weight = weight

        self.xmlProps = {}
        self._lastTestTime = None

        self.setFlags(self.flags() | Qt.ItemIsEditable)
        self.setToolTip()

        self.renderDisplayIcon()

    @property
    def difficulty(self):
        return self._difficulty

    @difficulty.setter
    def difficulty(self, d):
        self._difficulty = d
        if d == 20:
            self.setForeground(QColor(190, 0, 255))
        else:
            self.setForeground(QColor.fromHsvF(1, 1, min(max(d / 15, 0), 1), 1))

    @property
    def name(self):
        return self.data(0x100)

    @name.setter
    def name(self, n):
        self.setData(0x100, n)
        self.seed = hash(n)

    @property
    def gridSpawns(self):
        return self._gridSpawns

    @gridSpawns.setter
    def gridSpawns(self, g):
        self._gridSpawns = g

        self._spawnCount = 0
        for entStack in self.gridSpawns:
            if entStack:
                self._spawnCount += 1

    @property
    def lastTestTime(self):
        return self._lastTestTime

    @lastTestTime.setter
    def lastTestTime(self, t):
        self._lastTestTime = t
        self.setToolTip()

    DoorSortKey = lambda door: (door[0], door[1])

    def clearDoors(self):
        mainWindow.scene.clearDoors()
        for door in self.info.doors:
            d = Door(door)

    def getSpawnCount(self):
        return self._spawnCount

    def reshape(self, shape, doors=None):
        spawnIter = self.spawns()

        self.info.shape = shape
        if doors:
            self.info.doors = doors
        realWidth = self.info.dims[0]

        gridLen = self.info.gridLen()
        newGridSpawns = [[] for x in range(gridLen)]

        for stack, x, y in spawnIter:
            idx = Room.Info.gridIndex(x, y, realWidth)
            if idx < gridLen:
                newGridSpawns[idx] = stack

        self.gridSpawns = newGridSpawns

    def getDesc(self):
        name = self.name
        difficulty = self.difficulty
        weight = self.weight
        info = self.info
        return f"{name} ({info.type}.{info.variant}.{info.subtype}) ({info.width-2}x{info.height-2}) - Difficulty: {difficulty}, Weight: {weight}, Shape: {info.shape}"

    def setToolTip(self):
        self.setText(f"{self.info.variant} - {self.name}")

        lastTest = (
            "Never"
            if not self.lastTestTime
            else self.lastTestTime.astimezone().strftime("%x %I:%M %p")
        )

        tip = self.getDesc() + f"\nLast Tested: {lastTest}"

        QListWidgetItem.setToolTip(self, tip)

    def renderDisplayIcon(self):
        """Renders the mini-icon for display."""

        roomTypes = xmlLookups.roomTypes.lookup(room=self, showInMenu=True)
        if len(roomTypes) == 0:
            printf(
                "Warning: Unknown room type during renderDisplayIcon:", self.getDesc()
            )
            return

        i = QIcon(roomTypes[0].get("Icon"))
        self.setIcon(i)

    class _SpawnIter:
        def __init__(self, gridSpawns, dims):
            self.idx = -1
            self.spawns = gridSpawns
            self.width, self.height = dims

        def __iter__(self):
            return self

        def __next__(self):
            stack = None
            while True:
                self.idx += 1
                if self.idx >= self.width * self.height or self.idx >= len(self.spawns):
                    raise StopIteration

                stack = self.spawns[self.idx]
                if stack:
                    break
            x = int(self.idx % self.width)
            y = int(self.idx / self.width)
            return (stack, x, y)

    def spawns(self):
        return Room._SpawnIter(self.gridSpawns, self.info.dims)

    def setRoomBG(self, val=None):
        global xmlLookups

        if val is not None:
            self.roomBG = val
            return

        matchPath = mainWindow.path and os.path.split(mainWindow.path)[1]
        self.roomBG = xmlLookups.getRoomGfx(
            room=self, roomfile=mainWindow.roomList.file, path=matchPath
        )

    def mirrorX(self):
        # Flip spawns
        width, height = self.info.dims
        for y in range(height):
            for x in range(int(width / 2)):
                ox = Room.Info.gridIndex(x, y, width)
                mx = Room.Info.gridIndex(width - x - 1, y, width)
                oxs = self.gridSpawns[ox]
                self.gridSpawns[ox] = self.gridSpawns[mx]
                self.gridSpawns[mx] = oxs

        # Flip doors
        for door in self.info.doors:
            door[0] = width - door[0] - 1

        # Flip entities
        info = Entity.Info(changeAtStart=False)
        for stack, x, y in self.spawns():
            for spawn in stack:
                info.changeTo(spawn[0], spawn[1], spawn[2])

                # Directional entities
                if info.config.mirrorX:
                    for i in range(3):
                        spawn[i] = info.config.mirrorX[i]

                # Entities with subtypes that represent degrees
                if info.config.hasBitfields:
                    for bitfield in info.config.bitfields:
                        for element in bitfield.elements:
                            if element.unit == "Degrees":
                                angle = element.getWidgetValue(
                                    info.getBitfieldValue(bitfield)
                                )

                                # Convert to game direction, in degrees
                                angle = angle * (360 / (element.maximum + 1))
                                angle = (angle + 90) % 360

                                # Flip
                                x, y = vectorFromAngle(angle)
                                angle = angleFromVector(-x, y) % 360

                                # Convert to widget value, from degrees
                                angle = (angle / 360) * (element.maximum + 1)
                                angle = (angle + element.valueoffset) % (
                                    element.maximum + 1
                                )

                                info.setBitfieldElementValue(
                                    element, element.getRawValueFromWidgetValue(angle)
                                )
                                spawn[2] = info.Subtype

        # Flip shape
        shape = self.info.shapeData.get("MirrorX")
        if shape:
            self.reshape(shape, self.info.doors)

    def mirrorY(self):
        # Flip spawns
        width, height = self.info.dims
        for x in range(width):
            for y in range(int(height / 2)):
                oy = Room.Info.gridIndex(x, y, width)
                my = Room.Info.gridIndex(x, height - y - 1, width)
                oys = self.gridSpawns[oy]
                self.gridSpawns[oy] = self.gridSpawns[my]
                self.gridSpawns[my] = oys

        # Flip doors
        for door in self.info.doors:
            door[1] = height - door[1] - 1

        # Flip entities
        info = Entity.Info(changeAtStart=False)
        for stack, x, y in self.spawns():
            for spawn in stack:
                info.changeTo(spawn[0], spawn[1], spawn[2])

                # Directional entities
                if info.config.mirrorY:
                    for i in range(3):
                        spawn[i] = info.config.mirrorY[i]

                # Entities with subtypes that represent degrees
                if info.config.hasBitfields:
                    for bitfield in info.config.bitfields:
                        for element in bitfield.elements:
                            if element.unit == "Degrees":
                                angle = element.getWidgetValue(
                                    info.getBitfieldValue(bitfield)
                                )

                                # Convert to game direction, in degrees
                                angle = angle * (360 / (element.maximum + 1))
                                angle = (angle + 90) % 360

                                # Flip
                                x, y = vectorFromAngle(angle)
                                angle = angleFromVector(x, -y) % 360

                                # Convert to widget value, from degrees
                                angle = (angle / 360) * (element.maximum + 1)
                                angle = (angle + element.valueoffset) % (
                                    element.maximum + 1
                                )

                                info.setBitfieldElementValue(
                                    element, element.getRawValueFromWidgetValue(angle)
                                )
                                spawn[2] = info.Subtype

        # Flip shape
        shape = self.info.shapeData.get("MirrorY")
        if shape:
            self.reshape(shape, self.info.doors)


class RoomDelegate(QStyledItemDelegate):
    def __init__(self):
        self.pixmap = QPixmap("resources/UI/CurrentRoom.png")
        QStyledItemDelegate.__init__(self)

    def paint(self, painter, option, index):
        painter.fillRect(
            option.rect.right() - 19, option.rect.top(), 17, 16, QBrush(Qt.white)
        )

        QStyledItemDelegate.paint(self, painter, option, index)

        item = mainWindow.roomList.list.item(index.row())
        if item is not None and item.data(100):
            painter.drawPixmap(option.rect.right() - 19, option.rect.top(), self.pixmap)


class FilterMenu(QMenu):
    def __init__(self):
        QMenu.__init__(self)

    def paintEvent(self, event):
        QMenu.paintEvent(self, event)

        painter = QPainter(self)

        for act in self.actions():
            rect = self.actionGeometry(act)
            painter.fillRect(
                int(rect.right() / 2 - 12),
                rect.top() - 2,
                24,
                24,
                QBrush(Qt.transparent),
            )
            painter.drawPixmap(
                int(rect.right() / 2 - 12), rect.top() - 2, act.icon().pixmap(24, 24)
            )


class RoomSelector(QWidget):
    def __init__(self):
        """Initializes the widget."""

        QWidget.__init__(self)

        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)

        self.filterEntity = None

        self.file = None

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
        fq.load("resources/UI/FilterIcons.png")

        # Set the custom data
        self.filter.typeData = -1
        self.filter.sizeData = -1
        self.filter.extraData = {
            "enabled": False,
            "weight": {"min": 0, "max": 100000, "useRange": False, "enabled": False},
            "difficulty": {"min": 1, "max": 20, "useRange": False, "enabled": False},
            "subtype": {"min": 0, "max": 10, "useRange": False, "enabled": False},
            "lastTestTime": {
                "min": None,
                "max": None,
                "useRange": False,
                "enabled": False,
            },
            "tags": {"enabled": False, "mode": "Any", "tags": []},
        }

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

        self.typeToggle.setIcon(
            QIcon(QPixmap.fromImage(fq.copy(1 * 24 + 4, 4, 16, 16)))
        )
        act = typeMenu.addAction(
            QIcon(QPixmap.fromImage(fq.copy(1 * 24 + 4, 4, 16, 16))), ""
        )
        act.setData(-1)
        self.typeToggle.setDefaultAction(act)

        for iconType in xmlLookups.roomTypes.lookup(showInMenu=True):
            act = typeMenu.addAction(QIcon(iconType.get("Icon")), "")
            act.setData(int(iconType.get("Type")))

        self.typeToggle.triggered.connect(self.setTypeFilter)
        self.typeToggle.setMenu(typeMenu)

        # Weight Toggle Button
        class ExtraFilterToggle(QToolButton):
            def __init__(self):
                super(QToolButton, self).__init__()

            rightClicked = pyqtSignal()

            def mousePressEvent(self, e):
                if e.buttons() == Qt.RightButton:
                    self.rightClicked.emit()
                else:
                    self.clicked.emit()
                e.accept()

        self.extraToggle = ExtraFilterToggle()
        self.extraToggle.setIconSize(QSize(24, 24))
        self.extraToggle.setPopupMode(QToolButton.InstantPopup)

        self.extraToggle.setIcon(QIcon(QPixmap.fromImage(fq.copy(4 * 24, 0, 24, 24))))
        self.extraToggle.setToolTip("Right click for additional filter options")
        self.extraToggle.clicked.connect(self.setExtraFilter)
        self.extraToggle.rightClicked.connect(lambda: FilterDialog(self).exec())

        # Size Toggle Button
        self.sizeToggle = QToolButton()
        self.sizeToggle.setIconSize(QSize(24, 24))
        self.sizeToggle.setPopupMode(QToolButton.InstantPopup)

        sizeMenu = FilterMenu()

        q = QImage()
        q.load("resources/UI/ShapeIcons.png")

        self.sizeToggle.setIcon(QIcon(QPixmap.fromImage(fq.copy(3 * 24, 0, 24, 24))))
        act = sizeMenu.addAction(
            QIcon(QPixmap.fromImage(fq.copy(3 * 24, 0, 24, 24))), ""
        )
        act.setData(-1)
        act.setIconVisibleInMenu(False)
        self.sizeToggle.setDefaultAction(act)

        for i in range(12):
            act = sizeMenu.addAction(
                QIcon(QPixmap.fromImage(q.copy(i * 16, 0, 16, 16))), ""
            )
            act.setData(i + 1)
            act.setIconVisibleInMenu(False)

        self.sizeToggle.triggered.connect(self.setSizeFilter)
        self.sizeToggle.setMenu(sizeMenu)

        # Add to Layout
        self.filter.addWidget(QLabel("Filter by:"), 0, 0)
        self.filter.addWidget(self.IDFilter, 0, 1)
        self.filter.addWidget(self.entityToggle, 0, 2)
        self.filter.addWidget(self.typeToggle, 0, 3)
        self.filter.addWidget(self.sizeToggle, 0, 4)
        self.filter.addWidget(self.extraToggle, 0, 5)
        self.filter.setContentsMargins(4, 0, 0, 4)

        # Filter active notification and clear buttons

        # Palette
        self.clearAll = QToolButton()
        self.clearAll.setIconSize(QSize(24, 0))
        self.clearAll.setToolTip("Clear all filters")
        self.clearAll.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.clearAll.clicked.connect(self.clearAllFilter)

        self.clearName = QToolButton()
        self.clearName.setIconSize(QSize(24, 0))
        self.clearName.setToolTip("Clear name filter")
        self.clearName.setSizePolicy(self.IDFilter.sizePolicy())
        self.clearName.clicked.connect(self.clearNameFilter)

        self.clearEntity = QToolButton()
        self.clearEntity.setIconSize(QSize(24, 0))
        self.clearEntity.setToolTip("Clear entity filter")
        self.clearEntity.clicked.connect(self.clearEntityFilter)

        self.clearType = QToolButton()
        self.clearType.setIconSize(QSize(24, 0))
        self.clearType.setToolTip("Clear type filter")
        self.clearType.clicked.connect(self.clearTypeFilter)

        self.clearExtra = QToolButton()
        self.clearExtra.setIconSize(QSize(24, 0))
        self.clearExtra.setToolTip("Clear extra filter")
        self.clearExtra.clicked.connect(self.clearExtraFilter)

        self.clearSize = QToolButton()
        self.clearSize.setIconSize(QSize(24, 0))
        self.clearSize.setToolTip("Clear size filter")
        self.clearSize.clicked.connect(self.clearSizeFilter)

        self.filter.addWidget(self.clearAll, 1, 0)
        self.filter.addWidget(self.clearName, 1, 1)
        self.filter.addWidget(self.clearEntity, 1, 2)
        self.filter.addWidget(self.clearType, 1, 3)
        self.filter.addWidget(self.clearSize, 1, 4)
        self.filter.addWidget(self.clearExtra, 1, 5)

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
        self.list.itemSelectionChanged.connect(self.handleRoomListDisplayChanged)
        self.list.doubleClicked.connect(self.activateEdit)
        self.list.customContextMenuRequested.connect(self.customContextMenu)

        model = self.list.model()
        model.rowsInserted.connect(self.handleRoomListDisplayChanged)
        model.rowsRemoved.connect(self.handleRoomListDisplayChanged)
        model.modelReset.connect(
            self.handleRoomListDisplayChanged
        )  # fired when cleared

        self.list.itemDelegate().closeEditor.connect(self.editComplete)

    def setupToolbar(self):
        self.toolbar = QToolBar()

        self.addRoomButton = self.toolbar.addAction(QIcon(), "Add", self.addRoom)
        self.removeRoomButton = self.toolbar.addAction(
            QIcon(), "Delete", self.removeRoom
        )
        self.duplicateRoomButton = self.toolbar.addAction(
            QIcon(), "Duplicate", self.duplicateRoom
        )
        self.duplicateRoomButton.setToolTip(
            "Duplicate selected room.\nAlt: Mirror X and Duplicate\nAlt+Shift: Mirror Y and Duplicate"
        )
        self.exportRoomButton = self.toolbar.addAction(
            QIcon(), "Copy to File...", self.exportRoom
        )
        self.toolbar.addSeparator()

        self.numRoomsLabel = QLabel()
        self.numRoomsLabel.setIndent(10)
        self.toolbar.addWidget(self.numRoomsLabel)

        self.mirror = False
        self.mirrorY = False
        # self.IDButton = self.toolbar.addAction(QIcon(), 'ID', self.turnIDsOn)
        # self.IDButton.setCheckable(True)
        # self.IDButton.setChecked(True)

    def handleRoomListDisplayChanged(self):
        selectedRooms = len(self.selectedRooms())

        numRooms = selectedRooms
        if numRooms < 2:
            numRooms = 0
            for room in self.getRooms():
                if not room.isHidden():
                    numRooms += 1

        self.numRoomsLabel.setText(
            f"{'Selected rooms' if selectedRooms > 1 else 'Num Rooms'}: {numRooms}"
            if numRooms > 0
            else ""
        )

    def activateEdit(self):
        room = self.selectedRoom()
        room.setText(room.name)
        self.list.editItem(self.selectedRoom())

    def editComplete(self, lineEdit):
        room = self.selectedRoom()
        room.name = lineEdit.text()
        room.setText(f"{room.info.variant} - {room.name}")
        mainWindow.dirt()

    # @pyqtSlot(bool)
    def turnIDsOn(self):
        return

    # @pyqtSlot(QPoint)
    def customContextMenu(self, pos):
        if not self.selectedRoom():
            return

        menu = QMenu(self.list)

        # Type
        Type = QWidgetAction(menu)
        c = QComboBox()

        global xmlLookups
        types = xmlLookups.roomTypes.lookup(showInMenu=True)
        matchingTypes = xmlLookups.roomTypes.lookup(
            room=self.selectedRoom(), showInMenu=True
        )

        for i, t in enumerate(types):
            c.addItem(QIcon(t.get("Icon")), t.get("Name"))
            if t in matchingTypes:
                c.setCurrentIndex(i)

        c.currentIndexChanged.connect(self.changeType)
        Type.setDefaultWidget(c)
        menu.addAction(Type)

        # Variant
        Variant = QWidgetAction(menu)
        s = QSpinBox()
        s.setRange(0, 65534)
        s.setPrefix("ID - ")

        s.setValue(self.selectedRoom().info.variant)

        Variant.setDefaultWidget(s)
        s.valueChanged.connect(self.changeVariant)
        menu.addAction(Variant)

        menu.addSeparator()

        # Difficulty
        Difficulty = QWidgetAction(menu)
        dv = QSpinBox()
        dv.setRange(0, 20)
        dv.setPrefix("Difficulty - ")

        dv.setValue(self.selectedRoom().difficulty)

        Difficulty.setDefaultWidget(dv)
        dv.valueChanged.connect(self.changeDifficulty)
        menu.addAction(Difficulty)

        # Weight
        weight = QWidgetAction(menu)
        s = QDoubleSpinBox()
        s.setPrefix("Weight - ")

        s.setValue(self.selectedRoom().weight)

        weight.setDefaultWidget(s)
        s.valueChanged.connect(self.changeWeight)
        menu.addAction(weight)

        # Subtype
        Subtype = QWidgetAction(menu)
        st = QSpinBox()
        st.setRange(0, 4096)
        st.setPrefix("Sub - ")

        st.setValue(self.selectedRoom().info.subtype)

        Subtype.setDefaultWidget(st)
        st.valueChanged.connect(self.changeSubtype)
        menu.addAction(Subtype)

        menu.addSeparator()

        # Room shape
        Shape = QWidgetAction(menu)
        c = QComboBox()

        q = QImage()
        q.load("resources/UI/ShapeIcons.png")

        for shapeName in range(1, 13):
            c.addItem(
                QIcon(QPixmap.fromImage(q.copy((shapeName - 1) * 16, 0, 16, 16))),
                str(shapeName),
            )
        c.setCurrentIndex(self.selectedRoom().info.shape - 1)
        c.currentIndexChanged.connect(self.changeSize)
        Shape.setDefaultWidget(c)
        menu.addAction(Shape)

        # End it
        menu.exec(self.list.mapToGlobal(pos))

    # @pyqtSlot(bool)
    def clearAllFilter(self):
        self.IDFilter.clear()
        self.entityToggle.setChecked(False)
        self.filter.typeData = -1
        self.typeToggle.setIcon(self.typeToggle.defaultAction().icon())
        self.filter.sizeData = -1
        self.sizeToggle.setIcon(self.sizeToggle.defaultAction().icon())

        self.filter.extraData["enabled"] = False

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

    def clearExtraFilter(self):
        self.filter.extraData["enabled"] = False
        self.changeFilter()

    def clearSizeFilter(self):
        self.filter.sizeData = -1
        self.sizeToggle.setIcon(self.sizeToggle.defaultAction().icon())
        self.changeFilter()

    # @pyqtSlot(bool)
    def setEntityToggle(self, checked):
        self.entityToggle.checked = checked

    # @pyqtSlot(QAction)
    def setTypeFilter(self, action):
        self.filter.typeData = action.data()
        self.typeToggle.setIcon(action.icon())
        self.changeFilter()

    # @pyqtSlot(QAction)
    def setExtraFilter(self, checked, force=None):
        if force is None:
            force = not self.filter.extraData["enabled"]  # toggle on click

        self.filter.extraData["enabled"] = force
        self.changeFilter()

    # @pyqtSlot(QAction)
    def setSizeFilter(self, action):
        self.filter.sizeData = action.data()
        self.sizeToggle.setIcon(action.icon())
        self.changeFilter()

    def colorizeClearFilterButtons(self):
        colour = "background-color: #F00;"

        all = False

        # Name Button
        if self.IDFilter.text():
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
        if self.filter.typeData >= 0:
            self.clearType.setStyleSheet(colour)
            all = True
        else:
            self.clearType.setStyleSheet("")

        # Size Button
        if self.filter.sizeData >= 0:
            self.clearSize.setStyleSheet(colour)
            all = True
        else:
            self.clearSize.setStyleSheet("")

        # Extra filters Button
        if self.filter.extraData["enabled"]:
            self.clearExtra.setStyleSheet(colour)
            all = True
        else:
            self.clearExtra.setStyleSheet("")

        # All Button
        if all:
            self.clearAll.setStyleSheet(colour)
        else:
            self.clearAll.setStyleSheet("")

    # @pyqtSlot()
    def changeFilter(self):
        self.colorizeClearFilterButtons()

        # Here we go
        for room in self.getRooms():
            IDCond = entityCond = typeCond = sizeCond = extraCond = True

            IDCond = self.IDFilter.text().lower() in room.text().lower()

            # Check if the right entity is in the room
            if self.entityToggle.checked and self.filterEntity:
                entityCond = self.filterEntity.config.uniqueid in room.palette

            # Check if the room is the right type
            if self.filter.typeData != -1:
                # All the normal rooms
                typeCond = self.filter.typeData == room.info.type

                # For null rooms, include "empty" rooms regardless of type
                if not typeCond and self.filter.typeData == 0:
                    nonCombatRooms = settings.value("NonCombatRoomFilter") == "1"
                    checkTags = ["InEmptyRooms"]
                    if nonCombatRooms:
                        checkTags.append("InNonCombatRooms")

                    hasUsefulEntities = any(
                        not config.matches(tags=checkTags, matchAnyTag=True)
                        for config in room.palette.values()
                    )

                    typeCond = not hasUsefulEntities

            if self.filter.extraData["enabled"]:
                # Check if the room is the right weight
                weightData = self.filter.extraData["weight"]
                if extraCond and weightData["enabled"]:
                    if weightData["useRange"]:
                        extraCond = (
                            extraCond
                            and weightData["min"] <= room.weight <= weightData["max"]
                        )
                    else:
                        eps = 0.0001
                        extraCond = (
                            extraCond and abs(weightData["min"] - room.weight) < eps
                        )

                # Check if the room is the right difficulty
                difficultyData = self.filter.extraData["difficulty"]
                if extraCond and difficultyData["enabled"]:
                    if difficultyData["useRange"]:
                        extraCond = (
                            extraCond
                            and difficultyData["min"]
                            <= room.difficulty
                            <= difficultyData["max"]
                        )
                    else:
                        extraCond = difficultyData["min"] == room.difficulty

                # Check if the room is the right subtype
                subtypeData = self.filter.extraData["subtype"]
                if extraCond and subtypeData["enabled"]:
                    if subtypeData["useRange"]:
                        extraCond = (
                            extraCond
                            and subtypeData["min"]
                            <= room.info.subtype
                            <= subtypeData["max"]
                        )
                    else:
                        extraCond = subtypeData["min"] == room.info.subtype

                # Check if the room has been tested between a specific time range,
                # or tested before a certain date
                lastTestTimeData = self.filter.extraData["lastTestTime"]
                if extraCond and lastTestTimeData["enabled"]:
                    if lastTestTimeData["useRange"]:
                        # intentionally reversed; min is always the main value, but the default comparison for last time is for earlier times
                        extraCond = (
                            extraCond
                            and room.lastTestTime
                            and lastTestTimeData["max"]
                            <= room.lastTestTime
                            <= lastTestTimeData["min"]
                        )
                    else:
                        extraCond = extraCond and (
                            not room.lastTestTime
                            or room.lastTestTime <= lastTestTimeData["min"]
                        )

                # Check if the room contains entities with certain tags
                tagsData = self.filter.extraData["tags"]
                if extraCond and tagsData["enabled"]:
                    checkTags = tagsData["tags"]
                    matchAnyTag = (
                        tagsData["mode"] == "Any" or tagsData["mode"] == "Blacklist"
                    )
                    checkUnmatched = tagsData["mode"] == "Exclusive"

                    matched = any(
                        config.matches(tags=checkTags, matchAnyTag=matchAnyTag)
                        != checkUnmatched
                        for config in room.palette.values()
                    )

                    if tagsData["mode"] == "Blacklist":
                        extraCond = not matched
                    elif tagsData["mode"] == "Exclusive":
                        extraCond = not matched
                    else:
                        extraCond = matched

            # Check if the room is the right size
            if self.filter.sizeData != -1:
                sizeCond = self.filter.sizeData == room.info.shape

            # Filter em' out
            isMatch = IDCond and entityCond and typeCond and sizeCond and extraCond
            room.setHidden(not isMatch)

        self.handleRoomListDisplayChanged()

    def setEntityFilter(self, entity):
        self.filterEntity = entity
        self.entityToggle.setIcon(entity.icon)
        if self.entityToggle.checked:
            self.changeFilter()

    def changeSize(self, shapeIdx):
        # Set the Size - gotta lotta shit to do here
        s = shapeIdx + 1

        # No sense in doing work we don't have to!
        if self.selectedRoom().info.shape == s:
            return

        info = Room.Info(shape=s)
        w, h = info.dims

        # Check to see if resizing will destroy any entities
        mainWindow.storeEntityList()

        warn = any(x >= w or y >= h for stack, x, y in self.selectedRoom().spawns())

        if warn:
            msgBox = QMessageBox(
                QMessageBox.Warning,
                "Resize Room?",
                "Resizing this room will delete entities placed outside the new size. Are you sure you want to resize this room?",
                QMessageBox.NoButton,
                self,
            )
            msgBox.addButton("Resize", QMessageBox.AcceptRole)
            msgBox.addButton("Cancel", QMessageBox.RejectRole)
            if msgBox.exec_() == QMessageBox.RejectRole:
                # It's time for us to go now.
                return

        self.selectedRoom().reshape(s)

        # Clear the room and reset the size
        mainWindow.scene.clear()

        self.selectedRoom().clearDoors()

        mainWindow.scene.newRoomSize(s)

        mainWindow.editor.resizeEvent(
            QResizeEvent(mainWindow.editor.size(), mainWindow.editor.size())
        )

        # Spawn those entities
        for entStack, x, y in self.selectedRoom().spawns():
            if x >= w or y >= h:
                continue

            for entity in entStack:
                e = Entity(
                    x, y, entity[0], entity[1], entity[2], entity[3], respawning=True
                )

        self.selectedRoom().setToolTip()
        mainWindow.dirt()

    # @pyqtSlot(int)
    def changeType(self, index):
        for r in self.selectedRooms():
            r.info.type = index
            r.renderDisplayIcon()
            r.setRoomBG()

            r.setToolTip()

        mainWindow.scene.updateRoomDepth(self.selectedRoom())
        mainWindow.scene.update()
        mainWindow.dirt()

    # @pyqtSlot(int)
    def changeVariant(self, var):
        for r in self.selectedRooms():
            r.info.variant = var
            r.setToolTip()
        mainWindow.dirt()
        mainWindow.scene.update()

    # @pyqtSlot(int)
    def changeSubtype(self, var):
        for r in self.selectedRooms():
            r.info.subtype = var
            r.setToolTip()
        mainWindow.dirt()
        mainWindow.scene.update()

    # @pyqtSlot(QAction)
    def changeDifficulty(self, var):
        for r in self.selectedRooms():
            r.difficulty = var
            r.setToolTip()
        mainWindow.dirt()
        mainWindow.scene.update()

    # @pyqtSlot(QAction)
    def changeWeight(self, action):
        for r in self.selectedRooms():
            # r.weight = float(action.text())
            r.weight = action
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
        self.list.insertItem(self.list.currentRow() + 1, r)
        self.list.setCurrentItem(r, QItemSelectionModel.ClearAndSelect)
        mainWindow.dirt()

    def removeRoom(self):
        """Removes selected room (no takebacks)"""

        rooms = self.selectedRooms()
        if rooms is None or len(rooms) == 0:
            return

        msgBox = QMessageBox(
            QMessageBox.Warning,
            "Delete Room?",
            "Are you sure you want to delete the selected rooms? This action cannot be undone.",
            QMessageBox.NoButton,
            self,
        )
        msgBox.addButton("Delete", QMessageBox.AcceptRole)
        msgBox.addButton("Cancel", QMessageBox.RejectRole)
        if msgBox.exec_() == QMessageBox.AcceptRole:
            self.list.clearSelection()
            for item in rooms:
                self.list.takeItem(self.list.row(item))

            self.list.scrollToItem(self.list.currentItem())
            self.list.setCurrentItem(
                self.list.currentItem(), QItemSelectionModel.Select
            )
            mainWindow.dirt()

    def duplicateRoom(self):
        """Duplicates the selected room"""

        rooms = self.orderedSelectedRooms()
        if not rooms:
            return

        numRooms = len(rooms)

        mainWindow.storeEntityList()

        lastPlace = self.list.indexFromItem(rooms[-1]).row() + 1
        self.selectedRoom().setData(100, False)
        self.list.setCurrentItem(None, QItemSelectionModel.ClearAndSelect)

        for room in reversed(rooms):
            if self.mirrorY:
                v = 20000
                extra = " (flipped Y)"
            elif self.mirror:
                v = 10000
                extra = " (flipped X)"
            else:
                v = numRooms
                extra = " (copy)"

            usedRoomName = room.name
            if extra in room.name and extra != "":
                extraCount = room.name.count(extra)
                regSearch = QRegularExpression(" \((\d*)\)")
                counterMatches = regSearch.match(room.name)
                if counterMatches.hasMatch():
                    counter = counterMatches.captured(
                        counterMatches.lastCapturedIndex()
                    )
                    extraCount = extraCount + int(counter)
                usedRoomName = room.name.split(extra)[0]
                extra = extra + " (" + str(extraCount) + ")"

            r = Room(
                deepcopy(usedRoomName + extra),
                deepcopy(room.gridSpawns),
                deepcopy(room.palette),
                deepcopy(room.difficulty),
                deepcopy(room.weight),
                deepcopy(room.info.type),
                deepcopy(room.info.variant + v),
                deepcopy(room.info.subtype),
                deepcopy(room.info.shape),
                deepcopy([list(door) for door in room.info.doors]),
            )
            r.xmlProps = deepcopy(room.xmlProps)

            # Mirror the room
            if self.mirror:
                if self.mirrorY:
                    r.mirrorY()
                else:
                    r.mirrorX()

            self.list.insertItem(lastPlace, r)
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
        dialogDir = mainWindow.getRecentFolder()

        target, match = QFileDialog.getSaveFileName(
            self,
            "Select a new name or an existing XML",
            dialogDir,
            "XML File (*.xml)",
            "",
            QFileDialog.DontConfirmOverwrite,
        )
        mainWindow.restoreEditMenu()

        if len(target) == 0:
            return

        path = target

        rooms = self.orderedSelectedRooms()
        # Append these rooms onto the existing file
        if os.path.exists(path):
            oldRooms = mainWindow.open(path)
            oldRooms.rooms.extend(rooms)
            mainWindow.save(oldRooms.rooms, path, fileObj=oldRooms)
        # Make a new file with the selected rooms
        else:
            mainWindow.save(rooms, path, fileObj=self.file)

    def setButtonStates(self):
        rooms = len(self.selectedRooms()) > 0

        self.removeRoomButton.setEnabled(rooms)
        self.duplicateRoomButton.setEnabled(rooms)
        self.exportRoomButton.setEnabled(rooms)

    def selectedRoom(self):
        return self.list.currentItem()

    def selectedRooms(self):
        return self.list.selectedItems()

    def orderedSelectedRooms(self):
        sortedIndexes = sorted(
            self.list.selectionModel().selectedIndexes(),
            key=lambda x: (x.column(), x.row()),
        )
        return [self.list.itemFromIndex(i) for i in sortedIndexes]

    def getRooms(self):
        return [self.list.item(i) for i in range(self.list.count())]


# Entity Palette
########################


class EntityGroupItem(QStandardItem):
    """Group Item to contain Entities for sorting"""

    def __init__(self, group, startIndex=0):
        QStandardItem.__init__(self)

        self.objects = []
        self.config = group

        self.startIndex = startIndex

        self.name = group.label or ""
        self.entitycount = 0

        # Labelled groups are added last, so that loose entities are below the main group header.
        labelledGroups = []

        global xmlLookups
        endIndex = startIndex
        for entry in group.entries:
            endIndex += 1
            if isinstance(entry, xmlLookups.entities.GroupConfig):
                if entry.label:
                    labelledGroups.append(entry)
                    endIndex -= 1
                else:
                    groupItem = EntityGroupItem(entry, endIndex)
                    endIndex = groupItem.endIndex
                    self.entitycount += groupItem.entitycount
                    self.objects.append(groupItem)
            elif isinstance(entry, xmlLookups.entities.EntityConfig):
                self.entitycount += 1
                self.objects.append(EntityItem(entry))

        for entry in labelledGroups:
            endIndex += 1
            groupItem = EntityGroupItem(entry, endIndex)
            endIndex = groupItem.endIndex
            self.entitycount += groupItem.entitycount
            self.objects.append(groupItem)

        self.endIndex = endIndex

        self.alignment = Qt.AlignCenter

        self.collapsed = False

    def getItem(self, index):
        """Retrieves an item of a specific index. The index is already checked for validity"""

        if index == self.startIndex:
            return self

        checkIndex = self.startIndex
        for obj in self.objects:
            if isinstance(obj, EntityGroupItem):
                if index >= obj.startIndex and index <= obj.endIndex:
                    return obj.getItem(index)
                else:
                    checkIndex = obj.endIndex
            else:
                checkIndex += 1
                if checkIndex == index:
                    return obj

    def filterView(self, view, shownEntities=None, parentCollapsed=False):
        hideDuplicateEntities = settings.value("HideDuplicateEntities") == "1"

        if shownEntities is None:
            shownEntities = {}

        hasAnyVisible = False

        collapsed = self.collapsed or parentCollapsed

        row = self.startIndex
        for item in self.objects:
            if isinstance(item, EntityItem):
                row += 1
                hidden = False
                if view.filter.lower() not in item.name.lower():
                    hidden = True
                elif hideDuplicateEntities and item.config.uniqueid in shownEntities:
                    hidden = True

                view.setRowHidden(row, collapsed or hidden)
                if not hidden:
                    shownEntities[item.config.uniqueid] = True
                    hasAnyVisible = True
            elif isinstance(item, EntityGroupItem):
                row = item.endIndex
                visible = item.filterView(view, shownEntities, collapsed)
                hasAnyVisible = hasAnyVisible or visible

        if not hasAnyVisible or self.name == "" or parentCollapsed:
            view.setRowHidden(self.startIndex, True)
        else:
            view.setRowHidden(self.startIndex, False)

        return hasAnyVisible


class EntityItem(QStandardItem):
    """A single entity palette entry, not the in-editor Entity"""

    def __init__(self, config):
        QStandardItem.__init__(self)

        self.name = config.name
        self.ID = config.type
        self.variant = config.variant
        self.subtype = config.subtype
        self.icon = QIcon(config.imagePath)
        self.config = config

        self.setToolTip(self.name)


class EntityGroupModel(QAbstractListModel):
    """Model containing all the grouped objects in a tileset"""

    def __init__(self, group=None):
        QAbstractListModel.__init__(self)

        self.view = None

        if group is None:
            group = xmlLookups.entities.entityList

        self.group = EntityGroupItem(group)

    def rowCount(self, parent=None):
        return self.group.endIndex + 1

    def flags(self, index):
        item = self.getItem(index.row())

        if isinstance(item, EntityGroupItem):
            return Qt.ItemIsEnabled
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def getItem(self, index):
        return self.group.getItem(index)

    def data(self, index, role=Qt.DisplayRole):
        # Should return the contents of a row when asked for the index
        #
        # Can be optimized by only dealing with the roles we need prior
        # to lookup: Role order is 13, 6, 7, 9, 10, 1, 0, 8

        if (role > 1) and (role < 6):
            return None

        elif role == Qt.ForegroundRole:
            return QBrush(Qt.black)

        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

        if not index.isValid():
            return None
        n = index.row()

        if n < 0:
            return None
        if n >= self.rowCount():
            return None

        item = self.getItem(n)

        if role == Qt.DecorationRole:
            if isinstance(item, EntityItem):
                return item.icon

        if (
            role == Qt.ToolTipRole
            or role == Qt.StatusTipRole
            or role == Qt.WhatsThisRole
        ):
            if isinstance(item, EntityItem):
                return "{0}".format(item.name)

        elif role == Qt.DisplayRole:
            if isinstance(item, EntityGroupItem):
                return item.name + (" ▶" if item.collapsed else "")

        elif role == Qt.SizeHintRole:
            if isinstance(item, EntityGroupItem):
                return QSize(self.view.viewport().width(), 24)

        elif role == Qt.BackgroundRole:
            if isinstance(item, EntityGroupItem):
                colour = 165

                if colour > 255:
                    colour = 255

                brush = QBrush(QColor(colour, colour, colour), Qt.Dense4Pattern)

                return brush

        elif role == Qt.FontRole:
            font = QFont()
            font.setPixelSize(16)
            font.setBold(True)

            return font

        return None


class EntityPalette(QWidget):
    def __init__(self):
        """Initializes the widget. Remember to call setTileset() on it
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
        listView.setModel(EntityGroupModel())
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
        for tab in xmlLookups.entities.tabs:
            model = EntityGroupModel(tab)
            if model.group.entitycount != 0:
                listView = EntityList()
                printf(
                    f'Populating palette tab "{tab.name}" with {model.group.entitycount} entities'
                )

                listView.setModel(model)
                listView.model().view = listView
                listView.filterList()

                listView.clicked.connect(self.objSelected)

                if tab.iconSize:
                    listView.setIconSize(QSize(tab.iconSize[0], tab.iconSize[1]))

                self.tabs.addTab(listView, tab.name)
            else:
                printf(f"Skipping empty palette tab {tab.name}")

    def currentSelectedObject(self):
        """Returns the currently selected object reference, for painting purposes."""

        if len(self.searchBar.text()) > 0:
            index = self.searchTab.currentWidget().currentIndex().row()
            obj = self.searchTab.currentWidget().model().getItem(index)
        else:
            index = self.tabs.currentWidget().currentIndex().row()
            obj = self.tabs.currentWidget().model().getItem(index)

        return obj

    # @pyqtSlot()
    def objSelected(self):
        """Throws a signal emitting the current object when changed"""

        current = self.currentSelectedObject()
        if current is None:
            return

        if isinstance(current, EntityGroupItem):
            current.collapsed = not current.collapsed
            self.tabs.currentWidget().filterList()
            return

        # holding ctrl skips the filter change step
        kb = int(QGuiApplication.keyboardModifiers())

        holdCtrl = kb & Qt.ControlModifier != 0
        pinEntityFilter = settings.value("PinEntityFilter") == "1"
        self.objChanged.emit(current, holdCtrl == pinEntityFilter)

        # Throws a signal when the selected object is used as a replacement
        if kb & Qt.AltModifier != 0:
            self.objReplaced.emit(current)

    # @pyqtSlot()
    def updateSearch(self, text):
        if len(self.searchBar.text()) > 0:
            self.tabs.hide()
            self.searchTab.widget(0).filter = text
            self.searchTab.widget(0).filterList()
            self.searchTab.show()
        else:
            self.tabs.show()
            self.searchTab.hide()

    def updateTabs(self):
        for i in range(0, self.tabs.count()):
            self.tabs.widget(i).filterList()

    objChanged = pyqtSignal(EntityItem, bool)
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

        if index != -1:
            item = self.model().getItem(index)

            if isinstance(item, EntityItem):
                QToolTip.showText(event.globalPos(), item.name)

    def filterList(self):
        m = self.model()
        rows = m.rowCount()

        m.group.filterView(self)


class ReplaceDialog(QDialog):
    class EntSpinners(QWidget):
        def __init__(self):
            super(QWidget, self).__init__()
            layout = QFormLayout()

            self.type = QSpinBox()
            self.type.setRange(1, 2**31 - 1)
            self.variant = QSpinBox()
            self.variant.setRange(-1, 2**31 - 1)
            self.subtype = QSpinBox()
            self.subtype.setRange(-1, 2**8 - 1)

            layout.addRow("&Type:", self.type)
            layout.addRow("&Variant:", self.variant)
            layout.addRow("&Subtype:", self.subtype)

            self.entity = Entity.Info(0, 0, 0, 0, 0, 0, changeAtStart=False)

            self.type.valueChanged.connect(self.resetEnt)
            self.variant.valueChanged.connect(self.resetEnt)
            self.subtype.valueChanged.connect(self.resetEnt)

            self.setLayout(layout)

        def getEnt(self):
            return (self.type.value(), self.variant.value(), self.subtype.value())

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
            spinners.valueChanged.connect(
                lambda: icon.setPixmap(spinners.entity.pixmap)
            )
            info.addWidget(icon)
            infoWidget = QWidget()
            infoWidget.setLayout(info)
            return infoWidget, spinners

        fromInfo, self.fromEnt = genEnt("From")
        toInfo, self.toEnt = genEnt("To")

        selection = mainWindow.scene.selectedItems()
        if len(selection) > 0:
            selection = selection[0].entity
            self.fromEnt.setEnt(
                int(selection.Type), int(selection.Variant), int(selection.Subtype)
            )
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
            self.setToolTip(tooltip)
            self.setting = setting

        @property
        def val(self):
            settings = QSettings("settings.ini", QSettings.IniFormat)
            return settings.value(self.setting, [])

        @val.setter
        def val(self, v):
            settings = QSettings("settings.ini", QSettings.IniFormat)
            res = v
            if v is None:
                settings.remove(self.setting)
            else:
                settings.setValue(self.setting, res)

    def __init__(self, parent):
        super(QDialog, self).__init__(parent)
        self.setWindowTitle("Set Hooks")

        self.layout = QHBoxLayout()

        hookTypes = [
            (
                "On Save File",
                "HooksSave",
                "Runs on saved room files whenever a full save is performed",
            ),
            (
                "On Test Room",
                "HooksTest",
                "Runs on output room xmls when preparing to test the current room",
            ),
        ]

        self.hooks = QListWidget()
        for hook in hookTypes:
            self.hooks.addItem(HooksDialog.HookItem(*hook))
        self.layout.addWidget(self.hooks)

        pane = QVBoxLayout()
        pane.setContentsMargins(0, 0, 0, 0)
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
        return [
            self.content.item(i).text() for i in range(self.content.count())
        ] or None

    def setPaths(self, val):
        self.content.clear()
        if not val:
            return
        self.content.addItems(val)

    def displayHook(self, new, old):
        if old:
            old.val = self.contentPaths()
        self.setPaths(new.val)

    def insertPath(self, path=None):
        path = path or findModsPath()

        target, _ = QFileDialog.getOpenFileName(
            self, "Select script", os.path.normpath(path), "All files (*)"
        )
        return target

    def addPath(self):
        path = self.insertPath()
        if path != "":
            self.content.addItem(path)

    def editPath(self):
        item = self.content.currentItem()
        if not item:
            return

        path = self.insertPath(item.text())
        if path != "":
            item.setText(path)

    def deletePath(self):
        if self.content.currentItem():
            self.content.takeItem(self.content.currentRow())

    def closeEvent(self, evt):
        current = self.hooks.currentItem()
        if current:
            current.val = self.contentPaths()
        QWidget.closeEvent(self, evt)


class TestConfigDialog(QDialog):
    class ConfigItem(QLabel):
        def __init__(self, text, setting, tooltip, default=None):
            super(QLabel, self).__init__(text)
            self.setToolTip(tooltip)
            self.setting = setting
            self.default = default

        @property
        def val(self):
            settings = QSettings("settings.ini", QSettings.IniFormat)
            return settings.value(self.setting, self.default)

        @val.setter
        def val(self, v):
            settings = QSettings("settings.ini", QSettings.IniFormat)
            res = v
            if v is None:
                settings.remove(self.setting)
            else:
                settings.setValue(self.setting, res)

    def __init__(self, parent):
        super(QDialog, self).__init__(parent)
        self.setWindowTitle("Test Configuration")

        self.layout = QVBoxLayout()

        version = getGameVersion()

        # character
        characterLayout = QHBoxLayout()
        self.characterConfig = TestConfigDialog.ConfigItem(
            "Character",
            "TestCharacter",
            "Character to switch to when testing. (Isaac, Magdalene, etc.) If omitted, use the game's default",
        )
        self.characterEntry = QLineEdit()
        characterLayout.addWidget(self.characterConfig)
        characterLayout.addWidget(self.characterEntry)
        characterWidget = QWidget()
        characterWidget.setLayout(characterLayout)
        if version not in ["Repentance"]:
            characterWidget.setEnabled(False)
        self.layout.addWidget(characterWidget)

        # commands
        commandLayout = QVBoxLayout()
        self.commandConfig = TestConfigDialog.ConfigItem(
            "Debug Commands",
            "TestCommands",
            "Debug Console Commands that will get run one at a time after other BR initialization has finished",
            [],
        )
        pane = QVBoxLayout()
        pane.setContentsMargins(0, 0, 0, 0)
        paneWidget = QWidget()
        paneWidget.setLayout(pane)

        self.commandList = QListWidget()
        pane.addWidget(self.commandList)

        addButton = QPushButton("Add")
        editButton = QPushButton("Edit")
        deleteButton = QPushButton("Delete")

        buttons = QHBoxLayout()
        buttons.addWidget(addButton)
        buttons.addWidget(deleteButton)
        pane.addLayout(buttons)

        commandLayout.addWidget(self.commandConfig)
        commandLayout.addWidget(paneWidget)

        commandWidget = QWidget()
        commandWidget.setLayout(commandLayout)

        self.layout.addWidget(commandWidget, 1)

        # enable/disable
        enableLayout = QHBoxLayout()
        self.enableConfig = TestConfigDialog.ConfigItem(
            "Enabled",
            "TestConfigDisabled",
            "Enable/disable the test config bonus settings",
        )
        self.enableCheck = QCheckBox("Enabled")
        self.enableCheck.setToolTip(self.enableConfig.toolTip())
        enableLayout.addWidget(self.enableCheck)
        enableWidget = QWidget()
        enableWidget.setLayout(enableLayout)
        self.layout.addWidget(enableWidget)

        addButton.clicked.connect(self.addCommand)
        deleteButton.clicked.connect(self.deleteCommand)

        self.setValues()

        self.setLayout(self.layout)

    def enabled(self):
        return None if self.enableCheck.isChecked() else "1"

    def character(self):
        return self.characterEntry.text() or None

    def commands(self):
        return [
            self.commandList.item(i).text() for i in range(self.commandList.count())
        ] or None

    def setValues(self):
        self.enableCheck.setChecked(self.enableConfig.val != "1")
        self.characterEntry.setText(self.characterConfig.val)
        self.commandList.clear()
        self.commandList.addItems(self.commandConfig.val)
        for i in range(self.commandList.count()):
            item = self.commandList.item(i)
            item.setFlags(item.flags() | Qt.ItemIsEditable)

    def addCommand(self):
        item = QListWidgetItem("combo 2")
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.commandList.addItem(item)

    def deleteCommand(self):
        if self.commandList.currentItem():
            self.commandList.takeItem(self.commandList.currentRow())

    def closeEvent(self, evt):
        self.enableConfig.val = self.enabled()
        self.characterConfig.val = self.character()
        self.commandConfig.val = self.commands()
        QWidget.closeEvent(self, evt)


class FilterDialog(QDialog):
    class FilterEntry(QWidget):
        def __init__(
            self, roomList, text, key, EntryType=QLineEdit, ConversionType=int
        ):
            super(QWidget, self).__init__()
            self.setContentsMargins(0, 0, 0, 0)

            self.layout = QVBoxLayout()

            self.enabledToggle = QCheckBox(text)
            self.roomList = roomList
            self.key = key
            self.rangeEnabled = QCheckBox("Use Range")
            self.minVal = EntryType()
            self.maxVal = EntryType()
            self.conversionType = ConversionType

            self.layout.addWidget(self.enabledToggle)

            tweaks = QHBoxLayout()
            tweaks.addWidget(self.minVal)
            tweaks.addWidget(self.rangeEnabled)
            tweaks.addWidget(self.maxVal)
            self.layout.addLayout(tweaks)

            self.setVals()

            self.enabledToggle.stateChanged.connect(self.updateVals)
            self.rangeEnabled.stateChanged.connect(self.updateVals)
            self.minVal.editingFinished.connect(self.updateVals)
            self.maxVal.editingFinished.connect(self.updateVals)

            self.setLayout(self.layout)

        def setVals(self):
            filterData = self.roomList.filter.extraData[self.key]
            minVal = filterData["min"]
            maxVal = filterData["max"]
            if isinstance(self.minVal, QLineEdit):
                self.minVal.setText(str(minVal))
                self.maxVal.setText(str(maxVal))
            elif isinstance(self.minVal, QDateTimeEdit):
                self.minVal.setDateTime(minVal.astimezone())
                self.maxVal.setDateTime(maxVal.astimezone())

            self.enabledToggle.setChecked(filterData["enabled"])
            self.rangeEnabled.setChecked(filterData["useRange"])

        def updateVals(self):
            filterData = self.roomList.filter.extraData[self.key]
            minVal = None
            maxVal = None
            if isinstance(self.minVal, QLineEdit):
                minVal = self.conversionType(self.minVal.text())
                maxVal = self.conversionType(self.maxVal.text())
            elif isinstance(self.minVal, QDateTimeEdit):
                minVal = (
                    self.minVal.dateTime()
                    .toPyDateTime()
                    .astimezone(datetime.timezone.utc)
                )
                maxVal = (
                    self.maxVal.dateTime()
                    .toPyDateTime()
                    .astimezone(datetime.timezone.utc)
                )

            filterData["min"] = minVal
            filterData["max"] = maxVal
            filterData["enabled"] = self.enabledToggle.isChecked()
            filterData["useRange"] = self.rangeEnabled.isChecked()

    class TagFilterEntry(QWidget):
        class TagFilterListItem(QListWidgetItem):
            def __init__(self, config):
                super(QListWidgetItem, self).__init__(config.label or config.tag)
                self.config = config

        def __init__(self, roomList):
            super(QWidget, self).__init__()

            self.roomList = roomList

            self.layout = QVBoxLayout()

            buttons = QHBoxLayout()

            self.enabledToggle = QCheckBox("Tags")

            modeGroup = QButtonGroup()
            self.anyModeToggle = QRadioButton("Any")
            self.exclusiveModeToggle = QRadioButton("Exclusive")
            self.blacklistModeToggle = QRadioButton("Blacklist")

            modeGroup.addButton(self.anyModeToggle)
            modeGroup.addButton(self.exclusiveModeToggle)
            modeGroup.addButton(self.blacklistModeToggle)

            buttons.addWidget(self.enabledToggle)
            buttons.addWidget(self.anyModeToggle)
            buttons.addWidget(self.exclusiveModeToggle)
            buttons.addWidget(self.blacklistModeToggle)
            self.layout.addLayout(buttons)

            self.tagsList = QListWidget()
            global xmlLookups
            for tag in xmlLookups.entities.tags.values():
                if tag.filterable:
                    tagItem = FilterDialog.TagFilterEntry.TagFilterListItem(tag)
                    tagItem.setFlags(tagItem.flags() | Qt.ItemIsUserCheckable)
                    tagItem.setCheckState(Qt.Unchecked)
                    self.tagsList.addItem(tagItem)

            self.setVals()

            self.tagsList.itemChanged.connect(self.updateVals)
            self.enabledToggle.toggled.connect(self.updateVals)
            self.anyModeToggle.toggled.connect(self.updateVals)
            self.exclusiveModeToggle.toggled.connect(self.updateVals)
            self.blacklistModeToggle.toggled.connect(self.updateVals)

            self.layout.addWidget(self.tagsList)
            self.setLayout(self.layout)

        def setVals(self):
            filterData = self.roomList.filter.extraData["tags"]
            self.enabledToggle.setChecked(filterData["enabled"])
            self.anyModeToggle.setChecked(filterData["mode"] == "Any")
            self.exclusiveModeToggle.setChecked(filterData["mode"] == "Exclusive")
            self.blacklistModeToggle.setChecked(filterData["mode"] == "Blacklist")

            for row in range(self.tagsList.count()):
                item = self.tagsList.item(row)
                item.setCheckState(
                    Qt.Checked
                    if item.config.tag in filterData["tags"]
                    else Qt.Unchecked
                )

        def updateVals(self):
            filterData = self.roomList.filter.extraData["tags"]
            filterData["enabled"] = self.enabledToggle.isChecked()
            if self.anyModeToggle.isChecked():
                filterData["mode"] = "Any"
            elif self.exclusiveModeToggle.isChecked():
                filterData["mode"] = "Exclusive"
            elif self.blacklistModeToggle.isChecked():
                filterData["mode"] = "Blacklist"

            checkedTags = []
            for row in range(self.tagsList.count()):
                item = self.tagsList.item(row)
                if item.checkState() == Qt.Checked:
                    checkedTags.append(item.config.tag)

            filterData["tags"] = checkedTags

    def __init__(self, parent):
        super(QDialog, self).__init__(parent)
        self.setWindowTitle("Room Filter Configuration")

        self.roomList = parent
        roomList = self.roomList

        self.layout = QVBoxLayout()

        self.weightEntry = FilterDialog.FilterEntry(
            roomList, "Weight", "weight", ConversionType=float
        )
        self.layout.addWidget(self.weightEntry)

        self.difficultyEntry = FilterDialog.FilterEntry(
            roomList, "Difficulty", "difficulty"
        )
        self.layout.addWidget(self.difficultyEntry)

        self.subtypeEntry = FilterDialog.FilterEntry(roomList, "SubType", "subtype")
        self.layout.addWidget(self.subtypeEntry)

        ltt = roomList.filter.extraData["lastTestTime"]
        if not ltt["min"]:
            ltt["min"] = datetime.datetime.now(datetime.timezone.utc)
            ltt["max"] = ltt["min"] - datetime.timedelta(days=30)

        self.lastTestTimeEntry = FilterDialog.FilterEntry(
            roomList, "Last Test Time", "lastTestTime", EntryType=QDateTimeEdit
        )
        self.lastTestTimeEntry.setToolTip(
            "If no range, searches for never tested rooms and rooms before this date-time. Else searches for rooms tested within the range, starting from the righthand datetime"
        )
        self.layout.addWidget(self.lastTestTimeEntry)

        self.tagsEntry = FilterDialog.TagFilterEntry(roomList)
        self.layout.addWidget(self.tagsEntry)

        self.setLayout(self.layout)

    def closeEvent(self, evt):
        self.roomList.setExtraFilter(None, force=True)
        self.roomList.changeFilter()
        QWidget.closeEvent(self, evt)


class StatisticsDialog(QDialog):
    class EntityStatisticsEntry:
        class EntityStatItem(QTableWidgetItem):
            def __init__(self, entry, property, formatAsPercent=False):
                super(QTableWidgetItem, self).__init__()
                self.entry = entry
                self.property = property
                self.sortValue = getattr(self.entry, self.property)
                self.formatAsPercent = formatAsPercent
                self.setFlags(Qt.ItemIsEnabled)

            def __lt__(self, otherItem):
                if (
                    self.sortValue is not None
                    and isinstance(
                        otherItem, StatisticsDialog.EntityStatisticsEntry.EntityStatItem
                    )
                    and otherItem.sortValue is not None
                ):
                    return self.sortValue < otherItem.sortValue
                else:
                    return super(QTableWidgetItem, self).__lt__(otherItem)

            def updateValue(self):
                self.sortValue = getattr(self.entry, self.property)
                if self.formatAsPercent:
                    self.setText("{:.2%}".format(self.sortValue))
                else:
                    self.setText(str(round(self.sortValue, 2)))

        def __init__(self, parent, config: EntityLookup.EntityConfig, tag=None):
            self.parent = parent
            self.table = self.parent.statisticsTable
            self.config = config
            self.tag = tag
            self.includedintag = False

            self.appearCount = 0
            self.appearPercent = 0
            self.averageDifficulty = 0
            self.averageWeight = 0

            self.rooms = []

            self.pixmap = QPixmap(config.imagePath)

            self.table.insertRow(0)
            self.nameWidget = QTableWidgetItem()
            self.nameWidget.setFlags(Qt.ItemIsEnabled)

            if self.tag:
                self.nameWidget.setText(self.tag.label or self.tag.tag)
            else:
                self.nameWidget.setText(self.config.name)

            self.nameWidget.setIcon(QIcon(self.pixmap))
            self.table.setItem(0, 0, self.nameWidget)

            self.propertyWidgets = []
            properties = (
                "appearCount",
                "appearPercent",
                "averageDifficulty",
                "averageWeight",
            )
            column = 1
            for property in properties:
                widget = StatisticsDialog.EntityStatisticsEntry.EntityStatItem(
                    self, property, property == "appearPercent"
                )
                self.table.setItem(0, column, widget)
                self.propertyWidgets.append(widget)
                column += 1

        def updateWidgets(self, overallStats, filter, useAverage):
            roomStats = self.parent.getStatsForRooms(self.rooms, filter)

            self.appearCount = roomStats["Count"]
            if overallStats["SumWeight"] > 0:
                self.appearPercent = roomStats["SumWeight"] / overallStats["SumWeight"]
            else:
                self.appearPercent = 0

            if useAverage:
                self.averageDifficulty = roomStats["AverageDifficulty"]
                self.averageWeight = roomStats["AverageWeight"]
            else:
                self.averageDifficulty = roomStats["ModeDifficulty"]
                self.averageWeight = roomStats["ModeWeight"]

            for widget in self.propertyWidgets:
                widget.updateValue()

            hidden = self.appearCount < filter["AppearCountThreshold"]
            if filter["CombatEntitiesOnly"]:
                hidden = hidden or self.config.matches(tags=["InNonCombatRooms"])
            if filter["GroupSimilarEntities"]:
                hidden = hidden or self.includedintag
            else:
                hidden = hidden or self.tag is not None

            self.table.setRowHidden(self.nameWidget.row(), hidden)

    def __init__(self, parent, roomList: RoomSelector):
        super(QDialog, self).__init__(parent)
        self.setWindowTitle("Room Statistics")

        self.roomList = roomList

        self.layout = QVBoxLayout()

        generalStatsBox = QGroupBox("General Stats")
        generalStatsBoxLayout = QVBoxLayout()
        self.generalStatsLabel = QLabel()
        generalStatsBoxLayout.addWidget(self.generalStatsLabel)
        generalStatsBox.setLayout(generalStatsBoxLayout)
        self.layout.addWidget(generalStatsBox)

        filterBox = QGroupBox("Filter")
        filterBoxLayout = QVBoxLayout()

        generalFilterCheckBoxesLayout = QHBoxLayout()
        self.selectedRoomsToggle = QCheckBox("Selected Rooms")
        self.selectedRoomsToggle.setToolTip(
            "If checked, statistics are only evaluated for selected rooms\nIf you have no rooms selected, has no effect."
        )
        self.selectedRoomsToggle.toggled.connect(self.refresh)
        generalFilterCheckBoxesLayout.addWidget(self.selectedRoomsToggle)
        self.combatEntityToggle = QCheckBox("Combat Entities")
        self.combatEntityToggle.setToolTip(
            "If checked, hides non-combat related entities, like grids and pickups"
        )
        self.combatEntityToggle.toggled.connect(self.refresh)
        generalFilterCheckBoxesLayout.addWidget(self.combatEntityToggle)
        self.forceIndividualEntitiesToggle = QCheckBox("Force Individual Entities")
        self.forceIndividualEntitiesToggle.setToolTip(
            "Forces each entity entry to get its own row, rather than combining variants of the same entity"
        )
        self.forceIndividualEntitiesToggle.toggled.connect(self.refresh)
        generalFilterCheckBoxesLayout.addWidget(self.forceIndividualEntitiesToggle)
        self.modeAverageToggle = QCheckBox("Show Averages")
        self.modeAverageToggle.setToolTip(
            "If checked, displays the average difficulty / weight of the rooms each entity is in, rather than the most common"
        )
        self.modeAverageToggle.toggled.connect(self.refresh)
        generalFilterCheckBoxesLayout.addWidget(self.modeAverageToggle)
        filterBoxLayout.addLayout(generalFilterCheckBoxesLayout)

        difficultyFilterBox = QGroupBox("Room Difficulty")
        difficultyFilterBoxLayout = QHBoxLayout()
        self.difficultyCheckboxes = []
        filterableDifficulties = (1, 5, 10, 15, 20)
        for difficulty in filterableDifficulties:
            checkbox = QCheckBox(str(difficulty))
            checkbox.setChecked(True)
            checkbox.toggled.connect(self.refresh)
            self.difficultyCheckboxes.append(checkbox)
            difficultyFilterBoxLayout.addWidget(checkbox)
        difficultyFilterBox.setLayout(difficultyFilterBoxLayout)
        filterBoxLayout.addWidget(difficultyFilterBox)

        appearCountThresholdLabel = QLabel("Appear Count Threshold:")
        filterBoxLayout.addWidget(appearCountThresholdLabel)

        self.appearCountThresholdSpinner = QSpinBox()
        self.appearCountThresholdSpinner.setRange(1, (2**31) - 1)
        self.appearCountThresholdSpinner.valueChanged.connect(self.refresh)
        filterBoxLayout.addWidget(self.appearCountThresholdSpinner)

        filterBox.setLayout(filterBoxLayout)
        self.layout.addWidget(filterBox)

        entityStatsBox = QGroupBox("Entity Stats")
        entityStatsBoxLayout = QVBoxLayout()
        self.statsEntries = []
        self.statisticsTable = QTableWidget()
        self.statisticsTable.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        entityStatsBoxLayout.addWidget(self.statisticsTable)
        entityStatsBox.setLayout(entityStatsBoxLayout)
        self.layout.addWidget(entityStatsBox)

        self.populateTable()

        self.setLayout(self.layout)

        self.adjustSize()

    def getStatsForRooms(self, rooms, roomFilter=None):
        count = 0
        sumRoomDifficulties = 0
        sumRoomWeights = 0
        difficulties = {}
        weights = {}
        for room in rooms:
            if roomFilter:
                if room.difficulty not in roomFilter["AllowedDifficulties"]:
                    continue
                if roomFilter["Rooms"]:
                    if room not in roomFilter["Rooms"]:
                        continue

            count += 1
            sumRoomDifficulties += room.difficulty
            sumRoomWeights += room.weight

            if room.difficulty not in difficulties:
                difficulties[room.difficulty] = 0

            difficulties[room.difficulty] += 1

            if room.weight not in weights:
                weights[room.weight] = 0

            weights[room.weight] += 1

        if count == 0:
            return {
                "Count": 0,
                "SumDifficulty": 0,
                "AverageDifficulty": 0,
                "ModeDifficulty": 0,
                "SumWeight": 0,
                "AverageWeight": 0,
                "ModeWeight": 0,
            }

        return {
            "Count": count,
            "SumDifficulty": sumRoomDifficulties,
            "AverageDifficulty": sumRoomDifficulties / count,
            "ModeDifficulty": max(difficulties, key=difficulties.get),
            "SumWeight": sumRoomWeights,
            "AverageWeight": sumRoomWeights / count,
            "ModeWeight": max(weights, key=weights.get),
        }

    def populateTable(self):
        self.statisticsTable.setSortingEnabled(False)
        self.statisticsTable.clear()
        self.statisticsTable.setColumnCount(5)

        # if len(self.roomList.selectedRooms()) > 0:
        #    rooms = self.roomList.orderedSelectedRooms()

        rooms = self.roomList.getRooms()

        overallStats = self.getStatsForRooms(rooms)
        self.generalStatsLabel.setText(
            f"Rooms: {overallStats['Count']}\n"
            + f"Most Common Difficulty: {overallStats['ModeDifficulty']} (average: {round(overallStats['AverageDifficulty'], 2)})\n"
            + f"Most Common Weight: {overallStats['ModeWeight']} (average: {round(overallStats['AverageWeight'], 2)})"
        )

        global xmlLookups
        entities = {}
        tags = {}
        self.statsEntries = []
        for room in rooms:
            for config in room.palette.values():
                if config.uniqueid not in entities:
                    entities[config.uniqueid] = StatisticsDialog.EntityStatisticsEntry(
                        self, config
                    )
                    self.statsEntries.append(entities[config.uniqueid])

                for tag in config.tags.values():
                    if tag.statisticsgroup:
                        if tag.tag not in tags:
                            tags[tag.tag] = StatisticsDialog.EntityStatisticsEntry(
                                self, config, tag
                            )
                            self.statsEntries.append(tags[tag.tag])

                        if room not in tags[tag.tag].rooms:
                            tags[tag.tag].rooms.append(room)

                        entities[config.uniqueid].includedintag = True

                entities[config.uniqueid].rooms.append(room)

        self.refresh()

        self.statisticsTable.setSortingEnabled(True)
        self.statisticsTable.sortItems(1, Qt.DescendingOrder)
        self.statisticsTable.verticalHeader().hide()
        self.statisticsTable.resizeColumnsToContents()

    def refresh(self):
        rooms = self.roomList.getRooms()

        roomFilter = {
            "AllowedDifficulties": {},
            "Rooms": False,
            "AppearCountThreshold": self.appearCountThresholdSpinner.value(),
            "CombatEntitiesOnly": self.combatEntityToggle.isChecked(),
            "GroupSimilarEntities": not self.forceIndividualEntitiesToggle.isChecked(),
        }

        if (
            self.selectedRoomsToggle.isChecked()
            and len(self.roomList.selectedRooms()) > 0
        ):
            rooms = self.roomList.selectedRooms()
            roomFilter["Rooms"] = rooms

        for checkbox in self.difficultyCheckboxes:
            if checkbox.isChecked():
                roomFilter["AllowedDifficulties"][int(checkbox.text())] = True

        filteredStats = self.getStatsForRooms(rooms, roomFilter)

        for stats in self.statsEntries:
            stats.updateWidgets(
                filteredStats, roomFilter, self.modeAverageToggle.isChecked()
            )

        if self.modeAverageToggle.isChecked():
            self.statisticsTable.setHorizontalHeaderLabels(
                [
                    "Entity",
                    "Room Count",
                    "Appear Chance",
                    "Average Difficulty",
                    "Average Weight",
                ]
            )
        else:
            self.statisticsTable.setHorizontalHeaderLabels(
                [
                    "Entity",
                    "Room Count",
                    "Appear Chance",
                    "Common Difficulty",
                    "Common Weight",
                ]
            )


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

    def __init__(self):
        super(QMainWindow, self).__init__()

        self.setWindowTitle("Basement Renovator")
        self.setIconSize(QSize(16, 16))

        self._path = None

        self.dirty = False

        self.wroteModFolder = False
        self.disableTestModTimer = None

        self.scene = RoomScene(self)

        self.clipboard = None
        self.setAcceptDrops(True)

        self.editor = RoomEditorWidget(self.scene)
        self.setCentralWidget(self.editor)

        self.fixupLookups()

        self.setupDocks()
        self.setupMenuBar()
        self.setupStatusBar()

        self.setGeometry(100, 500, 1280, 600)

        self.restoreState(settings.value("MainWindowState", self.saveState()), 0)
        self.restoreGeometry(settings.value("MainWindowGeometry", self.saveGeometry()))

        self.resetWindow = {"state": self.saveState(), "geometry": self.saveGeometry()}

        # Setup a new map
        self.newMap()
        self.clean()

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, val):
        oldPath = self.path
        self._path = val
        if self.path != oldPath:
            self.updateTitlebar()

    def dragEnterEvent(self, evt):
        if evt.mimeData().hasFormat("text/uri-list"):
            evt.setAccepted(True)

    def dropEvent(self, evt):
        files = evt.mimeData().text().split("\n")
        s = files[0]
        target = urllib.request.url2pathname(urllib.parse.urlparse(s).path)
        self.openWrapper(target)
        evt.acceptProposedAction()

    FIXUP_PNGS = (
        "resources/UI/",
        "resources/Entities/5.100.0 - Collectible.png",
        "resources/Backgrounds/Door.png",
        "resources/Backgrounds/DisabledDoor.png",
        "resources/Entities/questionmark.png",
    )

    def fixupLookups(self):
        global xmlLookups

        fixIconFormat = settings.value("FixIconFormat") == "1"
        if not fixIconFormat:
            return

        savedPaths = {}

        def fixImage(path):
            if path not in savedPaths:
                savedPaths[path] = True
                formatFix = QImage(path)
                formatFix.save(path)

        for fixupPath in MainWindow.FIXUP_PNGS:
            dirPath = Path(fixupPath)
            if dirPath.is_dir():
                for dirPath, dirNames, filenames in os.walk(dirPath):
                    for filename in filenames:
                        path = os.path.join(dirPath, filename)
                        fixPath = Path(path)
                        if fixPath.is_file() and fixPath.suffix == ".png":
                            fixImage(path)

            elif dirPath.is_file() and dirPath.suffix == ".png":
                fixImage(fixupPath)
            else:
                printf(f"{fixupPath} is not a valid directory or png file")

        entities = xmlLookups.entities.lookup()
        for config in entities:
            if config.imagePath:
                fixImage(config.imagePath)

            if config.editorImagePath:
                fixImage(config.editorImagePath)

        nodes = xmlLookups.stages.lookup()
        nodes.extend(xmlLookups.roomTypes.lookup())

        for node in nodes:
            gfxs = node.findall("Gfx")
            if node.get("BGPrefix") is not None:
                gfx.append(node)

            for gfx in gfxs:
                for key, imgPath in xmlLookups.getGfxData(gfx)["Paths"].items():
                    if imgPath and os.path.isfile(imgPath):
                        fixImage(imgPath)

                for ent in gfx.findall("Entity"):
                    imgPath = ent.get("Image")
                    if imgPath and os.path.isfile(imgPath):
                        fixImage(imgPath)

    def setupFileMenuBar(self):
        f = self.fileMenu

        f.clear()
        self.fa = f.addAction("New", self.newMap, QKeySequence("Ctrl+N"))
        self.fc = f.addAction("Open (XML)...", self.openMap, QKeySequence("Ctrl+O"))
        self.fm = f.addAction(
            "Import (STB)...", self.importMap, QKeySequence("Ctrl+Shift+O")
        )
        self.fb = f.addAction(
            "Open/Import by Stage", self.openMapDefault, QKeySequence("Ctrl+Alt+O")
        )
        f.addSeparator()
        self.fd = f.addAction("Save", self.saveMap, QKeySequence("Ctrl+S"))
        self.fe = f.addAction(
            "Save As...", self.saveMapAs, QKeySequence("Ctrl+Shift+S")
        )
        self.fk = f.addAction(
            "Export to STB", lambda: self.exportSTB(), QKeySequence("Shift+Alt+S")
        )
        self.fk = f.addAction(
            "Export to STB (Rebirth)", lambda: self.exportSTB(stbType="Rebirth")
        )
        f.addSeparator()
        self.fk = f.addAction(
            "Copy Screenshot to Clipboard",
            lambda: self.screenshot("clipboard"),
            QKeySequence("F10"),
        )
        self.fg = f.addAction(
            "Save Screenshot to File...",
            lambda: self.screenshot("file"),
            QKeySequence("Ctrl+F10"),
        )
        f.addSeparator()
        self.fh = f.addAction(
            "Set Resources Path",
            self.setDefaultResourcesPath,
            QKeySequence("Ctrl+Shift+P"),
        )
        self.fi = f.addAction(
            "Reset Resources Path",
            self.resetResourcesPath,
            QKeySequence("Ctrl+Shift+R"),
        )
        f.addSeparator()
        self.fj = f.addAction("Set Hooks", self.showHooksMenu)
        self.fl = f.addAction(
            "Autogenerate mod content (discouraged)",
            lambda: self.toggleSetting("ModAutogen"),
        )
        self.fl.setCheckable(True)
        self.fl.setChecked(settings.value("ModAutogen") == "1")
        f.addSeparator()

        recent = settings.value("RecentFiles", [])
        for r in recent:
            f.addAction(os.path.normpath(r), self.openRecent).setData(r)

        f.addSeparator()

        self.fj = f.addAction("Exit", self.close, QKeySequence.Quit)

    def setupMenuBar(self):
        mb = self.menuBar()

        self.fileMenu = mb.addMenu("&File")
        self.setupFileMenuBar()

        self.e = mb.addMenu("Edit")
        self.ea = self.e.addAction("Copy", self.copy, QKeySequence.Copy)
        self.eb = self.e.addAction("Cut", self.cut, QKeySequence.Cut)
        self.ec = self.e.addAction("Paste", self.paste, QKeySequence.Paste)
        self.ed = self.e.addAction("Select All", self.selectAll, QKeySequence.SelectAll)
        self.ee = self.e.addAction("Deselect", self.deSelect, QKeySequence("Ctrl+D"))
        self.e.addSeparator()
        self.ef = self.e.addAction(
            "Clear Filters", self.roomList.clearAllFilter, QKeySequence("Ctrl+K")
        )
        self.eg = self.e.addAction(
            "Pin Entity Filter",
            lambda: self.toggleSetting("PinEntityFilter"),
            QKeySequence("Ctrl+Alt+K"),
        )
        self.eg.setCheckable(True)
        self.eg.setChecked(settings.value("PinEntityFilter") == "1")
        self.nonCombatFilter = self.e.addAction(
            "Non-Combat Room Filter",
            lambda: (
                self.toggleSetting("NonCombatRoomFilter"),
                self.roomList.changeFilter(),
            ),
        )
        self.nonCombatFilter.setCheckable(True)
        self.nonCombatFilter.setChecked(settings.value("NonCombatRoomFilter") == "1")
        self.el = self.e.addAction(
            "Snap to Room Boundaries",
            lambda: self.toggleSetting("SnapToBounds", onDefault=True),
        )
        self.el.setCheckable(True)
        self.el.setChecked(settings.value("SnapToBounds") != "0")
        self.em = self.e.addAction(
            "Export to STB on Save (slower saves)",
            lambda: self.toggleSetting("ExportSTBOnSave"),
        )
        self.em.setCheckable(True)
        self.em.setChecked(settings.value("ExportSTBOnSave") == "1")
        self.e.addSeparator()
        self.eh = self.e.addAction(
            "Bulk Replace Entities", self.showReplaceDialog, QKeySequence("Ctrl+R")
        )
        self.ei = self.e.addAction("Sort Rooms by ID", self.sortRoomIDs)
        self.ej = self.e.addAction("Sort Rooms by Name", self.sortRoomNames)
        self.ek = self.e.addAction(
            "Recompute Room IDs", self.recomputeRoomIDs, QKeySequence("Ctrl+B")
        )
        self.showStatistics = self.e.addAction(
            "View Room Statistics", self.showStatisticsMenu
        )

        v = mb.addMenu("View")

        self.wa = v.addAction(
            "Show Grid",
            lambda: self.toggleSetting("GridEnabled", onDefault=True),
            QKeySequence("Ctrl+G"),
        )
        self.wa.setCheckable(True)
        self.wa.setChecked(settings.value("GridEnabled") != "0")

        self.wg = v.addAction(
            "Show Out of Bounds Grid", lambda: self.toggleSetting("BoundsGridEnabled")
        )
        self.wg.setCheckable(True)
        self.wg.setChecked(settings.value("BoundsGridEnabled") == "1")

        self.wh = v.addAction(
            "Show Grid Indexes", lambda: self.toggleSetting("ShowGridIndex")
        )
        self.wh.setCheckable(True)
        self.wh.setChecked(settings.value("ShowGridIndex") == "1")

        self.wi = v.addAction(
            "Show Grid Coordinates", lambda: self.toggleSetting("ShowCoordinates")
        )
        self.wi.setCheckable(True)
        self.wi.setChecked(settings.value("ShowCoordinates") == "1")
        v.addSeparator()

        self.we = v.addAction(
            "Show Room Info",
            lambda: self.toggleSetting("StatusEnabled", onDefault=True),
            QKeySequence("Ctrl+I"),
        )
        self.we.setCheckable(True)
        self.we.setChecked(settings.value("StatusEnabled") != "0")

        self.wd = v.addAction(
            "Use Bitfont Counter",
            lambda: self.toggleSetting("BitfontEnabled", onDefault=True),
        )
        self.wd.setCheckable(True)
        self.wd.setChecked(settings.value("BitfontEnabled") != "0")

        self.hideDuplicateEntities = v.addAction(
            "Hide Duplicate Entities",
            lambda: (
                self.toggleSetting("HideDuplicateEntities"),
                self.EntityPalette.updateTabs(),
            ),
        )
        self.hideDuplicateEntities.setCheckable(True)
        self.hideDuplicateEntities.setChecked(
            settings.value("HideDuplicateEntities") == "1"
        )

        self.randomizeRocks = v.addAction(
            "Randomize Rock Appearance",
            lambda: self.toggleSetting("RandomizeRocks", onDefault=True),
        )
        self.randomizeRocks.setCheckable(True)
        self.randomizeRocks.setChecked(settings.value("RandomizeRocks") != "0")

        v.addSeparator()
        self.wb = v.addAction(
            "Hide Entity Painter", self.showPainter, QKeySequence("Ctrl+Alt+P")
        )
        self.wc = v.addAction(
            "Hide Room List", self.showRoomList, QKeySequence("Ctrl+Alt+R")
        )
        self.wf = v.addAction("Reset Window Defaults", self.resetWindowDefaults)
        v.addSeparator()

        r = mb.addMenu("Test")
        self.ra = r.addAction(
            "Test Current Room - InstaPreview",
            self.testMapInstapreview,
            QKeySequence("Ctrl+P"),
        )
        self.rb = r.addAction(
            "Test Current Room - Replace Stage", self.testMap, QKeySequence("Ctrl+T")
        )
        self.rc = r.addAction(
            "Test Current Room - Replace Start",
            self.testStartMap,
            QKeySequence("Ctrl+Shift+T"),
        )
        r.addSeparator()
        self.re = r.addAction("Test Configuration", self.showTestConfigMenu)
        self.rd = r.addAction(
            "Enable Test Mod Dialog", lambda: self.toggleSetting("DisableTestDialog")
        )
        self.rd.setCheckable(True)
        self.rd.setChecked(settings.value("DisableTestDialog") != "1")

        h = mb.addMenu("Help")
        self.ha = h.addAction("About Basement Renovator", self.aboutDialog)
        self.hb = h.addAction("Basement Renovator Documentation", self.goToHelp)
        # self.hc = h.addAction('Keyboard Shortcuts')

    def setupDocks(self):
        self.roomList = RoomSelector()
        self.roomListDock = QDockWidget("Rooms")
        self.roomListDock.setWidget(self.roomList)
        self.roomListDock.visibilityChanged.connect(self.updateDockVisibility)
        self.roomListDock.setObjectName("RoomListDock")

        self.roomList.list.currentItemChanged.connect(self.handleSelectedRoomChanged)

        self.addDockWidget(Qt.RightDockWidgetArea, self.roomListDock)

        self.EntityPalette = EntityPalette()
        self.EntityPaletteDock = QDockWidget("Entity Palette")
        self.EntityPaletteDock.setWidget(self.EntityPalette)
        self.EntityPaletteDock.visibilityChanged.connect(self.updateDockVisibility)
        self.EntityPaletteDock.setObjectName("EntityPaletteDock")

        self.EntityPalette.objChanged.connect(self.handleObjectChanged)
        self.EntityPalette.objReplaced.connect(self.handleObjectReplaced)

        self.addDockWidget(Qt.LeftDockWidgetArea, self.EntityPaletteDock)

    def setupStatusBar(self):
        self.statusBar = QStatusBar()
        self.statusBar.setStyleSheet("QStatusBar::item {border: None;}")
        tooltipElements = [
            {"label": ": Select", "icons": [[0, 0]]},
            {"label": ": Move Selection", "icons": [[64, 0]]},
            {"label": ": Multi Selection", "icons": [[0, 0], [16, 16]]},
            {"label": ": Replace with Palette selection", "icons": [[0, 0], [32, 16]]},
            {"label": ": Place Object", "icons": [[32, 0]]},
            {
                "label": ": Edit Spike&Chain + Fissure spawner properties",
                "icons": [[16, 0]],
            },
        ]

        q = QImage()
        q.load("resources/UI/uiIcons.png")
        for infoObj in tooltipElements:
            for subicon in infoObj["icons"]:
                iconObj = QLabel()
                iconObj.setPixmap(
                    QPixmap.fromImage(q.copy(subicon[0], subicon[1], 16, 16))
                )
                iconObj.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
                self.statusBar.addWidget(iconObj)
            label = QLabel(infoObj["label"])
            label.setContentsMargins(0, 0, 20, 0)
            label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
            label.setAlignment(Qt.AlignTop)
            self.statusBar.addWidget(label)

        self.setStatusBar(self.statusBar)

    def restoreEditMenu(self):
        a = self.e.actions()
        self.e.insertAction(a[1], self.ea)
        self.e.insertAction(a[2], self.eb)
        self.e.insertAction(a[3], self.ec)
        self.e.insertAction(a[4], self.ed)
        self.e.insertAction(a[5], self.ee)

    def updateTitlebar(self):
        if self.path == "":
            effectiveName = "Untitled Map"
        else:
            if "Windows" in platform.system():
                effectiveName = os.path.normpath(self.path)
            else:
                effectiveName = os.path.basename(self.path)

        self.setWindowTitle("%s - Basement Renovator" % effectiveName)

    def checkDirty(self):
        if self.dirty == False:
            return False

        msgBox = QMessageBox(
            QMessageBox.Warning,
            "File is not saved",
            "Completing this operation without saving could cause loss of data.",
            QMessageBox.NoButton,
            self,
        )
        msgBox.addButton("Continue", QMessageBox.AcceptRole)
        msgBox.addButton("Cancel", QMessageBox.RejectRole)
        if msgBox.exec_() == QMessageBox.AcceptRole:
            self.clean()
            return False

        return True

    def dirt(self):
        self.setWindowIcon(QIcon("resources/UI/BasementRenovator-SmallDirty.png"))
        self.dirty = True

    def clean(self):
        self.setWindowIcon(QIcon("resources/UI/BasementRenovator-Small.png"))
        self.dirty = False

    def storeEntityList(self, room=None):
        room = room or self.roomList.selectedRoom()
        if not room:
            return

        spawns = [[] for x in room.gridSpawns]

        width, height = room.info.dims

        for y in range(height):
            for e in self.scene.roomRows[y].childItems():
                spawns[Room.Info.gridIndex(e.entity.x, e.entity.y, width)].append(e)

        palette = {}
        for i, spawn in enumerate(spawns):
            for e in spawn:
                if e.entity.config.uniqueid not in palette:
                    palette[e.entity.config.uniqueid] = e.entity.config

            spawns[i] = list(
                map(
                    lambda e: [
                        e.entity.Type,
                        e.entity.Variant,
                        e.entity.Subtype,
                        e.entity.weight,
                    ],
                    sorted(spawn, key=QGraphicsItem.zValue),
                )
            )

        room.gridSpawns = spawns
        room.palette = palette

    def closeEvent(self, event):
        """Handler for the main window close event"""

        self.disableTestMod()

        if self.checkDirty():
            event.ignore()
        else:
            settings = QSettings("settings.ini", QSettings.IniFormat)

            # Save our state
            settings.setValue("MainWindowGeometry", self.saveGeometry())
            settings.setValue("MainWindowState", self.saveState(0))

            event.accept()

            app.quit()

    #####################
    # Slots for Widgets #
    #####################

    # @pyqtSlot(Room, Room)
    def handleSelectedRoomChanged(self, current, prev):
        if not current:
            return

        # Encode the current room, just in case there are changes
        if prev:
            self.storeEntityList(prev)

            # Clear the current room mark
            prev.setData(100, False)

        # Clear the room and reset the size
        self.scene.clear()
        self.scene.newRoomSize(current.info.shape)
        current.setRoomBG()
        self.scene.updateRoomDepth(current)

        self.editor.resizeEvent(QResizeEvent(self.editor.size(), self.editor.size()))

        # Make some doors
        current.clearDoors()

        # Spawn those entities
        for stack, x, y in current.spawns():
            for ent in stack:
                e = Entity(x, y, ent[0], ent[1], ent[2], ent[3], respawning=True)

        # Make the current Room mark for clearer multi-selection
        current.setData(100, True)

    # @pyqtSlot(EntityItem)
    def handleObjectChanged(self, entity, setFilter=True):
        self.editor.objectToPaint = entity
        if setFilter:
            self.roomList.setEntityFilter(entity)

    # @pyqtSlot(EntityItem)
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
        if self.checkDirty():
            return
        self.roomList.list.clear()
        self.scene.clear()
        self.path = ""

        self.dirt()
        self.roomList.changeFilter()

    def setDefaultResourcesPath(self):
        settings = QSettings("settings.ini", QSettings.IniFormat)
        if not settings.contains("ResourceFolder"):
            settings.setValue("ResourceFolder", self.findResourcePath())
        resPath = settings.value("ResourceFolder")
        resPathDialog = QFileDialog()
        resPathDialog.setFilter(QDir.Hidden)
        newResPath = QFileDialog.getExistingDirectory(self, "Select directory", resPath)

        if newResPath != "":
            settings.setValue("ResourceFolder", newResPath)

    def resetResourcesPath(self):
        settings = QSettings("settings.ini", QSettings.IniFormat)
        settings.remove("ResourceFolder")
        settings.setValue("ResourceFolder", self.findResourcePath())

    def showHooksMenu(self):
        hooks = HooksDialog(self)
        hooks.show()

    def showTestConfigMenu(self):
        testConfig = TestConfigDialog(self)
        testConfig.show()

    def showStatisticsMenu(self):
        statistics = StatisticsDialog(self, self.roomList)
        statistics.show()

    def openMapDefault(self):
        if self.checkDirty():
            return

        global xmlLookups
        selectMaps = {}
        for x in xmlLookups.stages.lookup(baseGamePath=True):
            selectMaps[x.get("Name")] = x.get("BaseGamePath")

        selectedMap, selectedMapOk = QInputDialog.getItem(
            self, "Map selection", "Select floor", selectMaps.keys(), 0, False
        )
        self.restoreEditMenu()

        if not selectedMapOk:
            return

        mapFileName = selectMaps[selectedMap] + ".stb"
        roomPath = os.path.join(
            os.path.expanduser(self.findResourcePath()), "rooms", mapFileName
        )

        if not QFile.exists(roomPath):
            self.setDefaultResourcesPath()
            roomPath = os.path.join(
                os.path.expanduser(self.findResourcePath()), "rooms", mapFileName
            )
            if not QFile.exists(roomPath):
                QMessageBox.warning(
                    self,
                    "Error",
                    "Failed opening stage. Make sure that the resources path is set correctly (see File menu) and that the proper STB file is present in the rooms directory.",
                )
                return

        # load the xml version if available
        xmlVer = roomPath[:-3] + "xml"
        if QFile.exists(xmlVer):
            roomPath = xmlVer

        self.openWrapper(roomPath)

    def getRecentFolder(self):
        startPath = ""

        # If a file is currently open, first default to the directory that the current file is in
        if self.path != "":
            dir_of_file_currently_open = os.path.dirname(self.path)
            return dir_of_file_currently_open

        settings = QSettings("settings.ini", QSettings.IniFormat)

        # Get the folder containing the last open file if you can
        # and it's not a default stage
        stagePath = os.path.join(settings.value("ResourceFolder", ""), "rooms")
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

    def openMapImpl(self, title, fileTypes, addToRecent=True):
        if self.checkDirty():
            return False

        target, ext = QFileDialog.getOpenFileName(
            self, title, self.getRecentFolder(), fileTypes
        )
        self.restoreEditMenu()

        # Looks like nothing was selected
        if not target:
            return False

        self.openWrapper(target, addToRecent=addToRecent)
        return True

    def openMap(self):
        self.openMapImpl("Open Room File", "XML File (*.xml)")

    def importMap(self, target=None):
        # part of openWrapper re-saves the file if it was not xml
        self.openMapImpl(
            "Import Rooms", "Stage Binary (*.stb);;TXT File (*.txt)", addToRecent=False
        )

    def openRecent(self):
        if self.checkDirty():
            return

        path = self.sender().data()
        self.restoreEditMenu()

        self.openWrapper(path)

    def openWrapper(self, path, addToRecent=True):
        printf(path)
        file, ext = os.path.splitext(path)
        isXml = ext == ".xml"

        if not isXml:
            newPath = f"{file}.xml"
            if os.path.exists(newPath):
                reply = QMessageBox.question(
                    self,
                    "Import Map",
                    f'"{newPath}" already exists; importing this file will overwrite it. Are you sure you want to import?',
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.No:
                    return

        self.path = path

        global xmlLookups
        self.floorInfo = (
            xmlLookups.stages.lookup(path=self.path)
            or xmlLookups.stages.lookup(name="Basement")
        )[-1]

        roomFile = None
        try:
            roomFile = self.open(addToRecent=addToRecent and isXml)
        except FileNotFoundError:
            QMessageBox.warning(
                self, "Error", "Failed opening rooms. The file does not exist."
            )
        except NotImplementedError:
            traceback.print_exception(*sys.exc_info())
            QMessageBox.warning(
                self,
                "Error",
                "This is not a valid STB file. (e.g. Rebirth or Afterbirth format) It may be one of the prototype STB files accidentally included in the AB+ release.",
            )
        except:
            traceback.print_exception(*sys.exc_info())
            QMessageBox.warning(
                self,
                "Error",
                f"Failed opening rooms.\n{''.join(traceback.format_exception(*sys.exc_info()))}",
            )

        if not roomFile:
            return

        self.roomList.list.clear()
        self.scene.clear()

        self.roomList.file = roomFile
        for room in roomFile.rooms:
            self.roomList.list.addItem(room)

        self.clean()
        self.roomList.changeFilter()

        if not isXml:
            self.saveMap()

    def open(self, path=None, addToRecent=True):
        path = path or self.path
        roomFile = None

        ext = os.path.splitext(path)[1]
        if ext == ".xml":
            roomFile = StageConvert.xmlToCommon(path)
        elif ext == ".txt":
            roomFile = StageConvert.txtToCommon(path, xmlLookups.entities)
        else:
            roomFile = StageConvert.stbToCommon(path)

        rooms = roomFile.rooms

        seenSpawns = {}
        for room in rooms:

            def sameDoorLocs(a, b):
                for ad, bd in zip(a, b):
                    if ad[0] != bd[0] or ad[1] != bd[1]:
                        return False
                return True

            normalDoors = sorted(room.info.shapeData["Doors"], key=Room.DoorSortKey)
            sortedDoors = sorted(room.info.doors, key=Room.DoorSortKey)
            if len(normalDoors) != len(sortedDoors) or not sameDoorLocs(
                normalDoors, sortedDoors
            ):
                printf(
                    f"Invalid doors in room {room.getPrefix()}: Expected {normalDoors}, Got {sortedDoors}"
                )

            for stackedEnts, ex, ey in room.spawns():
                if not room.info.isInBounds(ex, ey):
                    printf(
                        f"Found entity with out of bounds spawn loc in room {room.getPrefix()}: {ex-1}, {ey-1}"
                    )

                for ent in stackedEnts:
                    eType, eSubtype, eVariant = ent.Type, ent.Subtype, ent.Variant
                    if (eType, eSubtype, eVariant) not in seenSpawns:
                        config = xmlLookups.entities.lookupOne(
                            eType, eVariant, eSubtype
                        )

                        if config is None or config.invalid:
                            printf(
                                f"Room {room.getPrefix()} has invalid entity '{config is None and 'UNKNOWN' or config.name}'! ({eType}.{eVariant}.{eSubtype})"
                            )
                        seenSpawns[(eType, eSubtype, eVariant)] = (
                            config is None or config.invalid
                        )

        def coreToRoomItem(coreRoom):
            palette = {}
            gridSpawns = []
            global xmlLookups
            for gridSpawn in coreRoom.gridSpawns:
                spawns = []
                for spawn in gridSpawn:
                    spawns.append(
                        [spawn.Type, spawn.Variant, spawn.Subtype, spawn.weight]
                    )

                    config = xmlLookups.entities.lookupOne(
                        spawn.Type, spawn.Variant, spawn.Subtype
                    )
                    if config and config.uniqueid not in palette:
                        palette[config.uniqueid] = config

                gridSpawns.append(spawns)

            r = Room(
                coreRoom.name,
                gridSpawns,
                palette,
                coreRoom.difficulty,
                coreRoom.weight,
                coreRoom.info.type,
                coreRoom.info.variant,
                coreRoom.info.subtype,
                coreRoom.info.shape,
                coreRoom.info.doors,
            )
            r.xmlProps = dict(coreRoom.xmlProps)
            r.lastTestTime = coreRoom.lastTestTime
            return r

        roomFile.rooms = list(map(coreToRoomItem, rooms))

        # Update recent files
        if (
            addToRecent
        ):  # and ext == '.xml': # if a non-xml was deliberately opened, add it to recent
            self.updateRecent(path)

        return roomFile

    def saveMap(self, forceNewName=False):
        target = self.path

        if not target or forceNewName:
            dialogDir = (
                target == "" and self.getRecentFolder() or os.path.dirname(target)
            )
            target, ext = QFileDialog.getSaveFileName(
                self, "Save Map", dialogDir, "XML (*.xml)"
            )
            self.restoreEditMenu()

            if not target:
                return

            self.path = target

        try:
            self.save(
                self.roomList.getRooms(), fileObj=self.roomList.file, updateActive=True
            )
        except:
            traceback.print_exception(*sys.exc_info())
            QMessageBox.warning(
                self, "Error", "Saving failed. Try saving to a new file instead."
            )

        self.clean()
        self.roomList.changeFilter()

        settings = QSettings("settings.ini", QSettings.IniFormat)
        if settings.value("ExportSTBOnSave") == "1":
            self.exportSTB()

    def saveMapAs(self):
        self.saveMap(forceNewName=True)

    def exportSTB(self, stbType=None):
        target = self.path

        if not target:
            self.saveMap()
            target = self.path

        try:
            target = os.path.splitext(target)[0] + ".stb"
            self.save(
                self.roomList.getRooms(), target, updateRecent=False, stbType=stbType
            )
        except:
            traceback.print_exception(*sys.exc_info())
            QMessageBox.warning(
                self,
                "Error",
                f"Exporting failed.\n{''.join(traceback.format_exception(*sys.exc_info()))}",
            )

    def save(
        self,
        rooms,
        path=None,
        fileObj=None,
        updateActive=False,
        updateRecent=True,
        isPreview=False,
        stbType=None,
    ):
        path = path or (os.path.splitext(self.path)[0] + ".xml")

        self.storeEntityList()

        def entItemToCore(e, i, w):
            x = i % w
            y = int(i / w)
            return EntityData(x, y, e[0], e[1], e[2], e[3])

        def roomItemToCore(room):
            realWidth = room.info.dims[0]
            spawns = list(
                map(
                    lambda s: list(
                        map(lambda e: entItemToCore(e, s[0], realWidth), s[1])
                    ),
                    enumerate(room.gridSpawns),
                )
            )
            r = RoomData(
                room.name,
                spawns,
                room.difficulty,
                room.weight,
                room.info.type,
                room.info.variant,
                room.info.subtype,
                room.info.shape,
                room.info.doors,
            )
            r.xmlProps = dict(room.xmlProps)
            r.lastTestTime = room.lastTestTime
            return r

        rooms = list(map(roomItemToCore, rooms))

        ext = os.path.splitext(path)[1]
        if ext == ".xml":
            StageConvert.commonToXML(path, rooms, file=fileObj, isPreview=isPreview)
        else:
            if stbType == "Rebirth":
                StageConvert.commonToSTBRB(path, rooms)  # cspell:disable-line
            else:
                StageConvert.commonToSTBAB(path, rooms)  # cspell:disable-line

        if updateActive:
            self.path = path

        if updateRecent and ext == ".xml":
            self.updateRecent(path)

            # if a save doesn't update the recent list, it's probably not a real save
            # so only do hooks in this case
            settings = QSettings("settings.ini", QSettings.IniFormat)
            saveHooks = settings.value("HooksSave")
            if saveHooks:
                fullPath = os.path.abspath(path)
                for hook in saveHooks:
                    path, name = os.path.split(hook)
                    try:
                        subprocess.run([hook, fullPath, "--save"], cwd=path, timeout=60)
                    except Exception as e:
                        printf("Save hook failed! Reason:", e)

    def replaceEntities(self, replaced, replacement):
        self.storeEntityList()

        numEnts = 0
        numRooms = 0

        def checkEq(a, b):
            return (
                a[0] == b[0]
                and (b[1] < 0 or a[1] == b[1])
                and (b[2] < 0 or a[2] == b[2])
            )

        def fixEnt(a, b):
            a[0] = b[0]
            if b[1] >= 0:
                a[1] = b[1]
            if b[2] >= 0:
                a[2] = b[2]

        for i in range(self.roomList.list.count()):
            currentRoom = self.roomList.list.item(i)

            n = 0
            for stack, x, y in currentRoom.spawns():
                for ent in stack:
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
        QMessageBox.information(
            None,
            "Replace",
            numEnts > 0
            and f"Replaced {numEnts} entities in {numRooms} rooms"
            or "No entities to replace!",
        )

    def sortRoomIDs(self):
        self.sortRoomsByKey(lambda x: (x.info.type, x.info.variant))

    def sortRoomNames(self):
        self.sortRoomsByKey(lambda x: (x.info.type, x.name, x.info.variant))

    def sortRoomsByKey(self, key):
        roomList = self.roomList.list
        selection = roomList.currentItem()
        roomList.setCurrentItem(None, QItemSelectionModel.ClearAndSelect)

        rooms = sorted(
            [roomList.takeItem(roomList.count() - 1) for x in range(roomList.count())],
            key=key,
        )

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

            if room.info.type not in roomsByType:
                roomsByType[room.info.type] = room.info.variant

            room.info.variant = roomsByType[room.info.type]
            room.setToolTip()

            roomsByType[room.info.type] += 1

        self.dirt()
        self.scene.update()

    # @pyqtSlot()
    def screenshot(self, mode):
        filename = None
        if mode == "file":
            filename = QFileDialog.getSaveFileName(
                self,
                "Choose a new filename",
                "untitled.png",
                "Portable Network Graphics (*.png)",
            )[0]
            if filename == "":
                return

        g = settings.value("GridEnabled")
        settings.setValue("GridEnabled", "0")

        ScreenshotImage = QImage(
            self.scene.sceneRect().width(),
            self.scene.sceneRect().height(),
            QImage.Format_ARGB32,
        )
        ScreenshotImage.fill(Qt.transparent)

        RenderPainter = QPainter(ScreenshotImage)
        self.scene.render(
            RenderPainter, QRectF(ScreenshotImage.rect()), self.scene.sceneRect()
        )
        RenderPainter.end()

        if mode == "file":
            ScreenshotImage.save(filename, "PNG", 50)
        elif mode == "clipboard":
            QApplication.clipboard().setImage(ScreenshotImage, QClipboard.Clipboard)

        settings.setValue("GridEnabled", g)

    def getTestModPath(self):
        modFolder = findModsPath()
        name = "basement-renovator-helper"
        return os.path.join(modFolder, name)

    def makeTestMod(self, forceClean):
        folder = self.getTestModPath()
        roomPath = os.path.join(folder, "resources", "rooms")
        contentRoomPath = os.path.join(folder, "content", "rooms")

        if (forceClean or not mainWindow.wroteModFolder) and os.path.isdir(folder):
            try:
                shutil.rmtree(folder)
            except Exception as e:
                printf("Error clearing old mod data: ", e)

        # delete the old files
        if os.path.isdir(folder):
            dis = os.path.join(folder, "disable.it")
            if os.path.isfile(dis):
                os.unlink(dis)

            for path in [roomPath, contentRoomPath]:
                for f in os.listdir(path):
                    f = os.path.join(path, f)
                    try:
                        if os.path.isfile(f):
                            os.unlink(f)
                    except:
                        pass
        # otherwise, make it fresh
        else:
            try:
                shutil.copytree("./resources/modtemplate", folder)
                os.makedirs(roomPath)
                os.makedirs(contentRoomPath)
                mainWindow.wroteModFolder = True
            except Exception as e:
                printf("Could not copy mod template!", e)
                return "", e

        return folder, roomPath

    def writeTestData(self, folder, testType, floorInfo, testRooms):
        with open(os.path.join(folder, "roomTest.lua"), "w") as testData:
            quot = '\\"'
            bs = "\\"
            strFix = lambda x: f'''"{x.replace(bs, bs + bs).replace('"', quot)}"'''

            char = None
            commands = []
            if settings.value("TestConfigDisabled") != "1":
                char = settings.value("TestCharacter")
                if char:
                    char = strFix(char)

                commands = settings.value("TestCommands", [])

            roomsStr = ",\n\t".join(
                map(
                    lambda testRoom: f"""{{
        Name = {strFix(testRoom.name)},
        Type = {testRoom.info.type},
        Variant = {testRoom.info.variant},
        Subtype = {testRoom.info.subtype},
        Shape = {testRoom.info.shape}
    }}""",
                    testRooms,
                )
            )

            testData.write(
                f"""return {{
    TestType = {strFix(testType)},
    Character = {char or 'nil'}, -- only used in Repentance
    Commands = {{ {', '.join(map(strFix, commands))} }},
    Stage = {floorInfo.get('Stage')},
    StageType = {floorInfo.get('StageType')},
    StageName = {strFix(floorInfo.get('Name'))},
    IsModStage = {floorInfo.get('BaseGamePath') is None and 'true' or 'false'},
    RoomFile = {strFix(str(Path(self.path)) or 'N/A')},
    Rooms = {{
    {roomsStr}
    }}
}}
"""
            )

    def disableTestMod(self, modPath=None):
        modPath = modPath or self.getTestModPath()
        if not os.path.isdir(modPath):
            return

        with open(os.path.join(modPath, "disable.it"), "w"):
            pass

    # Test by replacing the rooms in the relevant floor
    def testMap(self):
        def setup(modPath, roomsPath, floorInfo, rooms, version):
            if version not in ["Afterbirth+", "Repentance"]:
                QMessageBox.warning(
                    self, "Error", f"Stage Replacement not supported for {version}!"
                )
                raise

            basePath = floorInfo.get("BaseGamePath")
            if basePath is None:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Custom stages cannot be tested with Stage Replacement, since they don't have a room file to replace.",
                )
                raise

            if floorInfo.get("Name") == "Blue Womb":
                QMessageBox.warning(
                    self,
                    "Error",
                    "Blue Womb cannot be tested with Stage Replacement, since it doesn't have normal room generation.",
                )
                raise

            # Set the selected rooms to max weight, best spawn difficulty, default type, and enable all the doors
            newRooms = list(
                map(
                    lambda room: Room(
                        room.name,
                        room.gridSpawns,
                        room.palette,
                        5,
                        1000.0,
                        1,
                        room.info.variant,
                        room.info.subtype,
                        room.info.shape,
                    ),
                    rooms,
                )
            )

            # Needs a padding room if all are skinny
            padMe = (
                next(
                    (
                        testRoom
                        for testRoom in newRooms
                        if testRoom.info.shape in [2, 3, 5, 7]
                    ),
                    None,
                )
                is not None
            )
            if padMe:
                newRooms.append(Room(difficulty=10, weight=0.1))

            # Make a new STB with a blank room
            path = os.path.join(roomsPath, basePath + ".stb")
            self.save(newRooms, path, updateRecent=False)

            # Prompt to restore backup
            message = "This method will not work properly if you have other mods that add rooms to the floor."
            if padMe:
                message += "\n\nAs the room has a non-standard shape, you may have to reset a few times for your room to appear."

            return [], newRooms, message

        self.testMapCommon("StageReplace", setup)

    # Test by replacing the starting room
    def testStartMap(self):
        def setup(modPath, roomsPath, floorInfo, testRoom, version):
            if len(testRoom) > 1:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Cannot test multiple rooms with Starting Room Replacement!",
                )
                raise
            testRoom = testRoom[0]

            if version not in ["Afterbirth+", "Repentance"]:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Starting Room Replacement not supported for {version}!",
                )
                raise

            # Sanity check for 1x1 room
            if testRoom.info.shape in [2, 7, 9]:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Room shapes 2 and 7 (Long and narrow) and 9 (L shaped with upper right corner missing) can't be tested as the Start Room.",
                )
                raise

            resourcePath = self.findResourcePath()
            if resourcePath == "":
                QMessageBox.warning(
                    self,
                    "Error",
                    "The resources folder could not be found. Please try reselecting it.",
                )
                raise

            roomPath = os.path.join(resourcePath, "rooms", "00.special rooms.stb")

            # Parse the special rooms, replace the spawns
            if not QFile.exists(roomPath):
                QMessageBox.warning(
                    self,
                    "Error",
                    "Missing 00.special rooms.stb from resources. Please unpack your resource files.",
                )
                raise

            startRoom = None
            roomFile = self.open(roomPath, False)
            for room in roomFile.rooms:
                if "Start Room" in room.name:
                    room.info.shape = testRoom.info.shape
                    room.gridSpawns = testRoom.gridSpawns
                    startRoom = room
                    break

            if not startRoom:
                QMessageBox.warning(
                    self, "Error", "00.special rooms.stb is not a valid STB file."
                )
                raise

            path = os.path.join(roomsPath, "00.special rooms.stb")

            # Resave the file
            self.save(roomFile.rooms, path, updateRecent=False)

            return [], [startRoom], ""

        self.testMapCommon("StartingRoom", setup)

    # Test by launching the game directly into the test room, skipping the menu
    def testMapInstapreview(self):
        def setup(modPath, roomsPath, floorInfo, rooms, version):
            testfile = "instapreview.xml"
            path = Path(modPath) / testfile
            path = path.resolve()

            roomsToUse = rooms

            # if there's a base game room file, override that. otherwise use special rooms
            newRooms = None
            if len(rooms) > 1:
                if (
                    version == "Afterbirth+"
                    and next(
                        (testRoom for testRoom in rooms if testRoom.info.type == 0),
                        None,
                    )
                    is not None
                ):
                    QMessageBox.warning(
                        self, "Error", f"{version} does not support the null room type."
                    )
                    raise

                baseSpecialPath = "00.special rooms"
                extraInfo = xmlLookups.stages.lookup(
                    stage=floorInfo.get("Stage"),
                    stageType=floorInfo.get("StageType"),
                    baseGamePath=True,
                )
                basePath = floorInfo.get("BaseGamePath") or extraInfo[-1].get(
                    "BaseGamePath"
                )

                # Set the selected rooms to have descending ids from max
                # this should avoid any id conflicts
                baseId = (2**31) - 1
                newRooms = list(
                    Room(
                        f"{room.name} [Real ID: {room.info.variant}]",
                        room.gridSpawns,
                        room.palette,
                        room.difficulty,
                        room.weight,
                        room.info.type,
                        baseId - i,
                        room.info.subtype,
                        room.info.shape,
                        room.info.doors,
                    )
                    for i, room in enumerate(rooms)
                )

                if basePath != baseSpecialPath:
                    specialRooms = list(
                        filter(lambda room: room.info.type != 1, newRooms)
                    )
                    normalRooms = list(
                        filter(lambda room: room.info.type <= 1, newRooms)
                    )

                    multiRoomPath = os.path.join(
                        modPath, "content", "rooms", baseSpecialPath + ".stb"
                    )
                    self.save(specialRooms, multiRoomPath, updateRecent=False)
                    multiRoomPath = os.path.join(
                        modPath, "content", "rooms", basePath + ".stb"
                    )
                    self.save(normalRooms, multiRoomPath, updateRecent=False)
                else:
                    multiRoomPath = os.path.join(
                        modPath, "content", "rooms", basePath + ".stb"
                    )
                    self.save(newRooms, multiRoomPath, updateRecent=False)

                roomsToUse = newRooms

            # Because instapreview is xml, no special allowances have to be made for rebirth
            self.save([roomsToUse[0]], path, updateRecent=False, isPreview=True)

            if version in ["Rebirth", "Antibirth"]:
                return (
                    [
                        "-room",
                        str(path),
                        "-floorType",
                        floorInfo.get("Stage"),
                        "-floorAlt",
                        floorInfo.get("StageType"),
                        "-console",
                    ],
                    None,
                    "",
                )

            return (
                [
                    f"--load-room={path}",
                    f"--set-stage={floorInfo.get('Stage')}",
                    f"--set-stage-type={floorInfo.get('StageType')}",
                ],
                newRooms,
                "",
            )

        self.testMapCommon("InstaPreview", setup)

    def findExecutablePath(self):
        if "Windows" in platform.system():
            installPath = findInstallPath()
            if installPath:
                exeName = "isaac-ng.exe"
                if QFile.exists(os.path.join(installPath, "isaac-ng-rebirth.exe")):
                    exeName = "isaac-ng-rebirth.exe"
                return os.path.join(installPath, exeName)

        return ""

    def findResourcePath(self):
        resourcesPath = ""

        if QFile.exists(settings.value("ResourceFolder")):
            resourcesPath = settings.value("ResourceFolder")

        else:
            installPath = findInstallPath()
            version = getGameVersion()

            if len(installPath) != 0:
                resourcesPath = os.path.join(installPath, "resources")
            # Fallback Resource Folder Locating
            else:
                resourcesPathOut = QFileDialog.getExistingDirectory(
                    self,
                    f"Please Locate The Binding of Isaac: {version} Resources Folder",
                )
                if not resourcesPathOut:
                    QMessageBox.warning(
                        self,
                        "Error",
                        "Couldn't locate resources folder and no folder was selected.",
                    )
                    return
                else:
                    resourcesPath = resourcesPathOut
                if resourcesPath == "":
                    QMessageBox.warning(
                        self,
                        "Error",
                        "Couldn't locate resources folder and no folder was selected.",
                    )
                    return
                if not QDir(resourcesPath).exists:
                    QMessageBox.warning(
                        self,
                        "Error",
                        "Selected folder does not exist or is not a folder.",
                    )
                    return
                if not QDir(os.path.join(resourcesPath, "rooms")).exists:
                    QMessageBox.warning(
                        self,
                        "Error",
                        "Could not find rooms folder in selected directory.",
                    )
                    return

            # Looks like nothing was selected
            if len(resourcesPath) == 0:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Could not find The Binding of Isaac: {version} Resources folder (%s)"
                    % resourcesPath,
                )
                return ""

            settings.setValue("ResourceFolder", resourcesPath)

        # Make sure 'rooms' exists
        roomsdir = os.path.join(resourcesPath, "rooms")
        if not QDir(roomsdir).exists:
            os.mkdir(roomsdir)
        return resourcesPath

    def killIsaac(self):
        for p in psutil.process_iter():
            try:
                if "isaac" in p.name().lower():
                    p.terminate()
            except:
                # This is totally kosher, I'm just avoiding zombies.
                pass

    def testMapCommon(self, testType, setupFunc):
        rooms = self.roomList.selectedRooms()
        if not rooms:
            QMessageBox.warning(self, "Error", "No rooms were selected to test.")
            return

        settings = QSettings("settings.ini", QSettings.IniFormat)
        version = getGameVersion()

        global xmlLookups
        floorInfo = mainWindow.floorInfo

        forceCleanModFolder = settings.value("HelperModDev") == "1"
        modPath, roomPath = self.makeTestMod(forceCleanModFolder)
        if modPath == "":
            QMessageBox.warning(
                self,
                "Error",
                "The basement renovator mod folder could not be copied over: "
                + str(roomPath),
            )
            return

        # Ensure that the room data is up to date before writing
        self.storeEntityList()

        # Call unique code for the test method
        launchArgs, extraMessage = None, None
        try:
            # setup raises an exception if it can't continue
            launchArgs, roomsOverride, extraMessage = setupFunc(
                modPath, roomPath, floorInfo, rooms, version
            ) or ([], None, "")
        except Exception as e:
            printf(
                "Problem setting up test:",
                "".join(traceback.format_exception(*sys.exc_info())),
            )
            return

        testRooms = roomsOverride or rooms
        self.writeTestData(modPath, testType, floorInfo, testRooms)

        testfile = "testroom.xml"
        testPath = Path(modPath) / testfile
        testPath = testPath.resolve()
        self.save(testRooms, testPath, fileObj=self.roomList.file, updateRecent=False)

        # Trigger test hooks
        testHooks = settings.value("HooksTest")
        if testHooks:
            tp = os.path.abspath(testPath)
            for hook in testHooks:
                wd, script = os.path.split(hook)
                try:
                    subprocess.run([hook, tp, "--test"], cwd=wd, timeout=60)
                except Exception as e:
                    printf("Test hook failed! Reason:", e)

        # Launch Isaac
        installPath = findInstallPath()
        if not installPath:
            QMessageBox.warning(
                self,
                "Error",
                "Your install path could not be found! You may have the wrong directory, reconfigure in settings.ini",
            )
            return

        now = datetime.datetime.now(datetime.timezone.utc)
        for room in rooms:
            room.lastTestTime = now
        self.dirt()  # dirty for test timestamps

        try:
            # try to run through steam to avoid steam confirmation popup, else run isaac directly
            # if there exists drm free copies, allow the direct exe launch method
            steamPath = None
            if version != "Antibirth" and settings.value("ForceExeLaunch") != "1":
                steamPath = getSteamPath() or ""

            if steamPath:
                exePath = f"{steamPath}\\Steam.exe"
            else:
                exePath = self.findExecutablePath()

            if (
                exePath
                and QFile.exists(exePath)
                and settings.value("ForceUrlLaunch") != "1"
            ):
                if steamPath:
                    launchArgs = ["-applaunch", "250900"] + launchArgs

                appArgs = [exePath] + launchArgs
                printf("Test: Running executable", " ".join(appArgs))
                subprocess.Popen(appArgs, cwd=installPath)
            else:
                args = " ".join(map(lambda x: " " in x and f'"{x}"' or x, launchArgs))
                urlArgs = urllib.parse.quote(args)
                urlArgs = re.sub(r"/", "%2F", urlArgs)

                url = f"steam://rungameid/250900//{urlArgs}"
                printf("Test: Opening url", url)
                webbrowser.open(url)

        except Exception as e:
            traceback.print_exception(*sys.exc_info())
            QMessageBox.warning(self, "Error", f"Failed to test with {testType}: {e}")
            return

        settings = QSettings("settings.ini", QSettings.IniFormat)
        if settings.value("DisableTestDialog") == "1":
            # disable mod in 5 minutes
            if self.disableTestModTimer:
                self.disableTestModTimer.disconnect()
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self.disableTestMod(modPath))
            self.disableTestModTimer = timer
            timer.start(5 * 60 * 1000)

            if extraMessage:
                QMessageBox.information(self, "BR Test", extraMessage)

        else:
            # Prompt to disable mod and perform cleanup
            # for some reason, if the dialog blocks on the button click,
            # e.g. QMessageBox.information() or msg.exec(), isaac crashes on launch.
            # This is probably a bug in python or Qt
            msg = QMessageBox(
                QMessageBox.Information,
                "Disable BR",
                (extraMessage and (extraMessage + "\n\n") or "")
                + 'Press "OK" when done testing to disable the BR helper mod.',
                QMessageBox.Ok,
                self,
            )

            def fin(button):
                result = msg.standardButton(button)
                if result == QMessageBox.Ok:
                    self.disableTestMod(modPath)

                self.killIsaac()

            msg.buttonClicked.connect(fin)
            msg.open()

    # Edit
    ########################

    # @pyqtSlot()
    def selectAll(self):
        path = QPainterPath()
        path.addRect(self.scene.sceneRect())
        self.scene.setSelectionArea(path)

    # @pyqtSlot()
    def deSelect(self):
        self.scene.clearSelection()

    # @pyqtSlot()
    def copy(self):
        self.clipboard = []
        for item in self.scene.selectedItems():
            self.clipboard.append(
                [
                    item.entity.x,
                    item.entity.y,
                    item.entity.Type,
                    item.entity.Variant,
                    item.entity.Subtype,
                    item.entity.weight,
                ]
            )

    # @pyqtSlot()
    def cut(self):
        self.clipboard = []
        for item in self.scene.selectedItems():
            self.clipboard.append(
                [
                    item.entity.x,
                    item.entity.y,
                    item.entity.Type,
                    item.entity.Variant,
                    item.entity.Subtype,
                    item.entity.weight,
                ]
            )
            item.remove()

    # @pyqtSlot()
    def paste(self):
        if not self.clipboard:
            return

        self.scene.clearSelection()
        for item in self.clipboard:
            ent = Entity(*item)
            ent.setSelected(True)

        self.dirt()

    def showReplaceDialog(self):
        replaceDialog = ReplaceDialog()
        if replaceDialog.exec() != QDialog.Accepted:
            return

        self.replaceEntities(
            replaceDialog.fromEnt.getEnt(), replaceDialog.toEnt.getEnt()
        )

    # Miscellaneous
    ########################

    def toggleSetting(self, setting, onDefault=False):
        settings = QSettings("settings.ini", QSettings.IniFormat)
        a, b = onDefault and ("0", "1") or ("1", "0")
        settings.setValue(setting, settings.value(setting) == a and b or a)
        self.scene.update()

    # @pyqtSlot()
    def showPainter(self):
        if self.EntityPaletteDock.isVisible():
            self.EntityPaletteDock.hide()
        else:
            self.EntityPaletteDock.show()

        self.updateDockVisibility()

    # @pyqtSlot()
    def showRoomList(self):
        if self.roomListDock.isVisible():
            self.roomListDock.hide()
        else:
            self.roomListDock.show()

        self.updateDockVisibility()

    # @pyqtSlot()
    def updateDockVisibility(self):
        if self.EntityPaletteDock.isVisible():
            self.wb.setText("Hide Entity Painter")
        else:
            self.wb.setText("Show Entity Painter")

        if self.roomListDock.isVisible():
            self.wc.setText("Hide Room List")
        else:
            self.wc.setText("Show Room List")

    # @pyqtSlot()
    def resetWindowDefaults(self):
        self.restoreState(self.resetWindow["state"], 0)
        self.restoreGeometry(self.resetWindow["geometry"])

    # Help
    ########################

    # @pyqtSlot(bool)
    def aboutDialog(self):
        caption = "About the Basement Renovator"

        text = """
            <big><b>Basement Renovator</b></big><br>
            <br>
            Basement Renovator is a room editor for the Binding of Isaac Rebirth and its DLCs and mods. You can use it to either edit existing rooms or create new ones.<br>
            <br>
            To edit the game's existing rooms, you must have unpacked the .stb files by using the game's resource extractor. (On Windows, this is located at "C:\\Program Files (x86)\\Steam\\steamapps\\common\\The Binding of Isaac Rebirth\\tools\\ResourceExtractor\\ResourceExtractor.exe".)<br>
            <br>
            Basement Renovator was originally programmed by Tempus (u/Chronometrics). It is open source and hosted on <a href='https://github.com/Tempus/Basement-Renovator'>GitHub</a>.
        """

        msg = QMessageBox.about(mainWindow, caption, text)

    # @pyqtSlot(bool)
    def goToHelp(self):
        QDesktopServices().openUrl(
            QUrl("https://github.com/Tempus/Basement-Renovator/")
        )


def applyDefaultSettings(settings, defaults):
    for key, val in defaults.items():
        if settings.value(key) is None:
            settings.setValue(key, val)


if __name__ == "__main__":
    import sys

    min_version = [3, 7]
    if not (
        sys.version_info[0] > min_version[0]
        or (
            sys.version_info[0] == min_version[0]
            and sys.version_info[1] >= min_version[1]
        )
    ):
        raise NotImplementedError(
            f"Basement Renovator requires minimum Python {min_version[0]}.{min_version[1]}, your version: {sys.version_info[0]}.{sys.version_info[0]}"
        )

    # Application
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("resources/UI/BasementRenovator.png"))

    cmdParser = QCommandLineParser()
    cmdParser.setApplicationDescription(
        "Basement Renovator is a room editor for The Binding of Isaac: Rebirth and its DLCs and mods"
    )
    cmdParser.addHelpOption()

    cmdParser.addPositionalArgument(
        "file", "optional file to open on launch, otherwise opens most recent file"
    )

    cmdParser.process(app)

    settings = QSettings("settings.ini", QSettings.IniFormat)

    applyDefaultSettings(settings, {"SnapToBounds": "1", "ExportSTBOnSave": "1"})

    # XML Globals
    version = getGameVersion()
    xmlLookups = MainLookup(version, settings.value("Verbose") == "1")
    if settings.value("DisableMods") != "1":
        loadMods(
            settings.value("ModAutogen") == "1",
            findInstallPath(),
            settings.value("ResourceFolder", ""),
        )

    printf("-".join(["" for i in range(50)]))
    printf("INITIALIZING MAIN WINDOW")
    mainWindow = MainWindow()

    settings.setValue("FixIconFormat", "0")

    startFile = None

    args = cmdParser.positionalArguments()
    if args:
        startFile = args[0]
    else:
        recent = settings.value("RecentFiles", [])
        if recent:
            startFile = recent[0]

    if startFile and os.path.exists(startFile):
        mainWindow.openWrapper(startFile)

    mainWindow.show()

    sys.exit(app.exec())
