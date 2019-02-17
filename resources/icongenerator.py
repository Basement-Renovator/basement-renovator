'''
Generates icons for BR from an anm2 file
'''
import os, platform, re
import xml.etree.ElementTree as ET
from pathlib import Path

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

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
                                             map(matcher.search, libLines)))
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
                return ''
            else:
                modsPath = modsPathOut
            if modsPath == "":
                QMessageBox.warning(None, "Error", "Couldn't locate Mods folder and no folder was selected.")
                return ''
            if not QDir(modsPath).exists:
                QMessageBox.warning(None, "Error", "Selected folder does not exist or is not a folder.")
                return ''

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

def extractFrames(anim, frameNumber, spritesheets, layers, anm2Dir, resourcePath):
    framelayers = anim.findall(".//LayerAnimation[Frame]")

    imgs = []
    ignoreCount = 0
    for layer in framelayers:
        if layer.get('Visible') == 'false':
            ignoreCount += 1
            continue

        frames = layer.findall('Frame')
        currFrame = 0
        correctFrame = None
        for frame in frames:
            duration = int(frame.get('Delay'))
            if currFrame + duration > frameNumber:
                correctFrame = frame
                break
            currFrame += duration

        if correctFrame is None:
            correctFrame = frames[-1]

        frame = correctFrame
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
            xs = float(frame.get("XScale")) / 100
            ys = float(frame.get("YScale")) / 100
            w = int(frame.get("Width"))
            h = int(frame.get("Height"))

            imgs.append([imgPath, x, y, xc, yc, w, h, xs, ys, r, xp, yp])

    if not imgs:
        print(f'Entity Icon could not be generated from animation due to {ignoreCount > 0 and "visibility" or "missing files"}')

    return imgs


def createIcon(anmPath, animName, frameNumber, overlayAnim, overlayFrame, resourcePath):
    if not os.path.isfile(anmPath):
        print('Skipping: Invalid anm2!')
        return None

    anm2Dir, anm2File = os.path.split(anmPath)

    # Grab the first frame of the anm
    anmTree = ET.parse(anmPath)
    spritesheets = anmTree.findall(".Content/Spritesheets/Spritesheet")
    layers = anmTree.findall(".Content/Layers/Layer")

    default = anmTree.find("Animations").get("DefaultAnimation")

    animName = animName or default
    anim = anmTree.find(f"./Animations/Animation[@Name='{animName}']")
    if anim is None:
        print('Invalid animation name given')
        anim = anmTree.find(f"./Animations/Animation[@Name='{default}']")

    print('Reading main animation...')
    imgs = extractFrames(anim, frameNumber, spritesheets, layers, anm2Dir, resourcePath)

    if overlayAnim:
        overlay = anmTree.find(f"./Animations/Animation[@Name='{overlayAnim}']")
        if overlay is None:
            print('Invalid overlay animation name given')
        else:
            print('Reading overlay animation...')
            imgs += extractFrames(overlay, overlayFrame, spritesheets, layers, anm2Dir, resourcePath)

    filename = "resources/Entities/questionmark.png"
    if imgs:

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

            cropRect.moveTopLeft(QPoint())
            cropRect = mat.mapRect(cropRect)
            cropRect.translate(QPoint(x, y))
            finalRect = finalRect.united(cropRect)
            img.append(cropRect)

        # Create the destination
        pixmapImg = QImage(finalRect.width(), finalRect.height(), QImage.Format_ARGB32)
        pixmapImg.fill(0)

        # Paint all the layers to it
        renderPainter = QPainter(pixmapImg)
        for imgPath, x, y, xc, yc, w, h, xs, ys, r, xp, yp, sourceImage, boundingRect in imgs:
            # Transfer the crop area to the pixmap
            boundingRect.translate(-finalRect.topLeft())
            renderPainter.drawImage(boundingRect, sourceImage)
        renderPainter.end()

        filename = f'{os.path.splitext(anm2File)[0]}.png'
        pixmapImg.save(filename, "PNG")

if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    cmdParser = QCommandLineParser()
    cmdParser.setApplicationDescription('Icon generator utility script for Basement Renovator. Takes an anm2 ')
    cmdParser.addHelpOption()

    cmdParser.addPositionalArgument('file', 'anm2 file to generate the icon from')

    frameOpt = QCommandLineOption(['f', 'frame'], 'frame in the anm2 to use, defaults to 0', 'f', '0')
    cmdParser.addOption(frameOpt)

    animOpt = QCommandLineOption(['n', 'anim'], 'name of the animation in the anm2 to use, defaults to the default anim', 'n')
    cmdParser.addOption(animOpt)

    overlayOpt = QCommandLineOption(['o', 'overlay-anim'], 'name of an animation in the anm2 to use as an overlay (optional)', 'o')
    cmdParser.addOption(overlayOpt)

    overlayFrameOpt = QCommandLineOption(['of', 'overlay-frame'], 'frame in the overlay animation to use, defaults to 0', 'of', '0')
    cmdParser.addOption(overlayFrameOpt)

    cmdParser.process(app)

    args = cmdParser.positionalArguments()
    fileArg = args[0]

    frameArg = int(cmdParser.value(frameOpt))
    animArg = cmdParser.value(animOpt)

    overlayArg = cmdParser.value(overlayOpt)
    overlayFrameArg = int(cmdParser.value(overlayFrameOpt))

    settings = QSettings('../settings.ini', QSettings.IniFormat)

    resources = settings.value('ResourceFolder', '')
    print('Resource Path:', resources)

    createIcon(fileArg, animArg, frameArg, overlayArg, overlayFrameArg, resources)
    print('Success!')
