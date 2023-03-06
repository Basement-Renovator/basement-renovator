from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import struct, os
import xml.etree.ElementTree as ET


def getEntity(id, subtype, variant):
    global entityXML
    ret = {}

    try:
        if subtype == 0 and variant == 0:
            en = entityXML.find("entity[@id='{0}']".format(id))
        elif subtype == 0:
            en = entityXML.find("entity[@id='{0}'][@variant='{1}']".format(id, variant))
        elif variant == 0:
            en = entityXML.find("entity[@id='{0}'][@subtype='{1}']".format(id, subtype))
        else:
            en = entityXML.find(
                "entity[@id='{0}'][@subtype='{1}'][@variant='{2}']".format(
                    id, subtype, variant
                )
            )

        ret["Name"] = en.get("name")
        ret["BaseHP"] = en.get("baseHP")
        ret["Boss"] = en.get("boss")
        ret["Champion"] = en.get("champion")

        atree = ET.parse(isaacResourceFolder + "gfx/" + en.get("anm2path"))
        aroot = atree.getroot()

        image = aroot.find(".Content/Spritesheets/Spritesheet[@Id='0']")
        frame = aroot.find(
            "./Animations[@DefaultAnimation]/Animation/LayerAnimations/LayerAnimation/Frame"
        )

        sourceImage = QImage()
        imgPath = os.path.normpath(
            os.path.join(
                isaacResourceFolder, "gfx/", image.get("Path").replace("\\", "/")
            )
        )
        sourceImage.load(imgPath, "Format_ARGB32")

        if sourceImage.isNull():
            print(id, subtype, variant, imgPath)

        cropRect = QRect(
            int(frame.get("XCrop")),
            int(frame.get("YCrop")),
            int(frame.get("Width")),
            int(frame.get("Height")),
        )

        pixmapImg = QImage(
            int(frame.get("Width")), int(frame.get("Height")), QImage.Format_ARGB32
        )
        RenderPainter = QPainter(pixmapImg)

        for layer in frame:
            cropRect = QRect(
                int(layer.get("XCrop")),
                int(layer.get("YCrop")),
                int(layer.get("Width")),
                int(layer.get("Height")),
            )
            RenderPainter.drawImage(0, 0, sourceImage.copy(cropRect))

        RenderPainter.end()
        ret["pixmap"] = QPixmap()
        ret["pixmap"].convertFromImage(sourceImage.copy(cropRect))

    except:
        print("Entity {0}:{1}:{2} not found.".format(id, subtype, variant))
        ret["Name"] = "Unknown"
        pass

    return ret


def openMap():
    global EntityOutput

    maps = [
        "00.special rooms.stb",
        "01.basement.stb",
        "02.cellar.stb",
        "04.caves.stb",
        "05.catacombs.stb",
        "07.depths.stb",
        "08.necropolis.stb",
        "10.womb.stb",
        "11.utero.stb",
        "13.blue womb.stb",
        "14.sheol.stb",
        "15.cathedral.stb",
        "16.dark room.stb",
        "17.chest.stb",
        "18.greed special.stb",
        "19.greed basement.stb",
        "20.greed caves.stb",
        "21.greed depths.stb",
        "22.greed womb.stb",
        "23.greed sheol.stb",
        "24.greed the shop.stb",
        "25.ultra greed.stb",
    ]

    f = "/Users/Chronometrics/Dropbox/Basement Renovator/Basement-Renovator/rooms/"

    entities = set()
    for path in maps:
        # Let's read the file and parse it into our list items
        stb = open(f + path, "rb").read()

        # Header
        header = struct.unpack_from("<4s", stb, 0)[0].decode()
        if header != "STB1":
            return

        off = 4

        # Room count
        rooms = struct.unpack_from("<I", stb, off)[0]
        off += 4
        ret = []

        for room in range(rooms):
            roomData = struct.unpack_from("<IIIBH", stb, off)
            off += 0xF

            roomName = struct.unpack_from("<{0}s".format(roomData[4]), stb, off)[
                0
            ].decode()
            off += roomData[4]

            entityTable = struct.unpack_from("<fBBBBH", stb, off)
            off += 0xA

            doors = []
            for door in range(entityTable[-2]):
                d = struct.unpack_from("<hh?", stb, off)
                doors.append([d[0], d[1], d[2]])
                off += 5

            for entity in range(entityTable[-1]):
                spawnLoc = struct.unpack_from("<hhB", stb, off)
                off += 5

                for spawn in range(spawnLoc[2]):
                    t = struct.unpack_from("<HHHf", stb, off)
                    entities.add((t[0], t[1], t[2], t[3]))
                    off += 0xA

    for eTmp in entities:
        e = {}
        e["ID"] = eTmp[0]
        e["Variant"] = eTmp[1]
        e["Subtype"] = eTmp[2]
        e["Weight"] = eTmp[3]

        tmp = entityRenoXML.find(
            "entity[@ID='{0}'][@Subtype='{1}'][@Variant='{2}']".format(
                e["ID"], e["Subtype"], e["Variant"]
            )
        )

        if tmp is None:
            di = getEntity(e["ID"], e["Subtype"], e["Variant"])

            e.update(di)
            e["Group"] = "Unknown"

            if "pixmap" in di:
                e["pixmap"].save(
                    "resources/NewEntities/{ID}.{Variant}.{Subtype} - {Name}.png".format(
                        **e
                    )
                )
                e[
                    "pixmap"
                ] = "resources/Entities/{ID}.{Variant}.{Subtype} - {Name}.png".format(
                    **e
                )
                EntityOutput.add(
                    (
                        e["ID"],
                        e["Name"],
                        e["Subtype"],
                        e["Variant"],
                        e["pixmap"],
                        e["Group"],
                        e["Boss"],
                        e["Champion"],
                        e["BaseHP"],
                    )
                )
            else:
                EntityOutput.add(
                    (e["ID"], e["Name"], e["Subtype"], e["Variant"], "", "Unknown")
                )


######

app = QApplication([])

EntityOutput = set()


# Renovator Entities
tree = ET.parse("Resources/Entities.xml")
entityRenoXML = tree.getroot()


# Isaac Entities
isaacResourceFolder = (
    "/Users/Chronometrics/Dropbox/Basement Renovator/Afterbirth Rooms/resources/"
)

tree = ET.parse(isaacResourceFolder + "entities2.xml")
entityXML = tree.getroot()
root = ET.Element("data")
ETout = ET.ElementTree(root)


openMap()

from operator import *

for e in sorted(EntityOutput, key=itemgetter(0, 3, 2)):
    new = ET.SubElement(root, "entity")
    new.set("ID", str(e[0]))
    new.set("Name", str(e[1]))
    new.set("Subtype", str(e[2]))
    new.set("Variant", str(e[3]))
    new.set("Image", e[4])
    new.set("Group", e[5])

    if len(e) > 6:
        new.set("Boss", e[6])
        new.set("Champion", e[7])
        new.set("BaseHP", e[8])


ETout.write("resources/NewEntities.xml")
