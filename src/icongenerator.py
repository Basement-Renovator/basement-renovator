"""
Generates icons for BR from an anm2 file
"""
import os, platform, re

import anm2

from PyQt5.QtCore import QSettings, QFile, QDir, QCommandLineOption, QCommandLineParser
from PyQt5.QtWidgets import QMessageBox, QApplication, QFileDialog


def findInstallPath():
    installPath = ""
    cantFindPath = False

    if QFile.exists(settings.value("InstallFolder")):
        installPath = settings.value("InstallFolder")

    else:
        # Windows path things
        if "Windows" in platform.system():
            basePath = QSettings(
                "HKEY_CURRENT_USER\\Software\\Valve\\Steam", QSettings.NativeFormat
            ).value("SteamPath")
            if not basePath:
                cantFindPath = True

            installPath = os.path.join(
                basePath, "steamapps", "common", "The Binding of Isaac Rebirth"
            )
            if not QFile.exists(installPath):
                cantFindPath = True

                libconfig = os.path.join(basePath, "steamapps", "libraryfolders.vdf")
                if os.path.isfile(libconfig):
                    libLines = list(open(libconfig, "r"))
                    matcher = re.compile(r'"\d+"\s*"(.*?)"')
                    installDirs = map(
                        lambda res: os.path.normpath(res.group(1)),
                        filter(lambda res: res, map(matcher.search, libLines)),
                    )
                    for root in installDirs:
                        installPath = os.path.join(
                            root, "steamapps", "common", "The Binding of Isaac Rebirth"
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
            print(
                f"Could not find The Binding of Isaac: Afterbirth+ install folder ({installPath})"
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
            modd = os.path.join(installPath, "savedatapath.txt")
            if os.path.isfile(modd):
                lines = list(open(modd, "r"))
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

    if cantFindPath:
        cantFindPath = False
        # Windows path things
        if "Windows" in platform.system():
            modsPath = os.path.join(
                os.path.expanduser("~"),
                "Documents",
                "My Games",
                "Binding of Isaac Afterbirth+ Mods",
            )
            if not QFile.exists(modsPath):
                cantFindPath = True

        # Mac Path things
        elif "Darwin" in platform.system():
            modsPath = os.path.expanduser(
                "~/Library/Application Support/Binding of Isaac Afterbirth+ Mods"
            )
            if not QFile.exists(modsPath):
                cantFindPath = True

        # Linux and others
        else:
            modsPath = os.path.expanduser(
                "~/.local/share/binding of isaac afterbirth+ mods/"
            )
            if not QFile.exists(modsPath):
                cantFindPath = True

        # Fallback Resource Folder Locating
        if cantFindPath:
            modsPathOut = QFileDialog.getExistingDirectory(
                None, "Please Locate The Binding of Isaac: Afterbirth+ Mods Folder"
            )
            if not modsPathOut:
                QMessageBox.warning(
                    None,
                    "Error",
                    "Couldn't locate Mods folder and no folder was selected.",
                )
                return ""
            else:
                modsPath = modsPathOut
            if modsPath == "":
                QMessageBox.warning(
                    None,
                    "Error",
                    "Couldn't locate Mods folder and no folder was selected.",
                )
                return ""
            if not QDir(modsPath).exists:
                QMessageBox.warning(
                    None, "Error", "Selected folder does not exist or is not a folder."
                )
                return ""

        # Looks like nothing was selected
        if modsPath == "" or not os.path.isdir(modsPath):
            QMessageBox.warning(
                None,
                "Error",
                f"Could not find The Binding of Isaac: Afterbirth+ Mods folder ({modsPath})",
            )
            return ""

        settings.setValue("ModsFolder", modsPath)

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


def createIcon(
    file, animName, frame, overlayName, overlayFrame, noScale, resourcesPath
):
    anim = anm2.Config(file, resourcesPath)

    anim.setAnimation(animName)
    if frame:
        anim.frame = frame

    if overlayName:
        anim.setOverlay(overlayName)
        if overlayFrame:
            anim.overlayFrame = overlayFrame

    img = anim.render(noScale=noScale)

    filename = "resources/Entities/questionmark.png"
    if img:
        filename = f"{os.path.splitext(anim.file)[0]}.png"
    img.save(filename, "PNG")


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    cmdParser = QCommandLineParser()
    cmdParser.setApplicationDescription(
        "Icon generator utility script for Basement Renovator. Takes an anm2 "
    )
    cmdParser.addHelpOption()

    cmdParser.addPositionalArgument("file", "anm2 file to generate the icon from")

    frameOpt = QCommandLineOption(
        ["f", "frame"], "frame in the anm2 to use, defaults to 0", "f", "0"
    )
    cmdParser.addOption(frameOpt)

    animOpt = QCommandLineOption(
        ["n", "anim"],
        "name of the animation in the anm2 to use, defaults to the default anim",
        "n",
    )
    cmdParser.addOption(animOpt)

    overlayOpt = QCommandLineOption(
        ["o", "overlay-anim"],
        "name of an animation in the anm2 to use as an overlay (optional)",
        "o",
    )
    cmdParser.addOption(overlayOpt)

    overlayFrameOpt = QCommandLineOption(
        ["of", "overlay-frame"],
        "frame in the overlay animation to use, defaults to 0",
        "of",
        "0",
    )
    cmdParser.addOption(overlayFrameOpt)

    noScaleOpt = QCommandLineOption("noscale", "turns off scaling in anm2")
    cmdParser.addOption(noScaleOpt)

    cmdParser.process(app)

    args = cmdParser.positionalArguments()
    fileArg = args[0]

    frameArg = int(cmdParser.value(frameOpt))
    animArg = cmdParser.value(animOpt)

    overlayArg = cmdParser.value(overlayOpt)
    overlayFrameArg = int(cmdParser.value(overlayFrameOpt))

    noScaleArg = cmdParser.isSet(noScaleOpt)

    settings = QSettings("../settings.ini", QSettings.IniFormat)

    resources = settings.value("ResourceFolder", "")
    print("Resource Path:", resources)

    createIcon(
        fileArg, animArg, frameArg, overlayArg, overlayFrameArg, noScaleArg, resources
    )
    print("Success!")
