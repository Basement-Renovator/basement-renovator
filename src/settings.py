from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import platform
import os
from pathlib import Path
import xml.etree.cElementTree as ET
import re

if not __package__:
    from util import *
else:
    from src.util import *


def getBasementRenovatorPath():
    path = Path(__file__).parent.parent
    return str(path)


settings = QSettings(getBasementRenovatorPath() + "/settings.ini", QSettings.IniFormat)


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


class ModPath:
    def __init__(self, modName, modPath, brPath):
        self.name = modName
        self.path = modPath
        self.brPath = brPath


def listModFolders(installPath, includeNonBrMods):
    # Each mod in the mod folder is a Group
    modsPath = findModsPath(installPath)
    if not os.path.isdir(modsPath):
        printf("Could not find Mods Folder! Skipping mod content!")
        return []

    modsInstalled = os.listdir(modsPath)

    mods = []

    for mod in modsInstalled:
        modPath = os.path.join(modsPath, mod)
        brPath = os.path.join(modPath, "basementrenovator")

        # Make sure we're a mod
        if not os.path.isdir(modPath) or os.path.isfile(
            os.path.join(modPath, "disable.it")
        ):
            continue

        # simple workaround for now
        if not (includeNonBrMods or os.path.exists(brPath)):
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

        mods.append(ModPath(modName, modPath, brPath))

    return mods
