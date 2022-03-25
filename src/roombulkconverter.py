"""
Converts stb files into xml
"""
from pathlib import Path

import subprocess
import roomconvert as cvt

from PyQt5.QtCore import QCommandLineOption, QCommandLineParser, QSettings
from PyQt5.QtWidgets import QApplication


def runmain():
    import sys

    app = QApplication(sys.argv)

    cmdParser = QCommandLineParser()
    cmdParser.setApplicationDescription(
        "Room file converter utility script for Basement Renovator. Takes a set of file paths"
    )
    cmdParser.addHelpOption()

    cmdParser.addPositionalArgument("file", "stb files to convert")

    skipOpt = QCommandLineOption(
        "roomconvert", "placeholder argument used to prevent recursive execution"
    )
    cmdParser.addOption(skipOpt)

    cmdParser.process(app)

    if cmdParser.isSet(skipOpt):
        print("Recursive execution from save hook, skipping")
        return

    paths = cmdParser.positionalArguments()
    if not paths:
        print("Must specify at least one file to merge!")
        return

    i = -1
    while (i + 1) < len(paths):
        i += 1

        file = paths[i]

        path = Path(file)
        if path.is_dir():
            files = list(filter(lambda f: f.suffix == ".stb", path.iterdir()))
            print("Adding stb files to queue from: ", path)
            del paths[i]
            i -= 1
            paths.extend(files)

    paths = list(filter(lambda f: Path(f).exists(), paths))

    for file in paths:
        print("----")
        print("Converting path:", file)

        path = Path(file)

        if path.suffix != ".stb":
            print("Must be stb! Skipping!")
            continue

        outputFilePath = path.with_suffix('.xml')
        roomFile = cvt.stbToCommon(path)
        cvt.commonToXML(outputFilePath, roomFile.rooms, file=roomFile)

    print("----")
    print('Done!')


if __name__ == "__main__":
    runmain()
