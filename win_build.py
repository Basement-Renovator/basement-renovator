from pathlib import Path
import sys, subprocess, shutil, os

if os.path.exists("dist"):
    shutil.rmtree("dist")


def exe(
    pyfile,
    name="",
    dest="",
    creator="PyInstaller",
    ico="",
    noconsole=False,
    versionFile="",
    addtlFiles: list[tuple[str, Path, str]] = [],
):
    args = [
        "uv",
        "run",
        "python",
        "-u",
        "-m",
        creator,
        pyfile,
        "-F",
        "--clean",
        "--distpath",
        str(dest or os.path.split(pyfile)[0]),
    ]
    if name:
        args.extend(("-n", name))
    if ico:
        args.extend(("-i", ico))
    if versionFile:
        args.extend(("--version-file", versionFile))
    if noconsole:
        args.append("--noconsole")

    for ty, src, dst in addtlFiles:
        args.extend(
            (
                ty == "binary" and "--add-binary" or "--add-data",
                f"{os.path.normpath(str(src))};{os.path.normpath(dst)}",
            )
        )

    print(args)
    subprocess.check_output(args)


# When running from uv, the exec path is under .venv/Scripts, but we want .venv itself
venvdir = Path(sys.executable).parent.parent
qt5dir = venvdir / "Lib/site-packages/PyQt5/Qt5"

# TODO once log files are added, disable the console
exe(
    "BasementRenovator.py",
    name="Basement Renovator",
    dest="dist",
    versionFile="winversion.txt",
    ico=os.path.normpath("resources/UI/BasementRenovator.ico"),
    addtlFiles=[
        (
            "binary",
            qt5dir / "plugins/platforms/qwindows.dll",
            "./platforms",
        ),
        (
            "binary",
            qt5dir / "bin/libEGL.dll",
            ".",
        ),
    ],
)

addtl = [
    ("resources", ""),
    ("README.md", ""),
    ("NicheFeatures.md", ""),
]

for src, dest in addtl:
    dest = os.path.join("dist", dest, os.path.split(src)[1])
    print(dest)
    if os.path.isdir(src):
        shutil.copytree(src, dest)
    else:
        shutil.copy2(src, dest)
