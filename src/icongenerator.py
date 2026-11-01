"""
Generates icons for BR from an anm2 file
"""

import os, platform, re
import xml.etree.cElementTree as ET
from pathlib import Path

from PyQt5.QtCore import QSettings, QFile, QDir, QCommandLineOption, QCommandLineParser
from PyQt5.QtWidgets import QMessageBox, QApplication, QFileDialog

if not __package__:
    import anm2 as anm2
    from util import *
    from lookup import MainLookup
    from version import getGameVersion
else:
    import src.anm2 as anm2
    from src.util import *
    from src.lookup import MainLookup
    from src.version import getGameVersion


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
            printf(
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


def findModPath(file: Path):
    """
    Returns the root folder of the mod containing file, if it's within the mods folder, otherwise None
    """
    modPath = next(
        (
            parent
            for parent in file.resolve().parents
            if (parent / "metadata.xml").is_file()
        ),
        None,
    )

    return modPath


def getModName(modPath):
    try:
        name = ET.parse(modPath / "metadata.xml").getroot().find("name")
        if name is not None and name.text:
            return name.text
    except ET.ParseError:
        printf(
            f'Failed to parse mod metadata "{modPath.name}", falling back on default name'
        )

    return modPath.name


def createIcon(file, animName, frame, overlayName, overlayFrame, noScale, mod):
    anim = anm2.Config(file, mod)

    anim.setAnimation(animName)
    if frame:
        anim.frame = frame

    if overlayName:
        anim.setOverlay(overlayName)
        if overlayFrame:
            anim.overlayFrame = overlayFrame

    img = anim.render(noScale=noScale)

    if img and not img.isNull():
        filename = f"{os.path.splitext(anim.file)[0]}.png"
        img.save(filename, "PNG")
        printf(f"Saved icon to {filename}")
    else:
        raise ValueError("Failed to render image from animation")


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    cmdParser = QCommandLineParser()
    cmdParser.setApplicationDescription(
        "Icon generator utility script for Basement Renovator. Takes an anm2 "
    )
    cmdParser.addHelpOption()

    cmdParser.addPositionalArgument("file", "anm2 file to generate the icon from")

    verboseOpt = QCommandLineOption("verbose", "Enable verbose output")
    cmdParser.addOption(verboseOpt)

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
    fileArg = Path(args[0]).resolve()

    frameArg = int(cmdParser.value(frameOpt))
    animArg = cmdParser.value(animOpt)

    overlayArg = cmdParser.value(overlayOpt)
    overlayFrameArg = int(cmdParser.value(overlayFrameOpt))

    noScaleArg = cmdParser.isSet(noScaleOpt)

    settings = QSettings(str(BR_ROOT / "settings.ini"), QSettings.IniFormat)

    resources = settings.value("ResourceFolder", "")
    printf("Resource Path:", resources)

    xmlLookups = MainLookup(
        getGameVersion(), BR_ROOT / "resources/", resources, cmdParser.isSet(verboseOpt)
    )

    mod = xmlLookups.basemod

    # if the file is inside the mod folder (and not inside BR),
    # and recursively within a mod dir, load that mod
    if not fileArg.is_relative_to(BR_ROOT):
        modsFolder = findModsPath()
        if modsFolder and fileArg.is_relative_to(modsFolder):
            modPath = findModPath(fileArg)
            if modPath:
                modName = getModName(modPath)
                printf(f'Loading mod "{modName}" from {modPath}')
                mod = xmlLookups.loadFromMod(
                    modPath, modPath / "basementrenovator", modName, False
                )

    createIcon(fileArg, animArg, frameArg, overlayArg, overlayFrameArg, noScaleArg, mod)
    printf("Success!")
