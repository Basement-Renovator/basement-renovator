"""
Generates a readout of various room file and entity usage statistics specified by a config file
"""
from pathlib import Path

import sys
import subprocess, json

from PyQt5.QtCore import QCommandLineParser
from PyQt5.QtWidgets import QApplication


def runmain():
    app = QApplication(sys.argv)

    cmdParser = QCommandLineParser()
    cmdParser.setApplicationDescription(
        "Room file statistics utility script for Basement Renovator. Takes a config file and feeds it to the cli roomstatistics script"
    )
    cmdParser.addHelpOption()

    cmdParser.addPositionalArgument(
        "configFile",
        """json config file to grab configuration from; sets current working directory to its directory. Format:
    {
        outputFile: txt file to store output in, if not specified prints to stdout,
        errorFile: txt file to store errors in, if not specified errors are discarded,
        useStatisticsGroups: whether to group entities with a StatisticsGroup tag together,
        roomThreshold: how many rooms an entity must appear in to be tracked,
        files: [
            {
                groupName: optional name of group that all file paths fall under,
                paths: [ path to file/folder to read statistics from, ... ]
            }...
        ]
    }

    Note that groupName must be set either for each set of paths or for none.
    """,
    )

    cmdParser.process(app)

    configArg = cmdParser.positionalArguments()[0]
    configPath = Path(configArg).absolute().resolve()
    if not configArg or not configPath.is_file():
        print("Invalid config path!")
        return

    scriptPath = Path(__file__ + "/../roomstatistics.py").absolute().resolve()

    with open(configPath) as configFile:
        config = json.load(configFile)

        if not "files" in config:
            print(
                'Config is formatted incorrectly! Requires "files" list. Use -h to see an example!'
            )
            return

        args = ["python", scriptPath]
        if "outputFile" in config:
            args.extend(["--output", config["outputFile"]])
        if "errorFile" in config:
            args.extend(["--errors", config["errorFile"]])
        if "roomThreshold" in config:
            args.extend(["--roomThreshold", str(config["roomThreshold"])])
        if "statisticsGroups" in config and config["statisticsGroups"]:
            args.extend(["--statisticsGroups"])

        usingGroups = None
        for configList in config["files"]:
            if not "paths" in configList:
                print(
                    'Config is formatted incorrectly! Requires "paths" list for each entry in "files" list. Use -h to see an example!'
                )
                return

            if "groupName" in configList:
                if usingGroups is False:
                    print(
                        'Config is formatted incorrectly! Either all entries in "files" list must have "groupName", or none can. Use -h to see an example!'
                    )
                    return
                elif usingGroups is None:
                    args.extend(["--groupFiles"])
                    usingGroups = True

                for path in configList["paths"]:
                    args.extend([path, configList["groupName"]])
            elif usingGroups:
                print(
                    'Config is formatted incorrectly! Either all entries in "files" list must have "groupName", or none can. Use -h to see an example!'
                )
                return
            else:
                args.extend(configList["paths"])

        subprocess.run(args, cwd=configPath.parent)


if __name__ == "__main__":
    runmain()
