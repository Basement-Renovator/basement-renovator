from PyQt5.QtCore import QSettings

if not __package__:
    from util import BR_ROOT
else:
    from src.util import BR_ROOT


def getGameVersion():
    """
    Returns the current compatibility mode, and the sub version if it exists
    """
    # default mode if not set
    settings = QSettings(str(BR_ROOT / "settings.ini"), QSettings.IniFormat)
    mode = settings.value("CompatibilityMode", "Repentance+")

    return mode


def willLaunchREPENTOGON():
    settings = QSettings(str(BR_ROOT / "settings.ini"), QSettings.IniFormat)
    exePath: str | None = settings.value("CustomExePath")
    return exePath and exePath.lower().endswith("repentogonlauncher.exe")


def canUseREPENTOGON():
    if getGameVersion() != "Repentance+":
        return False

    return willLaunchREPENTOGON()
