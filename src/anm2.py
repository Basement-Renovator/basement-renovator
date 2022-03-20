import os, re
import xml.etree.cElementTree as ET
from pathlib import Path

from PyQt5.QtCore import QRect, QPoint
from PyQt5.QtGui import QTransform, QImage, QPainter


class Config:
    def __init__(self, anmPath, resourcePath):
        self.path = Path(anmPath).resolve()
        self.resourcePath = resourcePath

        if not self.path.is_file():
            raise FileNotFoundError("Invalid anm2! " + self.path)

        self.dir, self.file = self.path.parent, self.path.name

        self.tree = ET.parse(self.path)
        self.spritesheets = list(
            map(
                lambda x: x.get("Path"),
                self.tree.findall(".Content/Spritesheets/Spritesheet"),
            )
        )
        self.layers = list(
            map(
                lambda x: int(x.get("SpritesheetId")),
                self.tree.findall(".Content/Layers/Layer"),
            )
        )

        self.animations = self.tree.findall("./Animations/Animation")
        self.defaultAnim = self.tree.find("Animations").get("DefaultAnimation")

        self.anim = None
        self.animLen = 0
        self.overlayAnim = None
        self.overlayLen = 0

        self.rootFrames = []
        self.frameLayers = []
        self.overlayRootFrames = []
        self.overlayFrameLayers = []

        self.frame = -1
        self.overlayFrame = -1

        self.useScaling = True

    def getAnim(self, name):
        if not name:
            return None
        return next((x for x in self.animations if x.get("Name") == name), None)

    def setAnimation(self, animName=None):
        self.anim = self.getAnim(animName or self.defaultAnim)
        if not self.anim:
            raise ValueError(f"Invalid animation! {animName or '[Default]'}")
        self.rootFrames = self.anim.findall(".//RootAnimation/Frame")
        self.frameLayers = self.anim.findall(".//LayerAnimation[Frame]")
        self.animLen = int(self.anim.get("FrameNum"))
        self.frame = 0

    def setOverlay(self, animName):
        self.overlayAnim = self.getAnim(animName)
        if not self.overlayAnim:
            raise ValueError(f"Invalid animation! {animName}")
        # not supported for now
        # self.overlayRootFrames = self.anim.findall(".//RootAnimation/Frame")
        self.overlayFrameLayers = self.overlayAnim.findall(".//LayerAnimation[Frame]")
        self.overlayLen = int(self.overlayAnim.get("FrameNum"))
        self.overlayFrame = 0

    @staticmethod
    def getFrameNode(frames, frameNumber):
        currFrame = 0
        for frame in frames:
            duration = int(frame.get("Delay"))
            if currFrame + duration > frameNumber:
                return frame

            currFrame += duration

        return frames[-1]

    def extractFrame(self, frameLayers, frameNumber):
        imgs = []
        ignoreCount = 0
        for layer in frameLayers:
            if layer.get("Visible") == "false":
                ignoreCount += 1
                continue

            frame = Config.getFrameNode(layer.findall("Frame"), frameNumber)
            if frame.get("Visible") == "false":
                ignoreCount += 1
                continue

            image = self.spritesheets[self.layers[int(layer.get("LayerId"))]] or ""

            imgPath = None
            sheetPath = None
            if isinstance(image, str):
                sheetPath = image
                image = os.path.abspath(os.path.join(self.dir, image))
                imgPath = Path(image)
                if not (imgPath and imgPath.exists()):
                    image = re.sub(r".*resources", self.resourcePath, image)
                    imgPath = Path(image)
                    image = str(imgPath) if imgPath.exists() else None

            if image is not None:
                # Here's the anm specs
                xp = -int(frame.get("XPivot"))  # applied before rotation
                yp = -int(frame.get("YPivot"))
                r = int(frame.get("Rotation"))
                x = int(frame.get("XPosition"))  # applied after rotation
                y = int(frame.get("YPosition"))
                xc = int(frame.get("XCrop"))
                yc = int(frame.get("YCrop"))
                xs = self.useScaling and float(frame.get("XScale")) / 100 or 1
                ys = self.useScaling and float(frame.get("YScale")) / 100 or 1
                w = int(frame.get("Width"))
                h = int(frame.get("Height"))

                imgs.append([image, x, y, xc, yc, w, h, xs, ys, r, xp, yp])
            else:
                print("Bad image! ", sheetPath, image)

        if not imgs:
            print(
                f'Frame could not be generated from animation due to {ignoreCount > 0 and "visibility" or "missing files"}'
            )

        return imgs

    def render(self, noScale=False):
        imgs = []

        root = Config.getFrameNode(self.rootFrames, self.frame)
        if root is not None and root.get("Visible") != "false":
            imgs += self.extractFrame(self.frameLayers, self.frame)

        if self.overlayAnim:
            imgs += self.extractFrame(self.overlayFrameLayers, self.overlayFrame)

        if not imgs:
            return None

        imgCache = {}

        # Fetch each layer and establish the needed dimensions for the final image
        finalRect = QRect()
        for img in imgs:
            image, x, y, xc, yc, w, h, xs, ys, r, xp, yp = img
            cropRect = QRect(xc, yc, w, h)

            mat = QTransform()
            mat.rotate(r)
            if not noScale:
                mat.scale(xs, ys)
            mat.translate(xp, yp)

            # Load the Image
            qimg = None
            if isinstance(image, str):
                qimg = imgCache.get(image)
                if qimg is None:
                    qimg = QImage(image)
                    imgCache[image] = qimg
                    # qimg.save(image)
            else:
                qimg = QImage(image)

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
        for (
            image,
            x,
            y,
            xc,
            yc,
            w,
            h,
            xs,
            ys,
            r,
            xp,
            yp,
            sourceImage,
            boundingRect,
        ) in imgs:
            # Transfer the crop area to the pixmap
            boundingRect.translate(-finalRect.topLeft())
            renderPainter.drawImage(boundingRect, sourceImage)
        renderPainter.end()

        if root is not None:
            mat = QTransform()
            mat.rotate(int(root.get("Rotation")))
            if not noScale:
                mat.scale(
                    float(root.get("XScale")) / 100, float(root.get("YScale")) / 100
                )
            mat.translate(int(root.get("XPosition")), int(root.get("YPosition")))

            pixmapImg = pixmapImg.transformed(mat)

        return pixmapImg
