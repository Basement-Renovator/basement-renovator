"""
Merges room files into one specified by a config file
"""
from pathlib import Path

import subprocess, json

from PyQt5.QtCore import QCommandLineOption, QCommandLineParser
from PyQt5.QtWidgets import QApplication


def mergeRooms(configList, scriptPath, cwd, fileEdited=None):
    print("Script path:", scriptPath)
    for config in configList:
        if fileEdited:
            skipConfig = True
            for path in config["paths"]:
                path = (cwd / path).absolute().resolve()
                if (path.is_dir() and fileEdited.parent == path) or path == fileEdited:
                    skipConfig = False
                    break

            if skipConfig:
                continue

        print("Current config:", config)

        args = (
            ["python", scriptPath, "--output", config["outputFile"]]
            + config["paths"]
            + (["--stb"] if not config.get("skipSTB") else [])
            + (["--noRecomputeIds"] if config.get("noRecomputeIds") else [])
            + (
                []
                if not config.get("startingId")
                else ["--startingId", str(config["startingId"])]
            )
        )

        subprocess.run(args, cwd=cwd)


def runmain():
    import sys

    app = QApplication(sys.argv)

    cmdParser = QCommandLineParser()
    cmdParser.setApplicationDescription(
        "Room file merger utility script for Basement Renovator. Takes a config file and feeds it to the cli roommerger script"
    )
    cmdParser.addHelpOption()

    cmdParser.addPositionalArgument(
        "configFile",
        """json config file to grab configuration from; sets current working directory to its directory. Format:
    {
        files: [
            {
                outputFile: path to file to output,
                paths: [ path to file/folder to replace, ... ],
                skipSTB: optional, true to skip generating the stb,
                noRecomputeIds: optional, true to skip recompute room ids,
                startingId: starting room id to recompute from
            }...
        ]
    }
    """,
    )

    fileEditedOpt = QCommandLineOption(
        "fileEdited",
        "optional file to limit which rooms get merged from the config",
        "file",
    )
    cmdParser.addOption(fileEditedOpt)

    cmdParser.process(app)

    configArg = cmdParser.positionalArguments()[0]
    configPath = Path(configArg).absolute().resolve()
    if not configArg or not configPath.is_file():
        print("Invalid config path!")
        return

    fileEditedArg = cmdParser.value(fileEditedOpt)
    fileEditedPath = None
    if fileEditedArg:
        fileEditedPath = Path(fileEditedArg).absolute().resolve()
        if not fileEditedPath.is_file():
            print("Invalid edited file path!")
            return

    scriptPath = Path(__file__ + "/../roommerger.py").absolute().resolve()

    with open(configPath) as configFile:
        config = json.load(configFile)

        mergeRooms(
            config["files"],
            str(scriptPath),
            configPath.parent,
            fileEdited=fileEditedPath,
        )

    print("Success! Merged all.")


if __name__ == "__main__":
    runmain()
