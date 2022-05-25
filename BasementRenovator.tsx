//////////////////////////////////////////////////////////////////////////////////////
//
//    Binding of Isaac) { Rebirth Stage Editor
//         by Colin Noga
//            Chronometrics / Tempus
//
//         UI Elements
//             Main Scene: Click to select, right click to paint. Auto resizes to match window zoom. Renders background.
//             Entity: A QGraphicsItem to be added to the scene for (drawing.
//             Room List: Shows a list of rooms with mini-renders as icons. Needs add and remove buttons. Should drag and drop re-sort.
//             Entity Palette: A palette from which to choose entities to draw.
//             Properties: Possibly a contextual menu thing?
//
//   Afterbirth Todo:
//         Fix up Rebirth/Afterbirth detection
//
//     Low priority
//         Clear Corner Rooms Grid
//         Fix icon for (win_setup.py
//         Bosscolours for (the alternate boss entities
//

//import src.roomconvert as StageConvert
//from src.core import Room as RoomData, Entity as EntityData
//from src.lookup import EntityLookup, MainLookup
//import src.anm2 as anm2
//from src.constants import *
//from src.util import *

////////////////////////////////////////////////
//       XML Data       //
////////////////////////////////////////////////


/**
 * Returns the current compatibility mode, && the sub version if it exists
 */
function getGameVersion() {
    // default mode if not set
    return settings.value("CompatibilityMode", "Repentance");
}


let STEAM_PATH;
function getSteamPath() {
    if (STEAM_PATH === undefined) {
        STEAM_PATH = QSettings(
            "HKEY_CURRENT_USER\\Software\\Valve\\Steam", QSettings.NativeFormat
        ).value("SteamPath");
    }
    return STEAM_PATH;
}


function findInstallPath() {
    version = getGameVersion();
    if (version === "Antibirth" && settings.value("AntibirthPath")) {
        return settings.value("AntibirthPath");
    }

    installPath = "";
    cantFindPath = false;

    if (QFile.exists(settings.value("InstallFolder"))) {
        installPath = settings.value("InstallFolder");
    }
    else {
        // Windows path things
        if (platform.system().includes("Windows")) {
            basePath = getSteamPath();
            if (!basePath) {
                cantFindPath = true;
            }
            else {
                installPath = os.path.join(basePath, "steamapps", "common", "The Binding of Isaac Rebirth");
                if (!QFile.exists(installPath)) {
                    cantFindPath = true;

                    libconfig = os.path.join(basePath, "steamapps", "libraryfolders.vdf");
                    if (os.path.isfile(libconfig)) {
                        libLines = list(open(libconfig, "r"));
                        matcher = re.compile(/"\d+"\s*"(.*?)"/);
                        installDirs = libLines.map(line => matcher.search(line))
                            .filter(res => res)
                            .map(res => os.path.normpath(res.group(1)));

                        for (const root of installDirs) {
                            installPath = os.path.join(root, "steamapps", "common", "The Binding of Isaac Rebirth");
                            if (QFile.exists(installPath)) {
                                cantFindPath = false;
                                break;
                            }
                        }
                    }
                }
            }
        }
        // Mac Path things
        else if (platform.system().includes("Darwin")) {
            installPath = os.path.expanduser(
                "~/Library/Application Support/Steam/steamapps/common/The Binding of Isaac Rebirth/The Binding of Isaac Rebirth.app/Contents/Resources"
            );
            if (!QFile.exists(installPath)) {
                cantFindPath = true;
            }
        }
        // Linux and others
        else if (platform.system().includes("Linux")) {
            installPath = os.path.expanduser("~/.local/share/Steam/steamapps/common/The Binding of Isaac Rebirth");
            if (!QFile.exists(installPath)) {
                cantFindPath = true;
            }
        }
        else {
            cantFindPath = true;
        }

        // Looks like nothing was selected
        if (cantFindPath || installPath === "" || !os.path.isdir(installPath)) {
            printf(`Could not find The Binding of Isaac: ${version} install folder (${installPath})`);
            return "";
        }

        settings.setValue("InstallFolder", installPath);
    }

    return installPath;
}

function findModsPath(installPath=undefined) {
    modsPath = "";
    cantFindPath = false;

    if (QFile.exists(settings.value("ModsFolder"))) {
        modsPath = settings.value("ModsFolder");
    }
    else {
        installPath = installPath ?? findInstallPath();
        if (installPath?.length > 0) {
            modDirectory = os.path.join(installPath, "savedatapath.txt");
            if (os.path.isfile(modDirectory)) {
                lines = open(modDirectory, "r");
                modDir = lines.map(line => line.split(": ")).find(([ part ]) => part === "Modding Data Path");
                if (modDir) {
                    modsPath = os.path.normpath(modDir[1].strip());
                }
            }
        }
    }

    if (modsPath === "" || !os.path.isdir(modsPath)) {
        cantFindPath = true;
    }

    version = getGameVersion();

    if (!["Afterbirth+", "Repentance"].includes(version)) {
        printf(`INFO: ${version} does not support mod folders`);
        return "";
    }

    if (cantFindPath) {
        cantFindPath = false;
        // Windows path things
        if (platform.system().includes("Windows")) {
            modsPath = os.path.join(os.path.expanduser("~"), "Documents", "My Games", `Binding of Isaac ${version} Mods`);
            if (!QFile.exists(modsPath)) {
                cantFindPath = true;
            }
        }
        // Mac Path things
        else if (platform.system().includes("Darwin")) {
            modsPath = os.path.expanduser(`~/Library/Application Support/Binding of Isaac ${version} Mods`);
            if (!QFile.exists(modsPath)) {
                cantFindPath = true;
            }
        }
        // Linux and others
        else {
            modsPath = os.path.expanduser(`~/.local/share/binding of isaac ${version.lowerCase()} mods/`);
            if (!QFile.exists(modsPath)) {
                cantFindPath = true;
            }
        }

        // Fallback Resource Folder Locating
        if (cantFindPath) {
            modsPathOut = QFileDialog.getExistingDirectory(
                undefined, `Please Locate The Binding of Isaac: ${version} Mods Folder`
            );
            if (!modsPathOut) {
                QMessageBox.warning(
                    undefined,
                    "Error",
                    "Couldn't locate Mods folder and no folder was selected.",
                );
                return;
            }
            else {
                modsPath = modsPathOut;
            }
            if (modsPath === "") {
                QMessageBox.warning(
                    undefined,
                    "Error",
                    "Couldn't locate Mods folder and no folder was selected.",
                );
                return;
            }
            if (!QDir(modsPath).exists) {
                QMessageBox.warning(
                    undefined, "Error", "Selected folder does !exist or !== a folder."
                );
                return;
            }
        }

        // Looks like nothing was selected
        if (modsPath === "" || !os.path.isdir(modsPath)) {
            QMessageBox.warning(
                undefined,
                "Error",
                `Could !find The Binding of Isaac) { {version} Mods folder ({modsPath})`,
            );
            return "";
        }

        settings.setValue("ModsFolder", modsPath);
    }

    return modsPath;
}

let xmlLookups;
function loadMods(autogenerate, installPath, resourcePath) {
    // Each mod of the mod folder is a Group
    modsPath = findModsPath(installPath);
    if (!os.path.isdir(modsPath)) {
        printf("Could !find Mods Folder! Skipping mod content!");
        return;
    }

    modsInstalled = os.listdir(modsPath);

    autogenPath = "resources/Entities/ModTemp";
    if (autogenerate && !os.path.exists(autogenPath)) {
        os.mkdir(autogenPath);
    }

    printSectionBreak();
    printf("LOADING MOD CONTENT");
    for (const mod of modsInstalled) {
        modPath = os.path.join(modsPath, mod);
        brPath = os.path.join(modPath, "basementrenovator");

        // Make sure we're a mod
        if (!os.path.isdir(modPath) || os.path.isfile(os.path.join(modPath, "disable.it"))) {
            continue;
        }

        // simple workaround for now
        if (!(autogenerate || os.path.exists(brPath))) {
            continue;
        }

        // Get the mod name
        modName = mod;
        try {
            tree = ET.parse(os.path.join(modPath, "metadata.xml"));
            root = tree.getroot();
            modName = root.find("name").text;
        }
        catch (e) {
            printf(`Failed to parse mod metadata "${modName}", falling back on default name`);
        }

        xmlLookups.loadFromMod(modPath, brPath, modName, autogenerate);


////////////////////////////////////////////////
//      Scene/View      //
////////////////////////////////////////////////


class RoomScene extends QGraphicsScene {
    constructor(parent) {
        super(0, 0, 0, 0);
        this.newRoomSize(1);

        // Make the bitfont
        q = QImage();
        q.load("resources/UI/Bitfont.png");

        this.bitfont = [
            QPixmap.fromImage(q.copy(i * 12, j * 12, 12, 12))
            for j of range(int(q.height() / 12))
            for i of range(int(q.width() / 12))
        ];
        this.bitText = true;

        this.roomDoorRoot = undefined;
        this.clearDoors();

        this.bgState = [];
        this.framecache = {};

        this.floorAnim = anm2.Config("resources/Backgrounds/FloorBackdrop.anm2", "resources");
        this.floorImg = undefined;
        this.wallAnim = anm2.Config("resources/Backgrounds/WallBackdrop.anm2", "resources");
        this.wallImg = undefined;
    }

    newRoomSize(shape) {
        this.roomInfo = Room.Info(shape=shape);
        if (!this.roomInfo.shapeData) {
            return;
        }

        this.roomWidth, this.roomHeight = this.roomInfo.dims;
        this.entCache = [[] for i of range(this.roomWidth * this.roomHeight)];

        this.roomRows = [QGraphicsWidget() for i of range(this.roomHeight)];
        for (const row of Object.values(this.roomRows)) {
            this.addItem(row);
        }

        this.setSceneRect(-1 * 26, -1 * 26, (this.roomWidth + 2) * 26, (this.roomHeight + 2) * 26);
    }

    updateRoomDepth(room) {
        if (room.roomBG.get("InvertDepth") !== "1") {
            for (const [ i, row ] of Object.entries(this.roomRows)) {
                row.setZValue(i);
            }
        }
        else {
            last = this.roomRows.length - 1;
            for (const [ i, row ] of Object.entries(this.roomRows)) {
                row.setZValue(last - i);
            }
        }
    }

    getAdjacentEnts(x, y, useCache=false) {
        width, height = this.roomWidth, this.roomHeight;

        // [ L, R, U, D, UL, DL, UR, DR ]
        lookup = {
            [-1]: [4, 2, 6],
            [0]:  [0, undefined, 1],
            [1]:  [5, 3, 7],
        };

        res = Array.from(range(8)).map(() => []);
        if (useCache) {
            for (const i of range(-1, 2)) {
                for (const j of range(-1, 2)) {
                    spot = lookup[i][j + 1];
                    if (spot !== undefined) {
                        idx = Room.Info.gridIndex(x + j, y + i, width);
                        if (idx < 0 || idx >= width * height)
                            continue;
                        res[spot] = this.entCache[idx];
                    }
                }
            }
            return res;
        }

        for (const yc of [y - 1, y, y + 1]) {
            if (yc < 0 || yc >= height)
                continue;

            for (const item of this.roomRows[yc].childItems()) {
                xc = item.entity.x;
                i = (xc - x) + 1;
                if (i > -1 && i < 3) {
                    spots = lookup[yc - y];
                    if (spots[i] !== undefined) {
                        res[spots[i]].push(item);
                    }
                }
            }
        }

        return res;
    }

    getFrame(key, anm2) {
        cache = this.framecache.get(key);
        if (!cache) {
            cache = {}
            this.framecache[key] = cache;
        }

        frame = cache.get(anm2.frame);
        if (frame === undefined) {
            frame = anm2.render();
            cache[anm2.frame] = frame;
        }

        return frame;
    }

    clearDoors() {
        if (this.roomDoorRoot) {
            // wrap if (the underlying object is deleted
            try {
                this.roomDoorRoot.remove();
            }
            catch {}
        }

        this.roomDoorRoot = QGraphicsWidget();
        this.roomDoorRoot.setZValue(-1000)  // make sure doors display under entities
        this.addItem(this.roomDoorRoot);
    }

    drawForeground(painter, rect) {
        // Bitfont drawing moved to the RoomEditorWidget.drawForeground for easier anti-aliasing

        // Grey out the screen to show it's inactive if there are no rooms selected
        if (mainWindow.roomList.selectedRoom() === undefined) {
            b = QBrush(QColor(255, 255, 255, 100));
            painter.setPen(Qt.white);
            painter.setBrush(b);

            painter.fillRect(rect, b);
            return;
        }
        if (settings.value("GridEnabled") === "0") {
            return;
        }

        gs = 26;

        painter.setRenderHint(QPainter.Antialiasing, true);
        painter.setRenderHint(QPainter.SmoothPixmapTransform, true);

        white = QColor.fromRgb(255, 255, 255, 100);
        bad = QColor.fromRgb(100, 255, 255, 100);

        showOutOfBounds = settings.value("BoundsGridEnabled") === "1";
        showGridIndex = settings.value("ShowGridIndex") === "1";
        showCoordinates = settings.value("ShowCoordinates") === "1";
        for (const y of range(this.roomHeight)) {
            for (const x of range(this.roomWidth)) {
                if (this.roomInfo.isInBounds(x, y)) {
                    painter.setPen(QPen(white, 1, Qt.DashLine));
                }
                else {
                    if (!showOutOfBounds) {
                        continue;
                    }
                    painter.setPen(QPen(bad, 1, Qt.DashLine));
                }

                painter.drawLine(x * gs, y * gs, (x + 1) * gs, y * gs);
                painter.drawLine(x * gs, (y + 1) * gs, (x + 1) * gs, (y + 1) * gs);
                painter.drawLine(x * gs, y * gs, x * gs, (y + 1) * gs);
                painter.drawLine((x + 1) * gs, y * gs, (x + 1) * gs, (y + 1) * gs);

                if (showGridIndex) {
                    painter.drawText(
                        x * gs + 2,
                        y * gs + 13,
                        Room.Info.gridIndex(x, y, this.roomWidth) + '',
                    );
                }
                if (showCoordinates) {
                    painter.drawText(x * gs + 2, y * gs + 24, `${x - 1},${y - 1}`);
                }
            }
        }

        // Draw Walls (Debug)
        // painter.setPen(QPen(Qt.green, 5, Qt.SolidLine))
        // h = gs / 2
        // walls = this.roomInfo.shapeData['Walls']
        // for (const [ wMin, wMax, wLvl, wDir ] of walls.X)
        //     painter.drawLine(wMin * gs + h, wLvl * gs + h, wMax * gs + h, wLvl * gs + h);
        // for (const [ wMin, wMax, wLvl, wDir ] of walls.Y)
        //     painter.drawLine(wLvl * gs + h, wMin * gs + h, wLvl * gs + h, wMax * gs + h);

        QGraphicsScene.drawForeground(this, painter, rect);
    }

    loadBackground() {
        roomBG = undefined;
        currentRoom = mainWindow.roomList.selectedRoom();
        if (currentRoom) {
            roomBG = currentRoom.roomBG;
            roomShape = currentRoom.info.shape;
        }
        else {
            roomShape = 1;
        }

        bgState = [roomBG, roomShape];
        if (bgState === this.bgState[:1]) {
            return;
        }

        this.bgState = bgState;

        gfxData = xmlLookups.getGfxData(roomBG);
        this.bgState.push(gfxData);

        roomBG = gfxData["Paths"];

        mainBG = roomBG.get("OuterBG") ?? "resources/none.png";
        overrideBG = roomBG.get("BigOuterBG");

        if (roomShape !== 1 && overrideBG) {
            this.floorAnim.spritesheets[0] = overrideBG;
        }
        else {
            this.floorAnim.spritesheets[0] = mainBG;
        }

        this.floorAnim.spritesheets[1] = roomBG.get("LFloor") ?? "resources/none.png";
        this.floorAnim.spritesheets[2] = roomBG.get("NFloor") ?? "resources/none.png";

        this.wallAnim.spritesheets[0] = mainBG;
        this.wallAnim.spritesheets[1] = roomBG.get("InnerBG") ?? "resources/none.png";

        this.floorAnim.setAnimation(str(roomShape));
        this.wallAnim.setAnimation(str(roomShape));

        this.floorImg = this.floorAnim.render();
        this.wallImg = this.wallAnim.render();

        this.roomShape = roomShape;
    }

    getBGGfxData() {
        return this.bgState?.[2];
    }

    drawBackground(painter, rect) {
        this.loadBackground();

        xOff, yOff = 0, 0;
        shapeData = RoomData.Shapes[this.roomShape];
        if (shapeData.get("TopLeft")) {
            xOff, yOff = RoomData.Info.coords(
                shapeData["TopLeft"], shapeData["Dims"][0]
            );
        }

        gs = 26;
        painter.drawImage((1 + xOff) * gs, (1 + yOff) * gs, this.floorImg);
        painter.drawImage((-1 + xOff) * gs, (-1 + yOff) * gs, this.wallImg);

        for (const stack of this.entCache) {
            stack.clear();
        }

        for (const item of this.items()) {
            if (item instanceof Entity) {
                xc = item.entity.x;
                yc = item.entity.y;
                this.entCache[Room.Info.gridIndex(xc, yc, this.roomWidth)].push(item);
            }
        }

        // have to set rock tiling ahead of time due to render order not being guaranteed left to right
        room = mainWindow.roomList.selectedRoom();
        if (room) {
            seed = room.seed;
            for (const [ i, stack ] of Object.entries(this.entCache)) {
                for (const ent of stack) {
                    if (ent.entity.config.renderRock && ent.entity.rockFrame === undefined) {
                        ent.setRockFrame(seed + i);
                    }
                }
            }
        }

        QGraphicsScene.drawBackground(this, painter, rect);
    }
}

class RoomEditorWidget extends QGraphicsView {
    constructor(scene, parent=undefined) {
        super(parent);

        this.setViewportUpdateMode(QGraphicsView.FullViewportUpdate);
        this.setDragMode(QGraphicsView.RubberBandDrag);
        this.setTransformationAnchor(QGraphicsView.AnchorViewCenter);
        this.setAlignment(Qt.AlignTop | Qt.AlignLeft);
        this.setAcceptDrops(true);

        this.assignNewScene(scene);

        this.canDelete = true;
    }

    dragEnterEvent(evt) {
        if (evt.mimeData().hasFormat("text/uri-list")) {
            evt.setAccepted(true);
            this.update();
        }
    }

    dropEvent(evt) {
        if (evt.mimeData().hasFormat("text/uri-list")) {
            mainWindow.dropEvent(evt);
        }
    }

    assignNewScene(scene) {
        this.setScene(scene);
        this.centerOn(0, 0);

        this.objectToPaint = undefined;
        this.lastTile = undefined;
    }


    /**
     * Called when a paint attempt is initiated
     */
    tryToPaint(event) {
        paint = this.objectToPaint;
        if (paint === undefined) {
            return;
        }

        clicked = this.mapToScene(event.x(), event.y());
        x, y = clicked.x(), clicked.y();

        x = (x / 26) | 0;
        y = (y / 26) | 0;

        xMax, yMax = this.scene().roomWidth, this.scene().roomHeight;

        x = Math.min(Math.max(x, 0), xMax - 1);
        y = Math.min(Math.max(y, 0), yMax - 1);

        if (settings.value("SnapToBounds") === "1") {
            [ x, y ] = this.scene().roomInfo.snapToBounds(x, y);
        }

        for (const i of this.scene().items()) {
            if (i instanceof Entity) {
                if (i.entity.x === x && i.entity.y === y) {
                    if (i.stackDepth === EntityStack.MAX_STACK_DEPTH) {
                        return;
                    }

                    i.hideWeightPopup();

                    // Don't stack multiple grid entities
                    if (i.entity.Type > 999 && this.objectToPaint.ID > 999) {
                        return;
                    }
                }
            }
        }

        // Make sure we're not spawning oodles
        if (this.lastTile.has((x, y))) {
            return;
        }
        this.lastTile.add((x, y));

        selection = this.scene().selectedItems();
        paintID, paintVariant, paintSubtype = paint.ID, paint.variant, paint.subtype;
        if (paint.config.hasBitfields && selection.length === 1) {
            selectedEntity = selection[0];
            if (selectedEntity.entity.config === paint.config) {
                paintID = selectedEntity.entity.Type;
                paintVariant = selectedEntity.entity.Variant;
                paintSubtype = selectedEntity.entity.Subtype;
            }
        }

        en = Entity(x, y, int(paintID), int(paintVariant), int(paintSubtype), 1.0);
        if (en.entity.config.hasTag("Grid")) {
            en.updateCoords(x, y, depth=0);
        }

        mainWindow.dirt();
    }

    mousePressEvent(event) {
        if (event.buttons() === Qt.RightButton) {
            if (mainWindow.roomList.selectedRoom() !== undefined) {
                this.lastTile = new Set();
                this.tryToPaint(event);
                event.accept();
            }
        }
        else {
            this.lastTile = undefined;
        }
        // not calling this for right click + adding items to the scene causes crashes
        QGraphicsView.mousePressEvent(this, event);
    }

    mouseMoveEvent(event) {
        if (this.lastTile) {
            if (mainWindow.roomList.selectedRoom() !== undefined) {
                this.tryToPaint(event);
                event.accept();
            }
        }
        QGraphicsView.mouseMoveEvent(this, event);
    }

    mouseReleaseEvent(event) {
        this.lastTile = undefined;
        QGraphicsView.mouseReleaseEvent(this, event);
    }

    keyPressEvent(event) {
        if (this.canDelete && event.key() === Qt.Key_Delete) {
            scene = this.scene();
            selection = scene.selectedItems();

            if (selection.length > 0) {
                for (const obj of selection) {
                    obj.setSelected(false);
                    obj.remove();
                }
                scene.update();
                this.update();
                mainWindow.dirt();
            }
        }

        QGraphicsView.keyPressEvent(this, event);
    }

    drawBackground(painter, rect) {
        painter.fillRect(rect, QColor(0, 0, 0));

        QGraphicsView.drawBackground(this, painter, rect);
    }

    resizeEvent(event) {
        QGraphicsView.resizeEvent(this, event);

        w = this.scene().roomWidth;
        h = this.scene().roomHeight;

        xScale = (event.size().width() - 2) / (26 * (w + 2));
        yScale = (event.size().height() - 2) / (26 * (h + 2));
        newScale = min([xScale, yScale]);

        tr = QTransform();
        tr.scale(newScale, newScale);

        this.setTransform(tr);

        if (newScale === yScale) {
            this.setAlignment(Qt.AlignTop | Qt.AlignHCenter);
        }
        else {
            this.setAlignment(Qt.AlignVCenter | Qt.AlignLeft);
        }
    }

    paintEvent(event) {
        // Purely handles the status overlay text
        QGraphicsView.paintEvent(this, event);

        if (settings.value("StatusEnabled") === "0") {
            return;
        }

        // Display the room status of a text overlay
        painter = QPainter();
        painter.begin(this.viewport());

        painter.setRenderHint(QPainter.Antialiasing, true);
        painter.setRenderHint(QPainter.SmoothPixmapTransform, true);
        painter.setPen(QPen(Qt.white, 1, Qt.SolidLine));

        room = mainWindow.roomList.selectedRoom();
        if (room) {
            // Room Type Icon
            roomTypes = xmlLookups.roomTypes.lookup(room=room, showInMenu=true);
            if (roomTypes.length > 0) {
                q = QPixmap(roomTypes[0].get("Icon"));
                painter.drawPixmap(2, 3, q);
            }
            else {
                printf("Warning: Unknown room type during paintEvent:", room.getDesc());
            }

            // Top Text
            font = painter.font();
            font.setPixelSize(13);
            painter.setFont(font);
            painter.drawText(20, 16, `${room.info.variant} - ${room.name}`);

            // Bottom Text
            font = painter.font();
            font.setPixelSize(10);
            painter.setFont(font);
            painter.drawText(
                8,
                30,
                `Type: ${room.info.type}, Variant: ${room.info.variant}, Subtype: ${room.info.subtype}, Difficulty: ${room.difficulty}, Weight: ${room.weight}`,
            );
        }

        // Display the currently selected entity of a text overlay
        selectedEntities = this.scene().selectedItems();

        if (selectedEntities.length === 1) {
            e = selectedEntities[0];
            r = event.rect();

            // Entity Icon
            painter.drawPixmap(QRect(r.right() - 32, 2, 32, 32), e.entity.iconpixmap);

            // Top Text
            font = painter.font();
            font.setPixelSize(13);
            painter.setFont(font);
            painter.drawText(
                r.right() - 34 - 400,
                2,
                400,
                16,
                int(Qt.AlignRight | Qt.AlignBottom),
                `${e.entity.Type}.${e.entity.Variant}.${e.entity.Subtype} - ${e.entity.config.name}`,
            );

            // Bottom Text
            font = painter.font();
            font.setPixelSize(10);
            painter.setFont(font);
            textY = 20;
            tags = e.entity.config.tagsString;
            if (tags !== "[]") {
                painter.drawText(
                    r.right() - 34 - 400,
                    textY,
                    400,
                    12,
                    int(Qt.AlignRight | Qt.AlignBottom),
                    "Tags : " + tags,
                );
                textY += 16;
            }

            painter.drawText(
                r.right() - 34 - 200,
                textY,
                200,
                12,
                int(Qt.AlignRight | Qt.AlignBottom),
                `Base HP : ${e.entity.config.baseHP}`,
            );
        }
        else if (selectedEntities.length > 1) {
            e = selectedEntities[0];
            r = event.rect();

            // Case Two) { more than one type of entity
            // Entity Icon
            painter.drawPixmap(QRect(r.right() - 32, 2, 32, 32), e.entity.pixmap);

            // Top Text
            font = painter.font();
            font.setPixelSize(13);
            painter.setFont(font);
            painter.drawText(
                r.right() - 34 - 200,
                2,
                200,
                16,
                int(Qt.AlignRight | Qt.AlignBottom),
                `${selectedEntities.length} Entities Selected`,
            );

            // Bottom Text
            font = painter.font();
            font.setPixelSize(10);
            painter.setFont(font);
            painter.drawText(
                r.right() - 34 - 200,
                20,
                200,
                12,
                Qt.AlignRight | Qt.AlignBottom,
                Array.from(new Set(selectedEntities.map(x => x.entity.config.name ?? "INVALID"))).join(', '),
            );
        }

        painter.end();
    }

    drawForeground(painter, rect) {
        QGraphicsView.drawForeground(this, painter, rect);

        painter.setRenderHint(QPainter.Antialiasing, true);
        painter.setRenderHint(QPainter.SmoothPixmapTransform, true);

        // Display the number of entities on a given tile, of bitFont || regular font
        tiles = [
            [0 for x of range(this.scene().roomWidth)]
            for y of range(this.scene().roomHeight)
        ];
        for (const e of this.scene().items()) {
            if (e instanceof Entity) {
                tiles[e.entity.y][e.entity.x]++;
            }
        }

        useAliased = settings.value("BitfontEnabled") === "0";

        if (useAliased) {
            painter.setPen(Qt.white);
            painter.font().setPixelSize(5);
        }

        for (const [ y, row ] of Object.entries(tiles)) {
            yc = (y + 1) * 26 - 12;

            for (const [ x, count ] of Object.entries(row)) {
                if (count <= 1) continue;

                if (!useAliased) {
                    xc = (x + 1) * 26 - 12;

                    digits = count.toString().split().map(d => +d);

                    fontrow = count === EntityStack.MAX_STACK_DEPTH ? 1 : 0;

                    numDigits = digits.length - 1;
                    for (const [ i, digit ] of Object.entries(digits)) {
                        painter.drawPixmap(
                            xc - 12 * (numDigits - i),
                            yc,
                            this.scene().bitfont[digit + fontrow * 10],
                        );
                    }
                }
                else {
                    if (count === EntityStack.MAX_STACK_DEPTH) {
                        painter.setPen(Qt.red);
                    }

                    painter.drawText(
                        x * 26,
                        y * 26,
                        26,
                        26,
                        int(Qt.AlignBottom | Qt.AlignRight),
                        count.toString(),
                    );

                    if (count === EntityStack.MAX_STACK_DEPTH) {
                        painter.setPen(Qt.white);
                    }
                }
            }
        }
    }

}

class Entity extends QGraphicsItem {
    static GRID_SIZE = 26;

    class Info {
        constructor(x=0, y=0, t=0, v=0, s=0, weight=0, changeAtStart=true) {
            // Supplied entity info
            this.x = x;
            this.y = y;
            this.weight = weight;

            if (changeAtStart) {
                this.changeTo(t, v, s);
            }
        }

        changeTo(t, v, s) {
            this.Type = t;
            this.Variant = v;
            this.Subtype = s;

            // Derived Entity Info
            this.config = undefined;
            this.rockFrame = undefined;
            this.placeVisual = undefined;
            this.imgPath = undefined;
            this.pixmap = undefined;
            this.iconpixmap = undefined;
            this.overlaypixmap = undefined;
            this.known = false;

            this.getEntityInfo(t, v, s);
        }

        getEntityInfo(entitytype, variant, subtype) {
            this.config = xmlLookups.entities.lookupOne(entitytype, variant, subtype);
            if (this.config === undefined) {
                printf(`'Could not find Entity ${entitytype}.${variant}.${subtype} for in-editor, using ?`);

                this.pixmap = QPixmap("resources/Entities/questionmark.png");
                this.iconpixmap = this.pixmap;
                this.config = xmlLookups.entities.EntityConfig();
                return;
            }

            if (this.config.hasBitfields) {
                for (const bitfield of this.config.bitfields) {
                    this.validateBitfield(bitfield);
                }
            }

            this.rockFrame = undefined;
            this.imgPath = this.config.editorImagePath ?? this.config.imagePath;

            if (entitytype === EntityType.PICKUP && variant === PickupVariant.COLLECTIBLE) {
                i = QImage();
                i.load("resources/Entities/5.100.0 - Collectible.png");
                i = i.convertToFormat(QImage.Format_ARGB32);

                d = QImage();
                d.load(this.imgPath);

                p = QPainter(i);
                p.drawImage(0, 0, d);
                p.end();

                this.pixmap = QPixmap.fromImage(i);
            }
            else {
                this.pixmap = QPixmap(this.imgPath);
            }

            if (this.imgPath !== this.config.imagePath) {
                this.iconpixmap = QPixmap(this.config.imagePath);
            }
            else {
                this.iconpixmap = this.pixmap;
            }

            if (this.config.placeVisual) {
                parts = this.config.placeVisual.split(",").map(x => x.strip());
                if (parts.length === 2 && checkFloat(parts[0]) && checkFloat(parts[1])) {
                    this.placeVisual = (parseFloat(parts[0]), parseFloat(parts[1]));
                }
                else {
                    this.placeVisual = parts[0];
                }
            }

            if (this.config.overlayImagePath) {
                this.overlaypixmap = QPixmap(this.config.overlayImagePath);
            }

            this.known = true;
        }

        validateBitfield(bitfield) {
            value = this.getBitfieldValue(bitfield);
            if (typeof value !== "number") {
                printf(
                    `Entity ${this.config.name} (${this.config.type}.${this.config.variant}.${this.config.subtype}) has an invalid bitfield Key ${bitfield.key}`
                );
                this.config.invalidBitfield = true;
            }
            else {
                value = bitfield.clampValues(value);
                this[bitfield.key] = value;
            }
        }

        getBitfieldValue(bitfield) {
            return this[bitfield.key];
        }

        setBitfieldElementValue(bitfieldElement, value) {
            this[bitfieldElement.bitfield.key] = bitfieldElement.setRawValue(
                this.getBitfieldValue(bitfieldElement.bitfield), +value
            );
        }
    }

    constructor(x, y, myType, variant, subtype, weight, respawning=false) {
        super();

        // used when the ent is coming in from a previous state and should not update permanent things,
        // e.g. door enablement
        this.respawning = respawning;

        this.setFlags(
            this.ItemSendsGeometryChanges | this.ItemIsSelectable | this.ItemIsMovable
        );

        this.stackDepth = 1;
        this.popup = undefined;
        mainWindow.scene.selectionChanged.connect(this.hideWeightPopup);

        this.entity = new Entity.Info(x, y, myType, variant, subtype, weight);
        this.updateCoords(x, y);
        this.updateTooltip();

        this.updatePosition();

        if (!Entity.SELECTION_PEN) {
            Entity.SELECTION_PEN = QPen(Qt.green, 1, Qt.DashLine);
            Entity.OFFSET_SELECTION_PEN = QPen(Qt.red, 1, Qt.DashLine);
            Entity.INVALID_ERROR_IMG = QPixmap("resources/UI/ent-error.png");
            Entity.OUT_OF_RANGE_WARNING_IMG = QPixmap("resources/UI/ent-warning.png");
        }

        this.setAcceptHoverEvents(true);

        this.respawning = false;
    }

    setData(t, v, s) {
        this.entity.changeTo(t, v, s);
        this.updateTooltip();
    }

    updateTooltip() {
        e = this.entity;
        tooltipStr = "";
        if (e.known) {
            tooltipStr = `${e.config.name} @ ${e.x-1} x ${e.y-1} - ${e.Type}.${e.Variant}.${e.Subtype}; HP: ${e.config.baseHP}`;
            tooltipStr += e.config.getEditorWarnings();
        }
        else {
            tooltipStr = `Missing @ ${e.x-1} x ${e.y-1} - ${e.Type}.${e.Variant}.${e.Subtype}`;
            tooltipStr += "\nMissing BR entry! Trying to spawn this entity might CRASH THE GAME!!";
        }

        this.setToolTip(tooltipStr);
    }

    updateCoords(x, y, depth=-1) {
        scene = mainWindow.scene;

        function entsInCoord(x, y) {
            return scene.roomRows[y].childItems().filter(e => e.entity.x === x && e !== this);
        }

        adding = this.parentItem() === undefined;
        if (adding) {
            this.setParentItem(scene.roomRows[y]);

            if (this.entity.config.gfx !== undefined) {
                currentRoom = mainWindow.roomList.selectedRoom();
                currentRoom?.setRoomBG(this.entity.config.gfx);
            }

            this.updateBlockedDoor(false, countOnly=this.respawning);
            return;
        }

        z = this.zValue();
        moving = this.entity.x !== x || this.entity.y !== y;

        if ((depth < 0 && moving) || depth !== z) {
            topOfStack = false;
            if (depth < 0) {
                depth = entsInCoord(x, y).length;
                topOfStack = true;
            }

            if (!topOfStack) {
                for (const entity of entsInCoord(x, y)) {
                    z2 = entity.zValue();
                    if (z2 >= depth) {
                        entity.setZValue(z2 + 1);
                    }
                }
            }

            if (moving) {
                for (const entity of entsInCoord(this.entity.x, this.entity.y)) {
                    z2 = entity.zValue();
                    if (z2 > z) {
                        entity.setZValue(z2 - 1);
                    }
                }
            }

            this.setParentItem(scene.roomRows[y]);
            this.setZValue(depth);
        }

        if (moving) {
            this.updateBlockedDoor(true);
        }

        this.entity.x = x;
        this.entity.y = y;

        if (moving) {
            this.updateBlockedDoor(false);
        }
    }

    updateBlockedDoor(val, countOnly=false) {
        if (!this.entity.config.hasTag("NoBlockDoors")) {
            blockedDoor = this.scene().roomInfo.inFrontOfDoor(
                this.entity.x, this.entity.y
            );
            if (blockedDoor) {
                for (const door of this.scene().roomDoorRoot.childItems()) {
                    if (door.doorItem[:2] === blockedDoor[:2]) {
                        doorFollowsBlockRule = (door.blockingCount === 0) === door.exists;
                        door.blockingCount += val ? -1 : 1;
                        if (doorFollowsBlockRule && door.exists && !countOnly) {
                            // if (the door was already following the blocking rules
                            // AND it was open (do !open closed doors) then close it
                            door.exists = door.blockingCount === 0;
                        }
                        break;
                    }
                }
            }
        }
    }

    static PitAnm2;
    static {
        PitAnm2 = anm2.Config("resources/Backgrounds/PitGrid.anm2", "resources");
        PitAnm2.setAnimation();
    }

    static RockAnm2;
    static {
        RockAnm2 = anm2.Config("resources/Backgrounds/RockGrid.anm2", "resources");
        RockAnm2.setAnimation();
    }

    getPitFrame(pitImg, rendered) {
        function matchInStack(stack) {
            for (const ent of stack) {
                img = ent.getCurrentImg();
                if (img === pitImg) {
                    return true;
                }
            }

            return false;
        }

        adjEnts = this.scene().getAdjacentEnts(
            this.entity.x, this.entity.y, useCache=true
        );

        [L, R, U, D, UL, DL, UR, DR] = adjEnts.map(matchInStack);
        hasExtraFrames = rendered.height() > 260;

        // copied from stageapi
        // Words were shortened to make writing code simpler.
        F = 0  // Sprite frame to set

        // First bitwise frames (works for all combinations of just left up right and down)
        if (L) {
            F = F | 1;
        }
        if (U) {
            F = F | 2;
        }
        if (R) {
            F = F | 4;
        }
        if (D) {
            F = F | 8;
        }

        // Then a bunch of other combinations
        if (U && L && !UL && !R && !D) {
            F = 17;
        }
        if (U && R && !UR && !L && !D) {
            F = 18;
        }
        if (L && D && !DL && !U && !R) {
            F = 19;
        }
        if (R && D && !DR && !L && !U) {
            F = 20;
        }
        if (L && U && R && D && !UL) {
            F = 21;
        }
        if (L && U && R && D && !UR) {
            F = 22;
        }
        if (U && R && D && !L && !UR) {
            F = 25;
        }
        if (L && U && D && !R && !UL) {
            F = 26;
        }
        if (hasExtraFrames) {
            if (U && L && D && UL && !DL) {
                F = 35;
            }
            if (U && R && D && UR && !DR) {
                F = 36;
            }
        }

        if (L && U && R && D && !DL && !DR) {
            F = 24;
        }
        if (L && U && R && D && !UR && !UL) {
            F = 23;
        }
        if (L && U && R && UL && !UR && !D) {
            F = 27;
        }
        if (L && U && R && UR && !UL && !D) {
            F = 28;
        }
        if (L && U && R && !D && !UR && !UL) {
            F = 29;
        }
        if (L && R && D && DL && !U && !DR) {
            F = 30;
        }
        if (L && R && D && DR && !U && !DL) {
            F = 31;
        }
        if (L && R && D && !U && !DL && !DR) {
            F = 32;
        }

        if (hasExtraFrames) {
            if (U && R && D && !L && !UR && !DR) {
                F = 33;
            }
            if (U && L && D && !R && !UL && !DL) {
                F = 34;
            }
            if (U && R && D && L && UL && UR && DL && !DR) {
                F = 37;
            }
            if (U && R && D && L && UL && UR && DR && !DL) {
                F = 38;
            }
            if (U && R && D && L && !UL && !UR && !DR && !DL) {
                F = 39;
            }
            if (U && R && D && L && DL && DR && !UL && !UR) {
                F = 40;
            }
            if (U && R && D && L && DL && UR && !UL && !DR) {
                F = 41;
            }
            if (U && R && D && L && UL && DR && !DL && !UR) {
                F = 42;
            }
            if (U && R && D && L && UL && !DL && !UR && !DR) {
                F = 43;
            }
            if (U && R && D && L && UR && !UL && !DL && !DR) {
                F = 44;
            }
            if (U && R && D && L && DL && !UL && !UR && !DR) {
                F = 45;
            }
            if (U && R && D && L && DR && !UL && !UR && !DL) {
                F = 46;
            }
            if (U && R && D && L && DL && DR && !UL && !UR) {
                F = 47;
            }
            if (U && R && D && L && DL && UL && !UR && !DR) {
                F = 48;
            }
            if (U && R && D && L && DR && UR && !UL && !DL) {
                F = 49;
            }
        }

        return F;
    }

    setRockFrame(seed) {
        Math.randomseed(seed);
        this.entity.rockFrame = (Math.random() * 3) | 0;
        this.entity.placeVisual = (0, 3 / 26);

        if (seed & 3 !== 0) {
            return;
        }

        rockImg = this.getCurrentImg();

        function findMatchInStack(stack) {
            for (ent of stack) {
                img = ent.getCurrentImg();

                if (img === rockImg) {
                    return ent;
                }
            }
            return undefined;
        }

        const [_, right, _, down, _, _, _, downRight] = this.scene().getAdjacentEnts(
            this.entity.x, this.entity.y, useCache=true
        );

        candidates = [];

        R = findMatchInStack(right);
        if (R !== undefined && R.entity.rockFrame === undefined) {
            candidates.push("2x1");
        }

        D = findMatchInStack(down);
        if (D !== undefined && D.entity.rockFrame === undefined) {
            candidates.push("1x2");
        }

        DR = undefined;
        if (candidates.length === 2) {
            DR = findMatchInStack(downRight);
            if (DR !== undefined && DR.entity.rockFrame === undefined) {
                candidates.push("2x2");
            }
        }

        if (!candidates) {
            return;
        }

        g = 6 / 26;
        h = 0.21  // 3/26 rounded;
        nh = -0.235  // -3/26 rounded, weird asymmetric offset issues;

        choice = candidates[(Math.random() * candidates.length) | 0];
        if (choice === "2x1") {
            this.entity.rockFrame = 3;
            this.entity.placeVisual = (nh, 0);
            R.entity.rockFrame = 4;
            R.entity.placeVisual = (h, 0);
        }
        else if (choice === "1x2") {
            this.entity.rockFrame = 5;
            this.entity.placeVisual = (0, 0);
            D.entity.rockFrame = 6;
            D.entity.placeVisual = (0, g);
        }
        else if (choice === "2x2") {
            this.entity.rockFrame = 7;
            this.entity.placeVisual = (nh, 0);
            R.entity.rockFrame = 8;
            R.entity.placeVisual = (h, 0);
            D.entity.rockFrame = 9;
            D.entity.placeVisual = (nh, g);
            DR.entity.rockFrame = 10;
            DR.entity.placeVisual = (h, g);
        }
    }

    itemChange(change, value) {
        if (change === this.ItemPositionChange) {

            currentX, currentY = this.entity.x, this.entity.y;

            xc, yc = value.x(), value.y();

            // TODO: fix this hack, this is only needed because we don't have a scene on init
            w, h = 28, 16;
            if (this.scene()) {
                w = this.scene().roomWidth;
                h = this.scene().roomHeight;
            }

            x = Math.round(xc / Entity.GRID_SIZE);
            y = Math.round(yc / Entity.GRID_SIZE);

            x = Math.min(Math.max(x, 0), w - 1);
            y = Math.min(Math.max(y, 0), h - 1);

            if (x !== currentX || y !== currentY) {
                // TODO: above hack is here too
                if (settings.value("SnapToBounds") === "1" && this.scene()) {
                    x, y = this.scene().roomInfo.snapToBounds(x, y);
                }

                this.updateCoords(x, y);

                this.updateTooltip();
                if (this.isSelected()) {
                    mainWindow.dirt();
                }
            }

            xc = x * Entity.GRID_SIZE;
            yc = y * Entity.GRID_SIZE;

            value.setX(xc);
            value.setY(yc);

            this.getStack();
            if (this.popup) {
                this.popup.update(this.stack);
            }

            return value;
        }

        return QGraphicsItem.itemChange(this, change, value);
    }

    boundingRect() {
        // if (this.entity.pixmap) {
        //     return QRectF(this.entity.pixmap.rect())
        // }
        // else {
        return QRectF(0.0, 0.0, 26.0, 26.0);
    }

    updatePosition() {
        this.setPos(this.entity.x * 26, this.entity.y * 26);
    }

    getGfxOverride() {
        gfxData = this.scene().getBGGfxData();
        if (gfxData === undefined) {
            return undefined;
        }

        entID = `${this.entity.Type}.${this.entity.Variant}.${this.entity.Subtype}`;
        return gfxData["Entities"].get(entID);
    }

    getCurrentImg() {
        override = this.getGfxOverride();
        return override === undefined ? this.entity.imgPath : override.get("Image");
    }

    paint(painter, option, widget) {

        painter.setRenderHint(QPainter.Antialiasing, true);
        painter.setRenderHint(QPainter.SmoothPixmapTransform, true);

        painter.setBrush(Qt.Dense5Pattern);
        painter.setPen(QPen(Qt.white));

        if (this.entity.pixmap) {
            xc, yc = 0, 0;

            typ, variant, sub = this.entity.Type, this.entity.Variant, this.entity.Subtype;

            function WallSnap() {
                ex = this.entity.x;
                ey = this.entity.y;

                shape = this.scene().roomInfo.shapeData;

                walls = shape["Walls"];
                distancesY = [
                    ((ex < w[0] || ex > w[1]) ? 100000 : abs(ey - w[2]), w)
                    for w of walls["X"]
                ];
                distancesX = [
                    ((ey < w[0] || ey > w[1]) ? 100000 : abs(ex - w[2]), w)
                    for w of walls["Y"]
                ];

                closestY = min(distancesY, key=lambda w: w[0]);
                closestX = min(distancesX, key=lambda w: w[0]);

                // TODO: match up with game when distances are equal
                wx, wy = 0, 0;
                if (closestY[0] < closestX[0]) {
                    w = closestY[1];
                    wy = w[2] - ey;
                }
                else {
                    w = closestX[1];
                    wx = (w[2] - ex) * 2;
                }

                return wx, wy;
            }

            customPlaceVisuals = { WallSnap };

            recenter = this.entity.placeVisual;

            imgPath = this.entity.imgPath;

            rendered = this.entity.pixmap;
            renderFunc = painter.drawPixmap;

            override = this.getGfxOverride();

            if (override !== undefined) {
                img = override.get("Image");
                if (img) {
                    rendered = QPixmap(img);
                    imgPath = img;

                    placeVisual = override.get("PlaceVisual");
                    if (placeVisual !== undefined) {
                        parts = placeVisual.split(",").map(x => x.strip());
                        if (parts.length === 2 && checkFloat(parts[0]) && checkFloat(parts[1])) {
                            placeVisual = (float(parts[0]), float(parts[1]));
                        }
                        else {
                            placeVisual = parts[0];
                        }
                        recenter = placeVisual;
                    }
                }

                if (override.get("InvertDepth") === "1") {
                    this.setZValue(-1 * this.entity.y);
                }
            }

            if (recenter) {
                if (typeof recenter === "string") {
                    recenter = customPlaceVisuals.get(recenter, undefined);
                    if (recenter) {
                        xc, yc = recenter();
                    }
                }
                else {
                    xc, yc = recenter;
                }
            }

            xc += 1;
            yc += 1;

            function drawGridBorders() {
                painter.drawLine(0, 0, 0, 4);
                painter.drawLine(0, 0, 4, 0);

                painter.drawLine(26, 0, 26, 4);
                painter.drawLine(26, 0, 22, 0);

                painter.drawLine(0, 26, 4, 26);
                painter.drawLine(0, 26, 0, 22);

                painter.drawLine(26, 26, 22, 26);
                painter.drawLine(26, 26, 26, 22);
            }

            if (this.entity.config.renderPit) {
                Entity.PitAnm2.frame = this.getPitFrame(imgPath, rendered);
                Entity.PitAnm2.spritesheets[0] = rendered;
                rendered = this.scene().getFrame(imgPath + " - pit", Entity.PitAnm2);
                renderFunc = painter.drawImage;
            }
            else if (this.entity.config.renderRock && this.entity.rockFrame !== undefined) {
                Entity.RockAnm2.frame = this.entity.rockFrame;
                Entity.RockAnm2.spritesheets[0] = rendered;
                rendered = this.scene().getFrame(imgPath + " - rock", Entity.RockAnm2);
                renderFunc = painter.drawImage;

                // clear frame after rendering to reset for next frame
                this.entity.rockFrame = undefined;
            }

            width, height = rendered.width(), rendered.height();

            x = +((xc * 26 - width) / 2);
            y = +(yc * 26 - height);

            renderFunc(x, y, rendered);

            // if (the offset === high enough, draw an indicator of the actual position
            if (!this.entity.config.disableOffsetIndicator && (
                abs(1 - yc) > 0.5 || abs(1 - xc) > 0.5
            )) {
                painter.setPen(this.OFFSET_SELECTION_PEN);
                painter.setBrush(Qt.NoBrush);
                painter.drawLine(13, 13, int(x + width / 2), y + height - 13);
                drawGridBorders();
                painter.fillRect(
                    int(x + width / 2 - 3), y + height - 13 - 3, 6, 6, Qt.red
                );
            }

            if (this.isSelected()) {
                painter.setPen(this.SELECTION_PEN);
                painter.setBrush(Qt.NoBrush);
                painter.drawRect(x, y, width, height);

                // Grid space boundary
                painter.setPen(Qt.green);
                drawGridBorders();
            }

            if (this.entity.overlaypixmap) {
                painter.drawPixmap(0, 0, this.entity.overlaypixmap);
            }
        }

        if (!this.entity.known) {
            painter.setFont(QFont("Arial", 6));

            painter.drawText(2, 26, `${typ}.${variant}.${sub}`);
        }

        warningIcon = undefined;
        // applies to entities that don't have a corresponding entities2 entry
        if (!this.entity.known || this.entity.config.invalid) {
            warningIcon = Entity.INVALID_ERROR_IMG;
        }
        // entities have 12 bits for type, variant, && subtype (?)
        // common mod error is to make them outside that range
        else if (this.entity.config.isOutOfRange()) {
            warningIcon = Entity.OUT_OF_RANGE_WARNING_IMG;
        }

        if (warningIcon) {
            painter.drawPixmap(18, -8, warningIcon);
        }
    }

    remove() {
        if (this.popup) {
            this.popup.remove();
            this.scene().views()[0].canDelete = true;
        }
        this.updateBlockedDoor(true);
        this.setParentItem(undefined);
        this.scene().removeItem(this);
    }

    mouseReleaseEvent(event) {
        e = this.entity;
        if (event.button() === Qt.MiddleButton && e.config.hasBitfields && !e.config.invalidBitfield) {
            new EntityMenu(e);
        }
        this.hideWeightPopup();
        QGraphicsItem.mouseReleaseEvent(this, event);
    }

    hoverEnterEvent(event) {
        this.createWeightPopup();
    }

    hoverLeaveEvent(event) {
        this.hideWeightPopup();
    }

    getStack() {
        // Get the stack
        stack = this.collidingItems(Qt.IntersectsItemBoundingRect);
        stack.push(this);

        // Make sure there are no doors or popups involved
        this.stack = stack.filter(x => x instanceof Entity);

        // 1 depth is not a stack
        this.stackDepth = this.stack.length;
    }

    createWeightPopup() {
        this.getStack();
        if (this.stackDepth <= 1 || this.stack.some(x => x.popup && x !== this && x.popup.isVisible())) {
            this.hideWeightPopup();
            return;
        }

        // if there's no popup, make a popup
        if (this.popup) {
            if (this.popup.activeSpinners !== this.stackDepth) {
                this.popup.update(this.stack);
            }
            this.popup.setVisible(true);
            return;
        }

        this.scene().views()[0].canDelete = false;
        this.popup = EntityStack(this.stack);
        this.scene().addItem(this.popup);
    }

    hideWeightPopup() {
        if (this.popup && !mainWindow.scene.selectedItems().includes(this)) {
            this.popup.setVisible(false);
            if (this.scene()) {
                this.scene().views()[0].canDelete = true;
            }
        }
    }
}

class EntityMenu extends QWidget {
    /**
     * Initializes the widget.
     */
    constructor(entity) {
        super();

        this.layout = QVBoxLayout();

        this.entity = entity;
        this.setupList();

        this.layout.addWidget(this.list);
        this.setLayout(this.layout);
    }

    setupList() {
        this.list = QListWidget();
        this.list.setViewMode(this.list.ListMode);
        this.list.setSelectionMode(this.list.ExtendedSelection);
        this.list.setResizeMode(this.list.Adjust);
        this.list.setContextMenuPolicy(Qt.CustomContextMenu);

        cursor = QCursor();
        this.customContextMenu(cursor.pos());
    }

    changeProperty(bitfieldElement, value) {
        this.entity.setBitfieldElementValue(bitfieldElement, value);

        mainWindow.dirt();
        mainWindow.scene.update();
    }

    updateLabel(label, bitfieldElement) {
        label.setText(`${bitfieldElement.name}: ${this.getDisplayValue(bitfieldElement)} ${bitfieldElement.unit}`);
    }

    connectBitfieldElement(widget, bitfieldElement, label=undefined) {
        function changeValue(x) {
            value = bitfieldElement.getRawValueFromWidgetValue(x);
            this.changeProperty(bitfieldElement, value);

            if (label) {
                this.updateLabel(label, bitfieldElement);
            }
        }

        if (bitfieldElement.widget === "dropdown") {
            widget.currentIndexChanged.connect(changeValue);
        }
        else if (bitfieldElement.widget === "checkbox") {
            widget.stateChanged.connect(() => changeValue(widget.isChecked()));
        }
        else {
            widget.valueChanged.connect(changeValue);
        }

        if (label) {
            this.updateLabel(label, bitfieldElement);
        }
    }

    getWidgetValue(bitfieldElement) {
        return bitfieldElement.getWidgetValue(
            this.entity.getBitfieldValue(bitfieldElement.bitfield)
        );
    }

    getDisplayValue(bitfieldElement) {
        return bitfieldElement.getDisplayValue(
            this.entity.getBitfieldValue(bitfieldElement.bitfield)
        );
    }

    static WIDGETS_WITH_LABELS = new Set(["slider", "dial"]);

    customContextMenu(pos) {
        menu = QMenu(this.list);

        for (const bitfieldElement of this.entity.config.getBitfieldElements()) {
            if (!this.entity[bitfieldElement.bitfield.key]) {
                continue;
            }

            label = undefined;
            if (EntityMenu.WIDGETS_WITH_LABELS.has(bitfieldElement.widget)) {
                action = QWidgetAction(menu);
                label = QLabel("");
                action.setDefaultWidget(label);
                menu.addAction(action);
            }

            action = QWidgetAction(menu);
            widget = undefined;
            if (bitfieldElement.widget === "spinner") {
                widget = QSpinBox();
                minimum, maximum = bitfieldElement.getWidgetRange();
                widget.setRange(minimum, maximum);
                widget.setValue(this.getWidgetValue(bitfieldElement));
                widget.setPrefix(bitfieldElement.name + ": ");
                if (bitfieldElement.floatvalueoffset !== 0) {
                    widget.setSuffix(`${bitfieldElement.floatvalueoffset.toString().substr(1)} ${bitfieldElement.unit}`);
                }
                else {
                    widget.setSuffix(` ${bitfieldElement.unit}`);
                }
            }
            else if (bitfieldElement.widget === "dropdown") {
                widget = QComboBox();
                for (const item of bitfieldElement.dropdownkeys) {
                    widget.addItem(item);
                }
                widget.setCurrentIndex(this.getWidgetValue(bitfieldElement));
            }
            else if (bitfieldElement.widget === "slider") {
                widget = QSlider(Qt.Horizontal);
                minimum, maximum = bitfieldElement.getWidgetRange();
                widget.setRange(minimum, maximum);
                widget.setValue(this.getWidgetValue(bitfieldElement));
            }
            else if (bitfieldElement.widget === "dial") {
                widget = QDial();
                minimum, maximum = bitfieldElement.getWidgetRange();
                widget.setRange(minimum, maximum);
                widget.setValue(this.getWidgetValue(bitfieldElement));
                widget.setNotchesVisible(true);
                widget.setWrapping(true);
            }
            else if (bitfieldElement.widget === "checkbox") {
                widget = QCheckBox();
                widget.setText(bitfieldElement.name);
                widget.setChecked(this.getWidgetValue(bitfieldElement));
            }

            if (bitfieldElement.tooltip) {
                widget.setToolTip(bitfieldElement.tooltip);
            }

            action.setDefaultWidget(widget);
            this.connectBitfieldElement(widget, bitfieldElement, label);
            menu.addAction(action);
        }

        // End it
        menu.exec(this.list.mapToGlobal(pos));
    }
}

class EntityStack extends QGraphicsItem {
    static MAX_STACK_DEPTH = 25;

    class WeightSpinner extends QDoubleSpinBox {
        constructor() {
            super(this);

            this.setRange(0.0, 100.0);
            this.setDecimals(2);
            this.setSingleStep(0.1);
            this.setFrame(false);
            this.setAlignment(Qt.AlignHCenter);

            this.setFont(QFont("Arial", 10));

            palette = this.palette();
            palette.setColor(QPalette.Base, Qt.transparent);
            palette.setColor(QPalette.Text, Qt.white);
            palette.setColor(QPalette.Window, Qt.transparent);

            this.setPalette(palette);
            this.setButtonSymbols(QAbstractSpinBox.NoButtons);
        }
    }

    class Proxy extends QGraphicsProxyWidget {
        constructor(button, parent) {
            super(parent);
            this.setWidget(button);
        }
    }

    constructor(items) {
        super();
        this.setZValue(1000);

        this.spinners = [];
        this.activeSpinners = 0;
        this.update(items);
    }

    update(items) {
        activeSpinners = items.length;

        for (const i of range(activeSpinners - this.spinners.length)) {
            weight = this.WeightSpinner();
            weight.valueChanged.connect(() => this.weightChanged(i));
            this.spinners.push(new EntityStack.Proxy(weight, this));
        }

        for (const i of range(activeSpinners, this.spinners.length)) {
            this.spinners[i].setVisible(false);
        }

        if (activeSpinners > 1) {
            for (const [ i, item ] of Object.entries(items)) {
                spinner = this.spinners[i];
                spinner.widget().setValue(item.entity.weight);
                spinner.setVisible(true);
            }
        }
        else {
            this.setVisible(false);
        }

        // it's very important that this happens AFTER setting up the spinners
        // it greatly increases the odds of races with weightChanged if (items are updated first
        this.items = items;
        this.activeSpinners = activeSpinners;
    }

    weightChanged(idx) {
        if (idx < this.activeSpinners) {
            this.items[idx].entity.weight = this.spinners[idx].widget().value();
        }
    }

    paint(painter, option, widget) {
        painter.setRenderHint(QPainter.Antialiasing, true);
        painter.setRenderHint(QPainter.SmoothPixmapTransform, true);

        brush = QBrush(QColor(0, 0, 0, 80));
        painter.setPen(QPen(Qt.transparent));
        painter.setBrush(brush);

        r = this.boundingRect().adjusted(0, 0, 0, -16);

        path = QPainterPath();
        path.addRoundedRect(r, 4, 4);
        path.moveTo(r.center().x() - 6, r.bottom());
        path.lineTo(r.center().x() + 6, r.bottom());
        path.lineTo(r.center().x(), r.bottom() + 12);
        painter.drawPath(path);

        painter.setPen(QPen(Qt.white));
        painter.setFont(QFont("Arial", 8));

        w = 0;
        for (const [ i, item ] of Object.entries(this.items)) {
            pix = item.entity.iconpixmap;
            this.spinners[i].setPos(w - 8, r.bottom() - 26);
            w += 4;
            painter.drawPixmap(int(w), int(r.bottom() - 20 - pix.height()), pix);

            // painter.drawText(w, r.bottom()-16, pix.width(), 8, Qt.AlignCenter, ": {.1f}".format(item.entity.weight))
            w += pix.width();
        }
    }

    boundingRect() {
        width = 0;
        height = 0;

        // Calculate the combined size
        for (const item of this.items) {
            dx, dy = 26, 26;
            pix = item.entity.iconpixmap;
            if (pix !== undefined) {
                dx, dy = pix.rect().width(), pix.rect().height();
            }
            width = width + dx;
            height = Math.max(height, dy);
        }

        // Add of buffers
        height = height + 8 + 8 + 8 + 16  // Top, bottom, weight text, and arrow;
        width = width + 4 + len(this.items) * 4  // Left and right and the middle bits;

        this.setX(this.items[-1].x() - width / 2 + 13);
        this.setY(this.items[-1].y() - height);

        return QRectF(0.0, 0.0, width, height);
    }

    remove() {
        // Fix for the null pointer left by the scene parent of the widget, avoids a segfault from the dangling pointer
        for (spin of this.spinners) {
            // spin.widget().setParent(undefined);
            spin.setWidget(undefined); // Turns out this function calls the above commented out function
            this.scene().removeItem(spin);
        }
        // del this.spinners // causes crashes

        this.scene().removeItem(this);
    }
}


class Door extends QGraphicsItem {
    static Image;
    static DisabledImage;

    constructor(doorItem) {
        super();

        // Supplied entity info
        this.doorItem = doorItem;

        this.blockingCount = 0;

        this.setPos(this.doorItem[0] * 26 - 13, this.doorItem[1] * 26 - 13);
        this.setParentItem(mainWindow.scene.roomDoorRoot);

        tr = QTransform();
        if ([0, 13].includes(doorItem[0])) {
            tr.rotate(270);
            this.moveBy(-13, 0);
        }
        else if ([14, 27].includes(doorItem[0])) {
            tr.rotate(90);
            this.moveBy(13, 0);
        }
        else if ([8, 15].includes(doorItem[1])) {
            tr.rotate(180);
            this.moveBy(0, 13);
        }
        else {
            this.moveBy(0, -13);
        }

        if (!Door.Image) {
            Door.Image = QImage("resources/Backgrounds/Door.png");
            Door.DisabledImage = QImage("resources/Backgrounds/DisabledDoor.png");
        }

        this.image = Door.Image.transformed(tr);
        this.disabledImage = Door.DisabledImage.transformed(tr);
    }

    get exists(): boolean {
        return !!this.doorItem[2];
    }

    set exists(val: boolean) {
        this.doorItem[2] = val;
    }

    paint(painter, option, widget) {
        painter.setRenderHint(QPainter.Antialiasing, true);
        painter.setRenderHint(QPainter.SmoothPixmapTransform, true);

        if (this.exists) {
            painter.drawImage(0, 0, this.image);
        }
        else {
            painter.drawImage(0, 0, this.disabledImage);
        }
    }

    boundingRect() {
        return QRectF(0.0, 0.0, 64.0, 52.0);
    }

    mouseDoubleClickEvent(event) {
        this.exists = !this.exists;

        event.accept();
        this.update();
        mainWindow.dirt();
    }

    remove() {
        this.scene().removeItem(this);
    }
}


////////////////////////////////////////////////
//     Dock Widgets     //
////////////////////////////////////////////////

// Room Selector
////////////////////////////////////////////////


class Room extends QListWidgetItem {

    // contains concrete room information necessary for examining a room's game qualities
    // such as type, variant, subtype, and shape information
    class Info {
        //////////////////// SHAPE DEFINITIONS
        // w x h
        // 1 = 1x1, 2 = 1x0.5, 3 = 0.5x1, 4 = 1x2, 5 = 0.5x2, 6 = 2x1, 7 = 2x0.5, 8 = 2x2
        // 9 = DR corner, 10 = DL corner, 11 = UR corner, 12 = UL corner
        // all coords must be offset -1, -1 when saving
        static Shapes = {
            [1]: {  // 1x1
                Doors: [[7, 0], [0, 4], [14, 4], [7, 8]],
                // format: min, max on axis, cross axis coord, normal direction along cross axis
                Walls: {
                    X: [(0, 14, 0, 1), (0, 14, 8, -1)],
                    Y: [(0, 8, 0, 1), (0, 8, 14, -1)],
                },
                Dims: (15, 9),
            },
            [2]: {  // horizontal closet (1x0.5)
                Doors: [[0, 4], [14, 4]],
                Walls: {
                    X: [(0, 14, 2, 1), (0, 14, 6, -1)],
                    Y: [(2, 6, 0, 1), (2, 6, 14, -1)],
                },
                TopLeft: 30,  // Grid coord
                BaseShape: 1,  // Base Room shape this is rendered over
                Dims: (15, 5),
            },
            [3]: {  // vertical closet (0.5x1)
                Doors: [[7, 0], [7, 8]],
                Walls: {
                    X: [(4, 10, 0, 1), (4, 10, 8, -1)],
                    Y: [(0, 8, 4, 1), (0, 8, 10, -1)],
                },
                TopLeft: 4,
                BaseShape: 1,
                Dims: (7, 9),
            },
            [4]: {  // 1x2 room
                Doors: [[7, 0], [14, 4], [0, 4], [14, 11], [0, 11], [7, 15]],
                Walls: {
                    X: [(0, 14, 0, 1), (0, 14, 15, -1)],
                    Y: [(0, 15, 0, 1), (0, 15, 14, -1)],
                },
                Dims: (15, 16),
            },
            [5]: {  // tall closet (0.5x2)
                Doors: [[7, 0], [7, 15]],
                Walls: {
                    X: [(4, 10, 0, 1), (4, 10, 15, -1)],
                    Y: [(0, 15, 4, 1), (0, 15, 10, -1)],
                },
                TopLeft: 4,
                BaseShape: 4,
                Dims: (7, 16),
            },
            [6]: {  // 2x1 room
                Doors: [[7, 0], [0, 4], [7, 8], [20, 8], [27, 4], [20, 0]],
                Walls: {
                    X: [(0, 27, 0, 1), (0, 27, 8, -1)],
                    Y: [(0, 8, 0, 1), (0, 8, 27, -1)],
                },
                Dims: (28, 9),
            },
            [7]: {  // wide closet (2x0.5)
                Doors: [[0, 4], [27, 4]],
                Walls: {
                    X: [(0, 27, 2, 1), (0, 27, 6, -1)],
                    Y: [(2, 6, 0, 1), (2, 6, 27, -1)],
                },
                TopLeft: 56,
                BaseShape: 6,
                Dims: (28, 5),
            },
            [8]: {  // 2x2 room
                Doors: [
                    [7, 0],
                    [0, 4],
                    [0, 11],
                    [20, 0],
                    [7, 15],
                    [20, 15],
                    [27, 4],
                    [27, 11],
                ],
                Walls: {
                    X: [(0, 27, 0, 1), (0, 27, 15, -1)],
                    Y: [(0, 15, 0, 1), (0, 15, 27, -1)],
                },
                Dims: (28, 16),
            },
            [9]: {  // mirrored L room
                Doors: [
                    [20, 0],
                    [27, 4],
                    [7, 15],
                    [20, 15],
                    [13, 4],
                    [0, 11],
                    [27, 11],
                    [7, 7],
                ],
                Walls: {
                    X: [(0, 13, 7, 1), (13, 27, 0, 1), (0, 27, 15, -1)],
                    Y: [(7, 15, 0, 1), (0, 7, 13, 1), (0, 15, 27, -1)],
                },
                BaseShape: 8,
                MirrorX: 10,
                MirrorY: 11,
                Dims: (28, 16),
            },
            [10]: {  // L room
                Doors: [
                    [0, 4],
                    [14, 4],
                    [7, 0],
                    [20, 7],
                    [7, 15],
                    [20, 15],
                    [0, 11],
                    [27, 11],
                ],
                Walls: {
                    X: [(0, 14, 0, 1), (14, 27, 7, 1), (0, 27, 15, -1)],
                    Y: [(0, 15, 0, 1), (0, 7, 14, -1), (7, 15, 27, -1)],
                },
                BaseShape: 8,
                MirrorX: 9,
                MirrorY: 12,
                Dims: (28, 16),
            },
            [11]: {  // mirrored r room
                Doors: [
                    [0, 4],
                    [7, 8],
                    [7, 0],
                    [13, 11],
                    [20, 0],
                    [27, 4],
                    [20, 15],
                    [27, 11],
                ],
                Walls: {
                    X: [(0, 27, 0, 1), (0, 13, 8, -1), (13, 27, 15, -1)],
                    Y: [(0, 8, 0, 1), (8, 15, 13, 1), (0, 15, 27, -1)],
                },
                BaseShape: 8,
                MirrorX: 12,
                MirrorY: 9,
                Dims: (28, 16),
            },
            [12]: {  // r room
                Doors: [
                    [0, 4],
                    [7, 0],
                    [20, 0],
                    [14, 11],
                    [27, 4],
                    [7, 15],
                    [0, 11],
                    [20, 8],
                ],
                Walls: {
                    X: [(0, 27, 0, 1), (14, 27, 8, -1), (0, 14, 15, -1)],
                    Y: [(0, 15, 0, 1), (8, 15, 14, -1), (0, 8, 27, -1)],
                },
                BaseShape: 8,
                MirrorX: 11,
                MirrorY: 10,
                Dims: (28, 16),
            },
        };

        static {
            for (const shape of Shapes.values()) {
                doorWalls = shape.DoorWalls = [];
                for (const door of shape.Doors) {
                    door.push(true);
                    for (const wall of shape.Walls.X) {
                        if (door[0] >= wall[0] && door[0] <= wall[1] && door[1] === wall[2]) {
                            doorWalls.push((door, wall, "X"));
                            break;
                        }
                    }
                    for (const wall of shape.Walls.Y) {
                        if (door[1] >= wall[0] && door[1] <= wall[1] && door[0] === wall[2]) {
                            doorWalls.push((door, wall, "Y"));
                        }
                    }
                }
            }
        }

        constructor(this, t=0, v=0, s=0, shape=1) {
            this.type = t;
            this.variant = v;
            this.subtype = s;
            this.shape = shape;
        }

        get shape() {
            return this._shape;
        }

        set shape(val) {
            this._shape = val;
            this.shapeData = Room.Info.Shapes[this.shape];
            bs = this.shapeData.get("BaseShape");
            this.baseShapeData = bs && Room.Info.Shapes[bs];
            this.makeNewDoors();
        }

        // represents the actual dimensions of the room, including out of bounds
        get dims() {
            return (this.baseShapeData ?? this.shapeData).Dims;
        }

        get width(): number {
            return this.shapeData.Dims[0];
        }

        get height(): number {
            return this.shapeData.Dims[1];
        }

        makeNewDoors(): void {
            this.doors = this.shapeData.Doors.map(door => door.slice());
        }

        gridLen(): number {
            return this.dims[0] * this.dims[1];
        }

        static gridIndex(x: number, y: number, w: number) {
            return y * w + x;
        }

        inFrontOfDoor(x: number, y: number) {
            for (const [ door, wall, axis ] of this.shapeData.DoorWalls) {
                if (axis === "X" && door[0] === x && y - door[1] === wall[3]) {
                    return door;
                }
                if (axis === "Y" && door[1] === y && x - door[0] === wall[3]) {
                    return door;
                }
            }
            return undefined;
        }

        static #axisBounds(a, c, w): boolean {
            const [ wMin, wMax, wLvl, wDir ] = w;
            return a < wMin || a > wMax || ((c > wLvl) - (c < wLvl)) === wDir;
        }

        isInBounds(x: number, y: number): boolean {
            return this.shapeData.Walls.X.every(w => Room.Info.#axisBounds(x, y, w)) &&
                   this.shapeData.Walls.Y.every(w => Room.Info.#axisBounds(y, x, w));
        }

        snapToBounds(x: number, y: number, dist = 1) {
            for (const w of this.shapeData.Walls.X) {
                if (!Room.Info.#axisBounds(x, y, w)) {
                    y = w[2] + w[3] * dist;
                }
            }

            for (const w of this.shapeData.Walls.Y) {
                if (!Room.Info.#axisBounds(y, x, w)) {
                    x = w[2] + w[3] * dist;
                }
            }

            return (x, y);
        }
    }

    /**
     * Initializes the room item.
     */
    constructor(
        name="New Room",
        spawns=[],
        palette={},
        difficulty=1,
        weight=1.0,
        myType=1,
        variant=0,
        subtype=0,
        shape=1,
        doors=undefined,
    ) {
        super(this);

        this.name = name;

        this.info = new Room.Info(myType, variant, subtype, shape);
        if (doors) {
            if (this.info.doors.length !== doors.length) {
                printf(`${name} (${variant}) : Invalid doors!`, doors);
            }
            this.info.doors = doors;
        }

        this.gridSpawns = spawns ?? [[] for x of range(this.info.gridLen())];
        if (this.info.gridLen() !== this.gridSpawns.length) {
            printf(`${name} (${variant}) : Invalid grid spawns!`);
        }

        this.palette = palette;

        this.difficulty = difficulty;
        this.weight = weight;

        this.xmlProps = {};
        this.#lastTestTime = undefined;

        this.setFlags(this.flags() | Qt.ItemIsEditable);
        this.setToolTip();

        this.renderDisplayIcon();
    }

    get difficulty(): number {
        return this.#difficulty;
    }

    set difficulty(d: number) {
        this.#difficulty = d;
        if (d === 20) {
            this.setForeground(QColor(190, 0, 255));
        }
        else {
            this.setForeground(QColor.fromHsvF(1, 1, min(max(d / 15, 0), 1), 1));
        }
    }

    get name(): string {
        return this.data(0x100);
    }

    set name(n: string) {
        this.setData(0x100, n);
        this.seed = hash(n);
    }

    get gridSpawns() {
        return this._gridSpawns;
    }

    set gridSpawns(g) {
        this._gridSpawns = g;

        this.#spawnCount = 0;
        for (entStack of this.gridSpawns) {
            if (entStack) {
                this.#spawnCount++;
            }
        }
    }

    get lastTestTime(): Date {
        return this.#lastTestTime;
    }

    set lastTestTime(t: Date) {
        this.#lastTestTime = t;
        this.setToolTip();
    }

    static DoorSortKey = door => (door[0], door[1]);

    clearDoors(): void {
        mainWindow.scene.clearDoors();
        for (const door of this.info.doors) {
            new Door(door);
        }
    }

    getSpawnCount(): number {
        return this.#spawnCount;
    }

    reshape(shape, doors=undefined): void {
        this.info.shape = shape;
        if (doors) {
            this.info.doors = doors;
        }
        realWidth = this.info.dims[0];

        gridLen = this.info.gridLen();
        newGridSpawns = [[] for x of range(gridLen)];

        for (const [ stack, x, y ] of this.spawns()) {
            idx = Room.Info.gridIndex(x, y, realWidth);
            if (idx < gridLen) {
                newGridSpawns[idx] = stack;
            }
        }

        this.gridSpawns = newGridSpawns;
    }

    getDesc(): string {
        name = this.name;
        difficulty = this.difficulty;
        weight = this.weight;
        info = this.info;
        return `${name} (${info.type}.${info.variant}.${info.subtype}) (${info.width-2}x${info.height-2}) - Difficulty: ${difficulty}, Weight: ${weight}, Shape: ${info.shape}`;
    }

    setToolTip(): void {
        this.setText(`${this.info.variant} - ${this.name}`);

        lastTest = !this.lastTestTime ? "Never" : this.lastTestTime.astimezone().strftime("%x %I) {%M %p");

        tip = this.getDesc() + `\nLast Tested: ${lastTest}`;

        QListWidgetItem.setToolTip(this, tip);
    }

    /**
     * Renders the mini-icon for display.
     */
    renderDisplayIcon(): void {
        roomTypes = xmlLookups.roomTypes.lookup(room=this, showInMenu=true);
        if (roomTypes.length === 0) {
            printf("Warning: Unknown room type during renderDisplayIcon:", this.getDesc());
            return;
        }

        i = QIcon(roomTypes[0].get("Icon"));
        this.setIcon(i);
    }

    spawns*(): IterableIterator {
        for (let i = 0;
            i >= this.info.width * this.info.height ||
            i >= this.gridSpawns.length;
        i++) {
            const stack = this.gridSpawns[i];
            if (stack) {
                x = (i % this.info.width) | 0;
                y = (i / this.info.width) | 0;
                yield (stack, x, y);
            }
        }
    }

    setRoomBG(val=undefined): void {
        if (val !== undefined) {
            this.roomBG = val;
            return;
        }

        matchPath = mainWindow.path && os.path.split(mainWindow.path)[1];
        this.roomBG = xmlLookups.getRoomGfx(
            room=this, roomfile=mainWindow.roomList.file, path=matchPath
        );
    }

    mirrorX(): void {
        // Flip spawns
        width, height = this.info.dims;
        for (const y of range(height)) {
            for (const x of range((width / 2) | 0)) {
                ox = Room.Info.gridIndex(x, y, width);
                mx = Room.Info.gridIndex(width - x - 1, y, width);
                oxs = this.gridSpawns[ox];
                this.gridSpawns[ox] = this.gridSpawns[mx];
                this.gridSpawns[mx] = oxs;
            }
        }

        // Flip doors
        for (door of this.info.doors) {
            door[0] = width - door[0] - 1;
        }

        // Flip entities
        info = Entity.Info(changeAtStart=false);
        for (const [ stack, x, y ] of this.spawns()) {
            for (const spawn of stack) {
                info.changeTo(spawn[0], spawn[1], spawn[2]);

                // Directional entities
                if (info.config.mirrorX) {
                    for (const i of range(3)) {
                        spawn[i] = info.config.mirrorX[i];
                    }
                }

                // Entities with subtypes that represent degrees
                if (info.config.hasBitfields) {
                    for (const bitfield of info.config.bitfields) {
                        for (const element of bitfield.elements) {
                            if (element.unit === "Degrees") {
                                angle = element.getWidgetValue(
                                    info.getBitfieldValue(bitfield)
                                );

                                // Convert to game direction, of degrees
                                angle = angle * (360 / (element.maximum + 1));
                                angle = (angle + 90) % 360;

                                // Flip
                                x, y = vectorFromAngle(angle);
                                angle = angleFromVector(-x, y) % 360;

                                // Convert to widget value, from degrees
                                angle = (angle / 360) * (element.maximum + 1);
                                angle = (angle + element.valueoffset) % (element.maximum + 1);

                                info.setBitfieldElementValue(
                                    element, element.getRawValueFromWidgetValue(angle)
                                );
                                spawn[2] = info.Subtype;
                            }
                        }
                    }
                }
            }
        }

        // Flip shape
        shape = this.info.shapeData.get("MirrorX");
        if (shape) {
            this.reshape(shape, this.info.doors);
        }
    }

    mirrorY(): void {
        // Flip spawns
        width, height = this.info.dims;
        for (const x of range(width)) {
            for (const y of range((height / 2) | 0)) {
                oy = Room.Info.gridIndex(x, y, width);
                my = Room.Info.gridIndex(x, height - y - 1, width);
                oys = this.gridSpawns[oy];
                this.gridSpawns[oy] = this.gridSpawns[my];
                this.gridSpawns[my] = oys;
            }
        }

        // Flip doors
        for (const door of this.info.doors) {
            door[1] = height - door[1] - 1;
        }

        // Flip entities
        info = Entity.Info(changeAtStart=false);
        for (const stack, x, y of this.spawns()) {
            for (const spawn of stack) {
                info.changeTo(spawn[0], spawn[1], spawn[2]);

                // Directional entities
                if (info.config.mirrorY) {
                    for (const i of range(3)) {
                        spawn[i] = info.config.mirrorY[i];
                    }
                }

                // Entities with subtypes that represent degrees
                if (info.config.hasBitfields) {
                    for (bitfield of info.config.bitfields) {
                        for (element of bitfield.elements) {
                            if (element.unit === "Degrees") {
                                angle = element.getWidgetValue(
                                    info.getBitfieldValue(bitfield)
                                );

                                // Convert to game direction, of degrees
                                angle = angle * (360 / (element.maximum + 1));
                                angle = (angle + 90) % 360;

                                // Flip
                                x, y = vectorFromAngle(angle);
                                angle = angleFromVector(x, -y) % 360;

                                // Convert to widget value, from degrees
                                angle = (angle / 360) * (element.maximum + 1);
                                angle = (angle + element.valueoffset) % (element.maximum + 1);

                                info.setBitfieldElementValue(
                                    element, element.getRawValueFromWidgetValue(angle)
                                );
                                spawn[2] = info.Subtype;
                            }
                        }
                    }
                }
            }
        }

        // Flip shape
        shape = this.info.shapeData.get("MirrorY");
        if (shape) {
            this.reshape(shape, this.info.doors);
        }
    }

}

class RoomDelegate extends QStyledItemDelegate {
    constructor() {
        super();
        this.pixmap = QPixmap("resources/UI/CurrentRoom.png");
    }

    paint(painter, option, index) {
        painter.fillRect(
            option.rect.right() - 19, option.rect.top(), 17, 16, QBrush(Qt.white)
        );

        QStyledItemDelegate.paint(this, painter, option, index);

        item = mainWindow.roomList.list.item(index.row());
        if (item !== undefined && item.data(100)) {
            painter.drawPixmap(option.rect.right() - 19, option.rect.top(), this.pixmap);
        }
    }
}


class FilterMenu extends QMenu {
    paintEvent(event) {
        QMenu.paintEvent(this, event);

        painter = QPainter(this);

        for (const act of this.actions()) {
            rect = this.actionGeometry(act);
            painter.fillRect(
                int(rect.right() / 2 - 12),
                rect.top() - 2,
                24,
                24,
                QBrush(Qt.transparent),
            );
            painter.drawPixmap(
                int(rect.right() / 2 - 12), rect.top() - 2, act.icon().pixmap(24, 24)
            );
        }
    }
}

class RoomSelector extends QWidget {
    /**
     * Initializes the widget.
     */
    constructor() {
        super();

        this.layout = QVBoxLayout();
        this.layout.setSpacing(0);

        this.filterEntity = undefined;

        this.file = undefined;

        this.setupFilters();
        this.setupList();
        this.setupToolbar();

        this.layout.addLayout(this.filter);
        this.layout.addWidget(this.list);
        this.layout.addWidget(this.toolbar);

        this.setLayout(this.layout);
        this.setButtonStates();
    }

    setupFilters() {
        this.filter = QGridLayout();
        this.filter.setSpacing(4);

        fq = QImage();
        fq.load("resources/UI/FilterIcons.png");

        // Set the custom data
        this.filter.typeData = -1;
        this.filter.sizeData = -1;
        this.filter.extraData = {
            enabled: false,
            weight:     { min: 0, max: 100000, useRange: false, enabled: false },
            difficulty: { min: 1, max: 20,     useRange: false, enabled: false },
            subtype:    { min: 0, max: 10,     useRange: false, enabled: false },
            lastTestTime: {
                min: undefined,
                max: undefined,
                useRange: false,
                enabled: false,
            },
            tags: { enabled: false, mode: "Any", tags: [] },
        };

        // ID Filter
        this.IDFilter = QLineEdit();
        this.IDFilter.setPlaceholderText("ID / Name");
        this.IDFilter.textChanged.connect(this.changeFilter);

        // Entity Toggle Button
        this.entityToggle = QToolButton();
        this.entityToggle.setCheckable(true);
        this.entityToggle.checked = false;
        this.entityToggle.setIconSize(QSize(24, 24));
        this.entityToggle.toggled.connect(this.setEntityToggle);
        this.entityToggle.toggled.connect(this.changeFilter);
        this.entityToggle.setIcon(QIcon(QPixmap.fromImage(fq.copy(0, 0, 24, 24))));

        // Type Toggle Button
        this.typeToggle = QToolButton();
        this.typeToggle.setIconSize(QSize(24, 24));
        this.typeToggle.setPopupMode(QToolButton.InstantPopup);

        typeMenu = QMenu();

        this.typeToggle.setIcon(QIcon(QPixmap.fromImage(fq.copy(1 * 24 + 4, 4, 16, 16))));
        act = typeMenu.addAction(QIcon(QPixmap.fromImage(fq.copy(1 * 24 + 4, 4, 16, 16))), "");
        act.setData(-1);
        this.typeToggle.setDefaultAction(act);

        for (const iconType of xmlLookups.roomTypes.lookup(showInMenu=true)) {
            act = typeMenu.addAction(QIcon(iconType.get("Icon")), "");
            act.setData(int(iconType.get("Type")));
        }

        this.typeToggle.triggered.connect(this.setTypeFilter);
        this.typeToggle.setMenu(typeMenu);

        // Weight Toggle Button
        class ExtraFilterToggle extends QToolButton {
            static rightClicked = pyqtSignal();

            mousePressEvent(e) {
                if (e.buttons() === Qt.RightButton) {
                    this.rightClicked.emit();
                }
                else {
                    this.clicked.emit();
                }
                e.accept();
            }
        }

        this.extraToggle = ExtraFilterToggle();
        this.extraToggle.setIconSize(QSize(24, 24));
        this.extraToggle.setPopupMode(QToolButton.InstantPopup);

        this.extraToggle.setIcon(QIcon(QPixmap.fromImage(fq.copy(4 * 24, 0, 24, 24))));
        this.extraToggle.setToolTip("Right click for additional filter options");
        this.extraToggle.clicked.connect(this.setExtraFilter);
        this.extraToggle.rightClicked.connect(() => FilterDialog(this).exec());

        // Size Toggle Button
        this.sizeToggle = QToolButton();
        this.sizeToggle.setIconSize(QSize(24, 24));
        this.sizeToggle.setPopupMode(QToolButton.InstantPopup);

        sizeMenu = FilterMenu();

        q = QImage();
        q.load("resources/UI/ShapeIcons.png");

        this.sizeToggle.setIcon(QIcon(QPixmap.fromImage(fq.copy(3 * 24, 0, 24, 24))));
        act = sizeMenu.addAction(QIcon(QPixmap.fromImage(fq.copy(3 * 24, 0, 24, 24))), "");
        act.setData(-1);
        act.setIconVisibleInMenu(false);
        this.sizeToggle.setDefaultAction(act);

        for (const i of range(12)) {
            act = sizeMenu.addAction(QIcon(QPixmap.fromImage(q.copy(i * 16, 0, 16, 16))), "");
            act.setData(i + 1);
            act.setIconVisibleInMenu(false);
        }

        this.sizeToggle.triggered.connect(this.setSizeFilter);
        this.sizeToggle.setMenu(sizeMenu);

        // Add to Layout
        this.filter.addWidget(QLabel("Filter by:"), 0, 0);
        this.filter.addWidget(this.IDFilter, 0, 1);
        this.filter.addWidget(this.entityToggle, 0, 2);
        this.filter.addWidget(this.typeToggle, 0, 3);
        this.filter.addWidget(this.sizeToggle, 0, 4);
        this.filter.addWidget(this.extraToggle, 0, 5);
        this.filter.setContentsMargins(4, 0, 0, 4);

        // Filter active notification && clear buttons

        // Palette
        this.clearAll = QToolButton();
        this.clearAll.setIconSize(QSize(24, 0));
        this.clearAll.setToolTip("Clear all filters");
        this.clearAll.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed);
        this.clearAll.clicked.connect(this.clearAllFilter);

        this.clearName = QToolButton();
        this.clearName.setIconSize(QSize(24, 0));
        this.clearName.setToolTip("Clear name filter");
        this.clearName.setSizePolicy(this.IDFilter.sizePolicy());
        this.clearName.clicked.connect(this.clearNameFilter);

        this.clearEntity = QToolButton();
        this.clearEntity.setIconSize(QSize(24, 0));
        this.clearEntity.setToolTip("Clear entity filter");
        this.clearEntity.clicked.connect(this.clearEntityFilter);

        this.clearType = QToolButton();
        this.clearType.setIconSize(QSize(24, 0));
        this.clearType.setToolTip("Clear type filter");
        this.clearType.clicked.connect(this.clearTypeFilter);

        this.clearExtra = QToolButton();
        this.clearExtra.setIconSize(QSize(24, 0));
        this.clearExtra.setToolTip("Clear extra filter");
        this.clearExtra.clicked.connect(this.clearExtraFilter);

        this.clearSize = QToolButton();
        this.clearSize.setIconSize(QSize(24, 0));
        this.clearSize.setToolTip("Clear size filter");
        this.clearSize.clicked.connect(this.clearSizeFilter);

        this.filter.addWidget(this.clearAll, 1, 0);
        this.filter.addWidget(this.clearName, 1, 1);
        this.filter.addWidget(this.clearEntity, 1, 2);
        this.filter.addWidget(this.clearType, 1, 3);
        this.filter.addWidget(this.clearSize, 1, 4);
        this.filter.addWidget(this.clearExtra, 1, 5);
    }

    setupList() {
        this.list = QListWidget();
        this.list.setViewMode(this.list.ListMode);
        this.list.setSelectionMode(this.list.ExtendedSelection);
        this.list.setResizeMode(this.list.Adjust);
        this.list.setContextMenuPolicy(Qt.CustomContextMenu);

        this.list.setAutoScroll(true);
        this.list.setDragEnabled(true);
        this.list.setDragDropMode(4);

        this.list.setVerticalScrollBarPolicy(0);
        this.list.setHorizontalScrollBarPolicy(1);

        this.list.setIconSize(QSize(52, 52));
        d = RoomDelegate();
        this.list.setItemDelegate(d);

        this.list.itemSelectionChanged.connect(this.setButtonStates);
        this.list.itemSelectionChanged.connect(this.handleRoomListDisplayChanged);
        this.list.doubleClicked.connect(this.activateEdit);
        this.list.customContextMenuRequested.connect(this.customContextMenu);

        model = this.list.model();
        model.rowsInserted.connect(this.handleRoomListDisplayChanged);
        model.rowsRemoved.connect(this.handleRoomListDisplayChanged);
        model.modelReset.connect(() => this.handleRoomListDisplayChanged()); // fired when cleared;

        this.list.itemDelegate().closeEditor.connect(this.editComplete);
    }

    setupToolbar() {
        this.toolbar = QToolBar();

        this.addRoomButton = this.toolbar.addAction(QIcon(), "Add", this.addRoom);
        this.removeRoomButton = this.toolbar.addAction(QIcon(), "Delete", this.removeRoom);
        this.duplicateRoomButton = this.toolbar.addAction(QIcon(), "Duplicate", this.duplicateRoom);
        this.duplicateRoomButton.setToolTip("Duplicate selected room.\nAlt: Mirror X and Duplicate\nAlt+Shift: Mirror Y && Duplicate");
        this.exportRoomButton = this.toolbar.addAction(QIcon(), "Copy to File...", this.exportRoom);
        this.toolbar.addSeparator();

        this.numRoomsLabel = QLabel();
        this.numRoomsLabel.setIndent(10);
        this.toolbar.addWidget(this.numRoomsLabel);

        this.mirror = false;
        this.mirrorY = false;
    }

    handleRoomListDisplayChanged() {
        selectedRooms = this.selectedRooms().length;

        numRooms = selectedRooms;
        if (numRooms < 2) {
            numRooms = 0;
            for (const room of this.getRooms()) {
                if (!room.isHidden()) {
                    numRooms++;
                }
            }
        }

        this.numRoomsLabel.setText(numRooms > 0 ?
            `${selectedRooms > 1 ? 'Selected rooms' : 'Num Rooms'}: ${numRooms}` :
            ""
        );
    }

    activateEdit() {
        room = this.selectedRoom();
        room.setText(room.name);
        this.list.editItem(this.selectedRoom());
    }

    editComplete(lineEdit) {
        room = this.selectedRoom();
        room.name = lineEdit.text();
        room.setText(`{room.info.variant} - {room.name}`);
        mainWindow.dirt();
    }

    customContextMenu(pos) {
        if (!this.selectedRoom()) {
            return;
        }

        menu = QMenu(this.list);

        // Type
        Type = QWidgetAction(menu);
        c = QComboBox();

        types = xmlLookups.roomTypes.lookup(showInMenu=true);
        matchingTypes = xmlLookups.roomTypes.lookup(
            room=this.selectedRoom(), showInMenu=true
        );

        for (const [ i, t ] of Object.entries(types)) {
            c.addItem(QIcon(t.get("Icon")), t.get("Name"));
            if (matchingTypes.includes(t)) {
                c.setCurrentIndex(i);
            }
        }

        c.currentIndexChanged.connect(this.changeType);
        Type.setDefaultWidget(c);
        menu.addAction(Type);

        // Variant
        Variant = QWidgetAction(menu);
        s = QSpinBox();
        s.setRange(0, 65534);
        s.setPrefix("ID - ");

        s.setValue(this.selectedRoom().info.variant);

        Variant.setDefaultWidget(s);
        s.valueChanged.connect(this.changeVariant);
        menu.addAction(Variant);

        menu.addSeparator();

        // Difficulty
        Difficulty = QWidgetAction(menu);
        dv = QSpinBox();
        dv.setRange(0, 20);
        dv.setPrefix("Difficulty - ");

        dv.setValue(this.selectedRoom().difficulty);

        Difficulty.setDefaultWidget(dv);
        dv.valueChanged.connect(this.changeDifficulty);
        menu.addAction(Difficulty);

        // Weight
        weight = QWidgetAction(menu);
        s = QDoubleSpinBox();
        s.setPrefix("Weight - ");

        s.setValue(this.selectedRoom().weight);

        weight.setDefaultWidget(s);
        s.valueChanged.connect(this.changeWeight);
        menu.addAction(weight);

        // Subtype
        Subtype = QWidgetAction(menu);
        st = QSpinBox();
        st.setRange(0, 4096);
        st.setPrefix("Sub - ");

        st.setValue(this.selectedRoom().info.subtype);

        Subtype.setDefaultWidget(st);
        st.valueChanged.connect(this.changeSubtype);
        menu.addAction(Subtype);

        menu.addSeparator();

        // Room shape
        Shape = QWidgetAction(menu);
        c = QComboBox();

        q = QImage();
        q.load("resources/UI/ShapeIcons.png");

        for (const shapeName of range(1, 13)) {
            c.addItem(
                QIcon(QPixmap.fromImage(q.copy((shapeName - 1) * 16, 0, 16, 16))),
                str(shapeName),
            );
        }
        c.setCurrentIndex(this.selectedRoom().info.shape - 1);
        c.currentIndexChanged.connect(this.changeSize);
        Shape.setDefaultWidget(c);
        menu.addAction(Shape);

        // End it
        menu.exec(this.list.mapToGlobal(pos));
    }

    clearAllFilter() {
        this.IDFilter.clear();
        this.entityToggle.setChecked(false);
        this.filter.typeData = -1;
        this.typeToggle.setIcon(this.typeToggle.defaultAction().icon());
        this.filter.sizeData = -1;
        this.sizeToggle.setIcon(this.sizeToggle.defaultAction().icon());

        this.filter.extraData.enabled = false;

        this.changeFilter();
    }

    clearNameFilter() {
        this.IDFilter.clear();
        this.changeFilter();
    }

    clearEntityFilter() {
        this.entityToggle.setChecked(false);
        this.changeFilter();
    }

    clearTypeFilter() {
        this.filter.typeData = -1;
        this.typeToggle.setIcon(this.typeToggle.defaultAction().icon());
        this.changeFilter();
    }

    clearExtraFilter() {
        this.filter.extraData["enabled"] = false;
        this.changeFilter();
    }

    clearSizeFilter() {
        this.filter.sizeData = -1;
        this.sizeToggle.setIcon(this.sizeToggle.defaultAction().icon());
        this.changeFilter();
    }

    setEntityToggle(checked) {
        this.entityToggle.checked = checked;
    }

    setTypeFilter(action) {
        this.filter.typeData = action.data();
        this.typeToggle.setIcon(action.icon());
        this.changeFilter();
    }

    setExtraFilter(checked, force=undefined) {
        if (force === undefined) {
            force = !this.filter.extraData.enabled  // toggle on click
        }

        this.filter.extraData.enabled = force;
        this.changeFilter();
    }

    setSizeFilter(action) {
        this.filter.sizeData = action.data();
        this.sizeToggle.setIcon(action.icon());
        this.changeFilter();
    }

    colorizeClearFilterButtons() {
        colour = "background-color: #F00;";

        all = false;

        // Name Button
        if (this.IDFilter.text()) {
            this.clearName.setStyleSheet(colour);
            all = true;
        }
        else {
            this.clearName.setStyleSheet("");
        }

        // Entity Button
        if (this.entityToggle.checked) {
            this.clearEntity.setStyleSheet(colour);
            all = true;
        }
        else {
            this.clearEntity.setStyleSheet("");
        }

        // Type Button
        if (this.filter.typeData >= 0) {
            this.clearType.setStyleSheet(colour);
            all = true;
        }
        else {
            this.clearType.setStyleSheet("");
        }

        // Size Button
        if (this.filter.sizeData >= 0) {
            this.clearSize.setStyleSheet(colour);
            all = true;
        }
        else {
            this.clearSize.setStyleSheet("");
        }

        // Extra filters Button
        if (this.filter.extraData["enabled"]) {
            this.clearExtra.setStyleSheet(colour);
            all = true;
        }
        else {
            this.clearExtra.setStyleSheet("");
        }

        // All Button
        if (all) {
            this.clearAll.setStyleSheet(colour);
        }
        else {
            this.clearAll.setStyleSheet("");
        }
    }

    changeFilter() {
        this.colorizeClearFilterButtons();

        // Here we go
        for (const room of this.getRooms()) {
            IDCond = entityCond = typeCond = sizeCond = extraCond = true;

            IDCond = room.text().lowerCase().includes(this.IDFilter.text().lowerCase());

            // Check if the right entity is in the room
            if (this.entityToggle.checked && this.filterEntity) {
                entityCond = room.palette.includes(this.filterEntity.config.uniqueid);
            }

            // Check if (the room === the right type
            if (this.filter.typeData !== -1) {
                // All the normal rooms
                typeCond = this.filter.typeData === room.info.type;

                // for (null rooms, include "empty" rooms regardless of type
                if (!typeCond && this.filter.typeData === 0) {
                    nonCombatRooms = settings.value("NonCombatRoomFilter") === "1";
                    checkTags = ["InEmptyRooms"];
                    if (nonCombatRooms) {
                        checkTags.push("InNonCombatRooms");
                    }

                    hasUsefulEntities = room.palette.values().some(config => !config.matches(tags=checkTags, matchAnyTag=true));

                    typeCond = !hasUsefulEntities;
                }
            }

            if (this.filter.extraData.enabled) {
                // Check if the room is the right weight
                weightData = this.filter.extraData.weight;
                if (extraCond && weightData.enabled) {
                    if (weightData.useRange) {
                        extraCond = extraCond && weightData.min <= room.weight <= weightData.max;
                    }
                    else {
                        eps = 0.0001;
                        extraCond = extraCond && Math.abs(weightData.min - room.weight) < eps;
                    }
                }

                // Check if (the room === the right difficulty
                difficultyData = this.filter.extraData.difficulty;
                if (extraCond && difficultyData.enabled) {
                    if (difficultyData.useRange) {
                        extraCond = extraCond && difficultyData.min <= room.difficulty && room.difficulty <= difficultyData.max;
                    }
                    else {
                        extraCond = difficultyData.min === room.difficulty;
                    }
                }

                // Check if the room is the right subtype
                subtypeData = this.filter.extraData.subtype;
                if (extraCond && subtypeData.enabled) {
                    if (subtypeData.useRange) {
                        extraCond = extraCond && subtypeData.min <= room.info.subtype && room.info.subtype <= subtypeData.max;
                    }
                    else {
                        extraCond = subtypeData.min === room.info.subtype;
                    }
                }

                // Check if the room has been tested between a specific time range,
                // or tested before a certain date
                lastTestTimeData = this.filter.extraData.lastTestTime;
                if (extraCond && lastTestTimeData.enabled) {
                    if (lastTestTimeData.useRange) {
                        // intentionally reversed; min is always the main value, but the default comparison for last time is for earlier times
                        extraCond = extraCond && room.lastTestTime && lastTestTimeData.max <= room.lastTestTime && room.lastTestTime <= lastTestTimeData.min;
                    }
                    else {
                        extraCond = extraCond && (!room.lastTestTime || room.lastTestTime <= lastTestTimeData.min);
                    }
                }

                // Check if the room contains entities with certain tags
                tagsData = this.filter.extraData.tags;
                if (extraCond && tagsData.enabled) {
                    checkTags = tagsData.tags;
                    matchAnyTag = tagsData.mode === "Any" || tagsData.mode === "Blacklist";
                    checkUnmatched = tagsData.mode === "Exclusive";

                    matched = room.palette.values().some(config => config.matches(tags=checkTags, matchAnyTag=matchAnyTag) !== checkUnmatched);

                    if (tagsData.mode === "Blacklist") {
                        extraCond = !matched;
                    }
                    else if (tagsData.mode === "Exclusive") {
                        extraCond = !matched;
                    }
                    else {
                        extraCond = matched;
                    }
                }
            }

            // Check if the room is the right size
            if (this.filter.sizeData !== -1) {
                sizeCond = this.filter.sizeData === room.info.shape;
            }

            // Filter em' out
            isMatch = IDCond && entityCond && typeCond && sizeCond && extraCond;
            room.setHidden(!isMatch);
        }

        this.handleRoomListDisplayChanged();
    }

    setEntityFilter(entity) {
        this.filterEntity = entity;
        this.entityToggle.setIcon(entity.icon);
        if (this.entityToggle.checked) {
            this.changeFilter();
        }
    }

    changeSize(shapeIdx) {
        // Set the Size - gotta lotta shit to do here
        s = shapeIdx + 1;

        // No sense of doing work we don't have to!
        if (this.selectedRoom().info.shape === s) {
            return;
        }

        info = Room.Info(shape=s);
        w, h = info.dims;

        // Check to see if resizing will destroy any entities
        mainWindow.storeEntityList();

        warn = this.selectedRoom().spawns().some(([ stack, x, y ]) => x >= w || y >= h);

        if (warn) {
            msgBox = QMessageBox(
                QMessageBox.Warning,
                "Resize Room?",
                "Resizing this room will delete entities placed outside the new size. Are you sure you want to resize this room?",
                QMessageBox.NoButton,
                this,
            );
            msgBox.addButton("Resize", QMessageBox.AcceptRole);
            msgBox.addButton("Cancel", QMessageBox.RejectRole);
            if (msgBox.exec_() === QMessageBox.RejectRole) {
                // It's time for us to go now.
                return;
            }
        }

        this.selectedRoom().reshape(s);

        // Clear the room and reset the size
        mainWindow.scene.clear();

        this.selectedRoom().clearDoors();

        mainWindow.scene.newRoomSize(s);

        mainWindow.editor.resizeEvent(QResizeEvent(mainWindow.editor.size(), mainWindow.editor.size()));

        // Spawn those entities
        for (const entStack, x, y of this.selectedRoom().spawns()) {
            if (x >= w || y >= h) {
                continue;
            }

            for (const entity of entStack) {
                e = new Entity(
                    x, y, entity[0], entity[1], entity[2], entity[3], respawning=true
                );
            }
        }

        this.selectedRoom().setToolTip();
        mainWindow.dirt();
    }

    changeType(index) {
        for (const r of this.selectedRooms()) {
            r.info.type = index;
            r.renderDisplayIcon();
            r.setRoomBG();

            r.setToolTip();
        }

        mainWindow.scene.updateRoomDepth(this.selectedRoom());
        mainWindow.scene.update();
        mainWindow.dirt();
    }

    changeVariant(val) {
        for (const r of this.selectedRooms()) {
            r.info.variant = val;
            r.setToolTip();
        }
        mainWindow.dirt();
        mainWindow.scene.update();
    }

    changeSubtype(val) {
        for (const r of this.selectedRooms()) {
            r.info.subtype = val;
            r.setToolTip();
        }
        mainWindow.dirt();
        mainWindow.scene.update();
    }

    changeDifficulty(val) {
        for (const r of this.selectedRooms()) {
            r.difficulty = val;
            r.setToolTip();
        }
        mainWindow.dirt();
        mainWindow.scene.update();
    }

    changeWeight(action) {
        for (const r of this.selectedRooms()) {
            // r.weight = float(action.text())
            r.weight = action;
            r.setToolTip();
        }
        mainWindow.dirt();
        mainWindow.scene.update();
    }

    keyPressEvent(event) {
        this.list.keyPressEvent(event);

        if (event.key() === Qt.Key_Delete || event.key() === Qt.Key_Backspace) {
            this.removeRoom();
        }
    }

    /**
     * Creates a new room.
     */
    addRoom() {
        r = new Room();
        this.list.insertItem(this.list.currentRow() + 1, r);
        this.list.setCurrentItem(r, QItemSelectionModel.ClearAndSelect);
        mainWindow.dirt();
    }

    /**
     * Removes selected room (no takebacks)
     */
    removeRoom() {
        rooms = this.selectedRooms();
        if (rooms === undefined || rooms.length === 0) {
            return;
        }

        msgBox = QMessageBox(
            QMessageBox.Warning,
            "Delete Room?",
            "Are you sure you want to delete the selected rooms? This action cannot be undone.",
            QMessageBox.NoButton,
            this,
        );
        msgBox.addButton("Delete", QMessageBox.AcceptRole);
        msgBox.addButton("Cancel", QMessageBox.RejectRole);
        if (msgBox.exec_() === QMessageBox.AcceptRole) {
            this.list.clearSelection();
            for (const item of rooms) {
                this.list.takeItem(this.list.row(item));
            }

            this.list.scrollToItem(this.list.currentItem());
            this.list.setCurrentItem(this.list.currentItem(), QItemSelectionModel.Select);
            mainWindow.dirt();
        }
    }

    /**
     * Duplicates the selected room
     */
    duplicateRoom() {
        rooms = this.orderedSelectedRooms();
        if (!rooms) {
            return;
        }

        numRooms = len(rooms);

        mainWindow.storeEntityList();

        lastPlace = this.list.indexFromItem(rooms[-1]).row() + 1;
        this.selectedRoom().setData(100, false);
        this.list.setCurrentItem(undefined, QItemSelectionModel.ClearAndSelect);

        for (const room of reversed(rooms)) {
            if (this.mirrorY) {
                v = 20000;
                extra = " (flipped Y)";
            }
            else if (this.mirror) {
                v = 10000;
                extra = " (flipped X)";
            }
            else {
                v = numRooms;
                extra = " (copy)";
            }

            usedRoomName = room.name;
            if (room.name.includes(extra) && extra !== "") {
                extraCount = room.name.count(extra);
                regSearch = QRegularExpression(" \((\d*)\)");
                counterMatches = regSearch.match(room.name);
                if (counterMatches.hasMatch()) {
                    counter = counterMatches.captured(counterMatches.lastCapturedIndex());
                    extraCount = extraCount + int(counter);
                }
                usedRoomName = room.name.split(extra)[0];
                extra = extra + ` (${extraCount})`;
            }

            r = new Room(
                deepcopy(usedRoomName + extra),
                deepcopy(room.gridSpawns),
                deepcopy(room.palette),
                deepcopy(room.difficulty),
                deepcopy(room.weight),
                deepcopy(room.info.type),
                deepcopy(room.info.variant + v),
                deepcopy(room.info.subtype),
                deepcopy(room.info.shape),
                deepcopy(room.info.doors.map(door => [...door])),
            );
            r.xmlProps = deepcopy(room.xmlProps);

            // Mirror the room
            if (this.mirror) {
                if (this.mirrorY) {
                    r.mirrorY();
                }
                else {
                    r.mirrorX();
                }
            }

            this.list.insertItem(lastPlace, r);
            this.list.setCurrentItem(r, QItemSelectionModel.Select);
        }

        mainWindow.dirt();
    }

    mirrorButtonOn() {
        this.mirror = true;
        this.duplicateRoomButton.setText("Mirror X");
    }

    mirrorButtonOff() {
        this.mirror = false;
        this.mirrorY = false;
        this.duplicateRoomButton.setText("Duplicate");
    }

    mirrorYButtonOn() {
        if (this.mirror) {
            this.mirrorY = true;
            this.duplicateRoomButton.setText("Mirror Y");
        }
    }

    mirrorYButtonOff() {
        if (this.mirror) {
            this.mirrorY = false;
            this.duplicateRoomButton.setText("Mirror X");
        }
    }

    exportRoom() {

        dialogDir = mainWindow.getRecentFolder();

        target, match = QFileDialog.getSaveFileName(
            this,
            "Select a new name or an existing XML",
            dialogDir,
            "XML File (*.xml)",
            "",
            QFileDialog.DontConfirmOverwrite,
        );
        mainWindow.restoreEditMenu();

        if (target.length === 0) {
            return;
        }

        path = target;

        rooms = this.orderedSelectedRooms();
        // Append these rooms onto the existing file
        if (os.path.exists(path)) {
            oldRooms = mainWindow.open(path);
            oldRooms.rooms.extend(rooms);
            mainWindow.save(oldRooms.rooms, path, fileObj=oldRooms);
        }
        // Make a new file with the selected rooms
        else {
            mainWindow.save(rooms, path, fileObj=this.file);
        }
    }

    setButtonStates() {
        rooms = this.selectedRooms().length > 0;

        this.removeRoomButton.setEnabled(rooms);
        this.duplicateRoomButton.setEnabled(rooms);
        this.exportRoomButton.setEnabled(rooms);
    }

    selectedRoom() {
        return this.list.currentItem();
    }

    selectedRooms() {
        return this.list.selectedItems();
    }

    orderedSelectedRooms() {
        sortedIndexes = this.list.selectionModel().selectedIndexes()
            .sort((a, b) => a.column() - b.column() || a.row() - b.row());
        return sortedIndexes.map(i => this.list.itemFromIndex(i));
    }

    getRooms() {
        return range(this.list.count()).map(i => this.list.item(i));
    }

}


// Entity Palette
////////////////////////////////////////////////


/**
 * Group Item to contain Entities for sorting
 */
class EntityGroupItem extends QStandardItem {

    constructor(group, startIndex=0) {
        super();

        this.objects = [];
        this.config = group;

        this.startIndex = startIndex;

        this.name = group.label ?? "";
        this.entitycount = 0;

        // Labelled groups are added last, so that loose entities are below the main group header.
        labelledGroups = [];

        endIndex = startIndex;
        for (const entry of group.entries) {
            endIndex += 1;
            if (entry instanceof xmlLookups.entities.GroupConfig) {
                if (entry.label) {
                    labelledGroups.push(entry);
                    endIndex--;
                }
                else {
                    groupItem = new EntityGroupItem(entry, endIndex);
                    endIndex = groupItem.endIndex;
                    this.entitycount += groupItem.entitycount;
                    this.objects.push(groupItem);
                }
            }
            else if (entry instanceof xmlLookups.entities.EntityConfig) {
                this.entitycount++;
                this.objects.push(new EntityItem(entry));
            }
        }

        for (const entry of labelledGroups) {
            endIndex++;
            groupItem = new EntityGroupItem(entry, endIndex);
            endIndex = groupItem.endIndex;
            this.entitycount += groupItem.entitycount;
            this.objects.push(groupItem);
        }

        this.endIndex = endIndex;

        this.alignment = Qt.AlignCenter;

        this.collapsed = false;
    }

    /**
     * Retrieves an item of a specific index. The index is already checked for validity
     */
    getItem(index) {
        if (index === this.startIndex) {
            return this;
        }

        checkIndex = this.startIndex;
        for (const obj of this.objects) {
            if (obj instanceof EntityGroupItem) {
                if (index >= obj.startIndex && index <= obj.endIndex) {
                    return obj.getItem(index);
                }
                else {
                    checkIndex = obj.endIndex;
                }
            }
            else {
                checkIndex++;
                if (checkIndex === index) {
                    return obj;
                }
            }
        }
    }

    filterView(view, shownEntities=undefined, parentCollapsed=false) {
        hideDuplicateEntities = settings.value("HideDuplicateEntities") === "1";

        if (shownEntities === undefined) {
            shownEntities = {};
        }

        hasAnyVisible = false;

        collapsed = this.collapsed || parentCollapsed;

        row = this.startIndex;
        for (const item of this.objects) {
            if (item instanceof EntityItem) {
                row++;
                hidden = false;
                if (item.name.lowerCase().includes(view.filter.lowerCase())) {
                    hidden = true;
                }
                else if (hideDuplicateEntities && shownEntities.has(item.config.uniqueid)) {
                    hidden = true;
                }

                view.setRowHidden(row, collapsed || hidden);
                if (!hidden) {
                    shownEntities[item.config.uniqueid] = true;
                    hasAnyVisible = true;
                }
            }
            else if (item instanceof EntityGroupItem) {
                row = item.endIndex;
                visible = item.filterView(view, shownEntities, collapsed);
                hasAnyVisible = hasAnyVisible || visible;
            }
        }

        if (!hasAnyVisible || this.name === "" || parentCollapsed) {
            view.setRowHidden(this.startIndex, true);
        }
        else {
            view.setRowHidden(this.startIndex, false);
        }

        return hasAnyVisible;
    }
}

/**
 * A single entity palette entry, not the in-editor Entity
 */
class EntityItem extends QStandardItem {
    constructor(config) {
        super();

        this.name = config.name;
        this.ID = config.type;
        this.variant = config.variant;
        this.subtype = config.subtype;
        this.icon = QIcon(config.imagePath);
        this.config = config;

        this.setToolTip(this.name);
    }
}

/**
 * Model containing all the grouped objects of a tileset
 */
class EntityGroupModel extends QAbstractListModel {
    constructor(group=undefined) {
        super();

        this.view = undefined;

        if (group === undefined) {
            group = xmlLookups.entities.entityList;
        }

        this.group = new EntityGroupItem(group);
    }

    rowCount(parent=undefined) {
        return this.group.endIndex + 1;
    }

    flags(index) {
        item = this.getItem(index.row());

        if (item instanceof EntityGroupItem) {
            return Qt.ItemIsEnabled;
        }
        else {
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable;
        }
    }

    getItem(index) {
        return this.group.getItem(index);
    }

    data(index, role=Qt.DisplayRole) {
        // Should return the contents of a row when asked for the index

        // Can be optimized by only dealing with the roles we need prior
        // to lookup: Role order is 13, 6, 7, 9, 10, 1, 0, 8

        if (role > 1 && role < 6) {
            return undefined;
        }
        else if (role === Qt.ForegroundRole) {
            return QBrush(Qt.black);
        }
        else if (role === Qt.TextAlignmentRole) {
            return Qt.AlignCenter;
        }

        if (!index.isValid()) {
            return undefined;
        }
        n = index.row();

        if (n < 0) {
            return undefined;
        }
        if (n >= this.rowCount()) {
            return undefined;
        }

        item = this.getItem(n);

        if (role === Qt.DecorationRole) {
            if (item instanceof EntityItem) {
                return item.icon;
            }
        }

        if (role === Qt.ToolTipRole || role === Qt.StatusTipRole || role === Qt.WhatsThisRole) {
            if (item instanceof EntityItem) {
                return `: ${item.name}`;
            }
        }
        else if (role === Qt.DisplayRole) {
            if (item instanceof EntityGroupItem) {
                return item.name + (item.collapsed ? " ▶" : "");
            }
        }
        else if (role === Qt.SizeHintRole) {
            if (item instanceof EntityGroupItem) {
                return QSize(this.view.viewport().width(), 24);
            }
        }
        else if (role === Qt.BackgroundRole) {
            if (item instanceof EntityGroupItem) {
                colour = 165;
                brush = QBrush(QColor(colour, colour, colour), Qt.Dense4Pattern);
                return brush;
            }
        }
        else if (role === Qt.FontRole) {
            font = QFont();
            font.setPixelSize(16);
            font.setBold(true);

            return font;
        }

        return undefined;
    }

}

/**
 * Initializes the widget. Remember to call setTileset() on it whenever the layer changes.
 */
class EntityPalette extends QWidget {
    constructor() {
        super();

        // Make the layout
        this.layout = QVBoxLayout();
        this.layout.setSpacing(0);

        // Create the tabs for (the default && mod entities
        this.tabs = QTabWidget();
        this.populateTabs();
        this.layout.addWidget(this.tabs);

        // Create the hidden search results tab
        this.searchTab = QTabWidget();

        // Funky model setup
        listView = EntityList();
        listView.setModel(EntityGroupModel());
        listView.model().view = listView;
        listView.clicked.connect(this.objSelected);

        // Hide the search results
        this.searchTab.addTab(listView, "Search");
        this.searchTab.hide();

        this.layout.addWidget(this.searchTab);

        // Add the Search bar
        this.searchBar = QLineEdit();
        this.searchBar.setPlaceholderText("Search");
        this.searchBar.textEdited.connect(this.updateSearch);
        this.layout.addWidget(this.searchBar);

        // And Done
        this.setLayout(this.layout);
    }

    populateTabs() {
        for (tab of xmlLookups.entities.tabs) {
            model = new EntityGroupModel(tab);
            if (model.group.entitycount !== 0) {
                listView = EntityList();
                printf(`Populating palette tab "${tab.name}" with ${model.group.entitycount} entities`);

                listView.setModel(model);
                listView.model().view = listView;
                listView.filterList();

                listView.clicked.connect(this.objSelected);

                if (tab.iconSize) {
                    listView.setIconSize(QSize(tab.iconSize[0], tab.iconSize[1]));
                }

                this.tabs.addTab(listView, tab.name);
            }
            else {
                printf(`Skipping empty palette tab ${tab.name}`);
            }
        }
    }

    /**
     * Returns the currently selected object reference, for painting purposes
     */
    currentSelectedObject() {
        if (this.searchBar.text().length > 0) {
            index = this.searchTab.currentWidget().currentIndex().row();
            obj = this.searchTab.currentWidget().model().getItem(index);
        }
        else {
            index = this.tabs.currentWidget().currentIndex().row();
            obj = this.tabs.currentWidget().model().getItem(index);
        }

        return obj;
    }

    /**
     * Emits a signal with the current object when changed
     */
    objSelected() {
        current = this.currentSelectedObject();
        if (current === undefined) {
            return;
        }

        if (current instanceof EntityGroupItem) {
            current.collapsed = !current.collapsed;
            this.tabs.currentWidget().filterList();
            return;
        }

        // holding ctrl skips the filter change step
        kb = +QGuiApplication.keyboardModifiers();

        holdCtrl = kb & Qt.ControlModifier !== 0;
        pinEntityFilter = settings.value("PinEntityFilter") === "1";
        this.objChanged.emit(current, holdCtrl === pinEntityFilter);

        // Throws a signal when the selected object === used as a replacement
        if (kb & Qt.AltModifier !== 0) {
            this.objReplaced.emit(current);
        }
    }

    updateSearch(text) {
        if (this.searchBar.text().length > 0) {
            this.tabs.hide();
            this.searchTab.widget(0).filter = text;
            this.searchTab.widget(0).filterList();
            this.searchTab.show();
        }
        else {
            this.tabs.show();
            this.searchTab.hide();
        }
    }

    updateTabs() {
        for (const i of range(0, this.tabs.count())) {
            this.tabs.widget(i).filterList();
        }
    }

    static objChanged = pyqtSignal(EntityItem, bool);
    static objReplaced = pyqtSignal(EntityItem);
}

class EntityList extends QListView {
    constructor() {
        super();

        this.setFlow(QListView.LeftToRight);
        this.setLayoutMode(QListView.SinglePass);
        this.setMovement(QListView.Static);
        this.setResizeMode(QListView.Adjust);
        this.setWrapping(true);
        this.setIconSize(QSize(26, 26));

        this.setMouseTracking(true);

        this.filter = "";
    }

    mouseMoveEvent(event) {
        index = this.indexAt(event.pos()).row();

        if (index !== -1) {
            item = this.model().getItem(index);

            if (item instanceof EntityItem) {
                QToolTip.showText(event.globalPos(), item.name);
            }
        }
    }

    filterList() {
        m = this.model();
        rows = m.rowCount();

        m.group.filterView(this);
    }
}

class ReplaceDialog extends QDialog {
    class EntSpinners extends QWidget {
        constructor() {
            super();
            layout = QFormLayout();

            this.type = QSpinBox();
            this.type.setRange(1, 2**31 - 1);
            this.variant = QSpinBox();
            this.variant.setRange(-1, 2**31 - 1);
            this.subtype = QSpinBox();
            this.subtype.setRange(-1, 2**8 - 1);

            layout.addRow("&Type:", this.type);
            layout.addRow("&Variant:", this.variant);
            layout.addRow("&Subtype:", this.subtype);

            this.entity = Entity.Info(0, 0, 0, 0, 0, 0, changeAtStart=false);

            this.type.valueChanged.connect(this.resetEnt);
            this.variant.valueChanged.connect(this.resetEnt);
            this.subtype.valueChanged.connect(this.resetEnt);

            this.setLayout(layout);
        }

        getEnt() {
            return (this.type.value(), this.variant.value(), this.subtype.value());
        }

        setEnt(t, v, s) {
            this.type.setValue(t);
            this.variant.setValue(v);
            this.subtype.setValue(s);
            this.entity.changeTo(t, v, s);
        }

        static valueChanged = pyqtSignal();

        resetEnt() {
            this.entity.changeTo(...this.getEnt());
            this.valueChanged.emit();
        }
    }

    constructor() {
        super();
        this.setWindowTitle("Replace Entities");

        layout = QVBoxLayout();

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel);
        buttonBox.accepted.connect(this.accept);
        buttonBox.rejected.connect(this.reject);

        cols = QHBoxLayout();

        function genEnt(name) {
            spinners = ReplaceDialog.EntSpinners();
            info = QVBoxLayout();
            info.addWidget(QLabel(name));
            icon = QLabel();
            spinners.valueChanged.connect(() => icon.setPixmap(spinners.entity.pixmap));
            info.addWidget(icon);
            infoWidget = QWidget();
            infoWidget.setLayout(info);
            return [ infoWidget, spinners ];
        }

        [ fromInfo, this.fromEnt ] = genEnt("From");
        [ toInfo, this.toEnt ] = genEnt("To");

        selection = mainWindow.scene.selectedItems();
        if (selection.length > 0) {
            selection = selection[0].entity;
            this.fromEnt.setEnt(+selection.Type, +selection.Variant, +selection.Subtype);
        }
        else {
            this.fromEnt.resetEnt();
        }

        paint = mainWindow.editor.objectToPaint;
        if (paint) {
            this.toEnt.setEnt(int(paint.ID), int(paint.variant), int(paint.subtype));
        }
        else {
            this.toEnt.resetEnt();
        }

        cols.addWidget(fromInfo);
        cols.addWidget(this.fromEnt);
        cols.addWidget(toInfo);
        cols.addWidget(this.toEnt);

        layout.addLayout(cols);
        layout.addWidget(buttonBox);
        this.setLayout(layout);
    }
}

class HooksDialog extends QDialog {
    class HookItem extends QListWidgetItem {
        constructor(this, text, setting, tooltip) {
            super(text);
            this.setToolTip(tooltip);
            this.setting = setting;
        }

        get val() {
            settings = QSettings("settings.ini", QSettings.IniFormat);
            return settings.value(this.setting, []);
        }

        set val(v) {
            settings = QSettings("settings.ini", QSettings.IniFormat);
            res = v;
            if (v === undefined) {
                settings.remove(this.setting);
            }
            else {
                settings.setValue(this.setting, res);
            }
        }
    }

    constructor(parent) {
        super(parent);
        this.setWindowTitle("Set Hooks");

        this.layout = QHBoxLayout();

        hookTypes = [
            [
                "On Save File",
                "HooksSave",
                "Runs on saved room files whenever a full save === performed",
            ],
            [
                "On Test Room",
                "HooksTest",
                "Runs on output room xmls when preparing to test the current room",
            ],
        ];

        this.hooks = QListWidget();
        for (hook of hookTypes) {
            this.hooks.addItem(HooksDialog.HookItem(...hook));
        }
        this.layout.addWidget(this.hooks);

        pane = QVBoxLayout();
        pane.setContentsMargins(0, 0, 0, 0);
        paneWidget = QWidget();
        paneWidget.setLayout(pane);

        this.content = QListWidget();
        pane.addWidget(this.content);

        addButton = QPushButton("Add");
        editButton = QPushButton("Edit");
        deleteButton = QPushButton("Delete");

        buttons = QHBoxLayout();
        buttons.addWidget(addButton);
        buttons.addWidget(editButton);
        buttons.addWidget(deleteButton);
        pane.addLayout(buttons);

        this.layout.addWidget(paneWidget, 1);

        this.hooks.currentItemChanged.connect(this.displayHook);

        addButton.clicked.connect(this.addPath);
        editButton.clicked.connect(this.editPath);
        deleteButton.clicked.connect(this.deletePath);

        this.setLayout(this.layout);
    }

    contentPaths() {
        return [ this.content.item(i).text() for i of range(this.content.count()) ] || undefined;
    }

    setPaths(val) {
        this.content.clear();
        if (!val) {
            return;
        }
        this.content.addItems(val);
    }

    displayHook(new, old) {
        if (old) {
            old.val = this.contentPaths();
        }
        this.setPaths(new.val);
    }

    insertPath(path=findModsPath()) {
        [ target ] = QFileDialog.getOpenFileName(this, "Select script", os.path.normpath(path), "All files (*)");
        return target;
    }

    addPath() {
        path = this.insertPath();
        if (path !== "") {
            this.content.addItem(path);
        }
    }

    editPath() {
        item = this.content.currentItem();
        if (!item) {
            return;
        }

        path = this.insertPath(item.text());
        if (path !== "") {
            item.setText(path);
        }
    }

    deletePath() {
        if (this.content.currentItem()) {
            this.content.takeItem(this.content.currentRow());
        }
    }

    closeEvent(evt) {
        current = this.hooks.currentItem();
        if (current) {
            current.val = this.contentPaths();
        }
        QWidget.closeEvent(this, evt);
    }
}

class TestConfigDialog extends QDialog {
    class ConfigItem extends QLabel {
        constructor(text, setting, tooltip, def=undefined) {
            super(text);
            this.setToolTip(tooltip);
            this.setting = setting;
            this.default = def;
        }

        get val() {
            settings = QSettings("settings.ini", QSettings.IniFormat);
            return settings.value(this.setting, this.default);
        }

        set val(v) {
            settings = QSettings("settings.ini", QSettings.IniFormat);
            res = v;
            if (v === undefined) {
                settings.remove(this.setting);
            }
            else {
                settings.setValue(this.setting, res);
            }
        }
    }

    constructor(parent) {
        super(parent);
        this.setWindowTitle("Test Configuration");

        this.layout = QVBoxLayout();

        version = getGameVersion();

        // character
        characterLayout = QHBoxLayout();
        this.characterConfig = TestConfigDialog.ConfigItem(
            "Character",
            "TestCharacter",
            "Character to switch to when testing. (Isaac, Magdalene, etc.) if omitted, use the game's default",
        );
        this.characterEntry = QLineEdit();
        characterLayout.addWidget(this.characterConfig);
        characterLayout.addWidget(this.characterEntry);
        characterWidget = QWidget();
        characterWidget.setLayout(characterLayout);
        if (!["Repentance"].includes(version)) {
            characterWidget.setEnabled(false);
        }
        this.layout.addWidget(characterWidget);

        // commands
        commandLayout = QVBoxLayout();
        this.commandConfig = TestConfigDialog.ConfigItem(
            "Debug Commands",
            "TestCommands",
            "Debug Console Commands that will get run one at a time after other BR initialization has finished",
            [],
        );
        pane = QVBoxLayout();
        pane.setContentsMargins(0, 0, 0, 0);
        paneWidget = QWidget();
        paneWidget.setLayout(pane);

        this.commandList = QListWidget();
        pane.addWidget(this.commandList);

        addButton = QPushButton("Add");
        editButton = QPushButton("Edit");
        deleteButton = QPushButton("Delete");

        buttons = QHBoxLayout();
        buttons.addWidget(addButton);
        buttons.addWidget(deleteButton);
        pane.addLayout(buttons);

        commandLayout.addWidget(this.commandConfig);
        commandLayout.addWidget(paneWidget);

        commandWidget = QWidget();
        commandWidget.setLayout(commandLayout);

        this.layout.addWidget(commandWidget, 1);

        // enable/disable
        enableLayout = QHBoxLayout();
        this.enableConfig = TestConfigDialog.ConfigItem(
            "Enabled",
            "TestConfigDisabled",
            "Enable/disable the test config bonus settings",
        );
        this.enableCheck = QCheckBox("Enabled");
        this.enableCheck.setToolTip(this.enableConfig.toolTip());
        enableLayout.addWidget(this.enableCheck);
        enableWidget = QWidget();
        enableWidget.setLayout(enableLayout);
        this.layout.addWidget(enableWidget);

        addButton.clicked.connect(this.addCommand);
        deleteButton.clicked.connect(this.deleteCommand);

        this.setValues();

        this.setLayout(this.layout);
    }

    enabled() {
        return this.enableCheck.isChecked() ? undefined : "1";
    }

    character() {
        return this.characterEntry.text() || undefined;
    }

    commands() {
        return [ this.commandList.item(i).text() for i of range(this.commandList.count()) ] || undefined;
    }

    setValues() {
        this.enableCheck.setChecked(this.enableConfig.val !== "1");
        this.characterEntry.setText(this.characterConfig.val);
        this.commandList.clear();
        this.commandList.addItems(this.commandConfig.val);
        for (const i of range(this.commandList.count())) {
            item = this.commandList.item(i);
            item.setFlags(item.flags() | Qt.ItemIsEditable);
        }
    }

    addCommand() {
        item = QListWidgetItem("combo 2");
        item.setFlags(item.flags() | Qt.ItemIsEditable);
        this.commandList.addItem(item);
    }

    deleteCommand() {
        if (this.commandList.currentItem()) {
            this.commandList.takeItem(this.commandList.currentRow());
        }
    }

    closeEvent(evt) {
        this.enableConfig.val = this.enabled();
        this.characterConfig.val = this.character();
        this.commandConfig.val = this.commands();
        QWidget.closeEvent(this, evt);
    }
}

class FilterDialog extends QDialog {
    class FilterEntry extends QWidget {
        constructor(roomList, text, key, EntryType=QLineEdit, ConversionType=parseInt) {
            super();
            this.setContentsMargins(0, 0, 0, 0);

            this.layout = QVBoxLayout();

            this.enabledToggle = QCheckBox(text);
            this.roomList = roomList;
            this.key = key;
            this.rangeEnabled = QCheckBox("Use Range");
            this.minVal = EntryType();
            this.maxVal = EntryType();
            this.conversionType = ConversionType;

            this.layout.addWidget(this.enabledToggle);

            tweaks = QHBoxLayout();
            tweaks.addWidget(this.minVal);
            tweaks.addWidget(this.rangeEnabled);
            tweaks.addWidget(this.maxVal);
            this.layout.addLayout(tweaks);

            this.setVals();

            this.enabledToggle.stateChanged.connect(this.updateVals);
            this.rangeEnabled.stateChanged.connect(this.updateVals);
            this.minVal.editingFinished.connect(this.updateVals);
            this.maxVal.editingFinished.connect(this.updateVals);

            this.setLayout(this.layout);
        }

        setVals() {
            filterData = this.roomList.filter.extraData[this.key];
            minVal = filterData.min;
            maxVal = filterData.max;
            if (this.minVal instanceof QLineEdit) {
                this.minVal.setText(minVal.toString());
                this.maxVal.setText(maxVal.toString());
            }
            else if (this.minVal instanceof QDateTimeEdit) {
                this.minVal.setDateTime(minVal.astimezone());
                this.maxVal.setDateTime(maxVal.astimezone());
            }

            this.enabledToggle.setChecked(filterData.enabled);
            this.rangeEnabled.setChecked(filterData.useRange);
        }

        updateVals() {
            filterData = this.roomList.filter.extraData[this.key];
            minVal = undefined;
            maxVal = undefined;
            if (this.minVal instanceof QLineEdit) {
                minVal = this.conversionType(this.minVal.text());
                maxVal = this.conversionType(this.maxVal.text());
            }
            else if (this.minVal instanceof QDateTimeEdit) {
                minVal = this.minVal.dateTime().toPyDateTime().astimezone(datetime.timezone.utc);
                maxVal = this.maxVal.dateTime().toPyDateTime().astimezone(datetime.timezone.utc);
            }

            filterData.min = minVal;
            filterData.max = maxVal;
            filterData.enabled = this.enabledToggle.isChecked();
            filterData.useRange = this.rangeEnabled.isChecked();
        }
    }

    class TagFilterEntry extends QWidget {
        class TagFilterListItem extends QListWidgetItem {
            constructor(config) {
                super(config.label ?? config.tag);
                this.config = config;
            }
        }

        constructor(roomList) {
            super();

            this.roomList = roomList;

            this.layout = QVBoxLayout();

            buttons = QHBoxLayout();

            this.enabledToggle = QCheckBox("Tags");

            modeGroup = QButtonGroup();
            this.anyModeToggle = QRadioButton("Any");
            this.exclusiveModeToggle = QRadioButton("Exclusive");
            this.blacklistModeToggle = QRadioButton("Blacklist");

            modeGroup.addButton(this.anyModeToggle);
            modeGroup.addButton(this.exclusiveModeToggle);
            modeGroup.addButton(this.blacklistModeToggle);

            buttons.addWidget(this.enabledToggle);
            buttons.addWidget(this.anyModeToggle);
            buttons.addWidget(this.exclusiveModeToggle);
            buttons.addWidget(this.blacklistModeToggle);
            this.layout.addLayout(buttons);

            this.tagsList = QListWidget();
            for (const tag of xmlLookups.entities.tags.values()) {
                if (tag.filterable) {
                    tagItem = FilterDialog.TagFilterEntry.TagFilterListItem(tag);
                    tagItem.setFlags(tagItem.flags() | Qt.ItemIsUserCheckable);
                    tagItem.setCheckState(Qt.Unchecked);
                    this.tagsList.addItem(tagItem);
                }
            }

            this.setVals();

            this.tagsList.itemChanged.connect(this.updateVals);
            this.enabledToggle.toggled.connect(this.updateVals);
            this.anyModeToggle.toggled.connect(this.updateVals);
            this.exclusiveModeToggle.toggled.connect(this.updateVals);
            this.blacklistModeToggle.toggled.connect(this.updateVals);

            this.layout.addWidget(this.tagsList);
            this.setLayout(this.layout);
        }

        setVals() {
            filterData = this.roomList.filter.extraData.tags;
            this.enabledToggle.setChecked(filterData.enabled);
            this.anyModeToggle.setChecked(filterData.mode === "Any");
            this.exclusiveModeToggle.setChecked(filterData.mode === "Exclusive");
            this.blacklistModeToggle.setChecked(filterData.mode === "Blacklist");

            for (const row of range(this.tagsList.count())) {
                item = this.tagsList.item(row);
                item.setCheckState(filterData.tags.includes(item.config.tag) ? Qt.Checked : Qt.Unchecked);
            }
        }

        updateVals() {
            filterData = this.roomList.filter.extraData.tags;
            filterData.enabled = this.enabledToggle.isChecked();
            if (this.anyModeToggle.isChecked()) {
                filterData.mode = "Any";
            }
            else if (this.exclusiveModeToggle.isChecked()) {
                filterData.mode = "Exclusive";
            }
            else if (this.blacklistModeToggle.isChecked()) {
                filterData.mode = "Blacklist";
            }

            checkedTags = [];
            for (const row of range(this.tagsList.count())) {
                item = this.tagsList.item(row);
                if (item.checkState() === Qt.Checked) {
                    checkedTags.push(item.config.tag);
                }
            }

            filterData.tags = checkedTags;
        }
    }

    constructor(parent) {
        super(parent);
        this.setWindowTitle("Room Filter Configuration");

        this.roomList = parent;
        roomList = this.roomList;

        this.layout = QVBoxLayout();

        this.weightEntry = FilterDialog.FilterEntry(roomList, "Weight", "weight", ConversionType=parseFloat);
        this.layout.addWidget(this.weightEntry);

        this.difficultyEntry = FilterDialog.FilterEntry(roomList, "Difficulty", "difficulty");
        this.layout.addWidget(this.difficultyEntry);

        this.subtypeEntry = FilterDialog.FilterEntry(roomList, "SubType", "subtype");
        this.layout.addWidget(this.subtypeEntry);

        ltt = roomList.filter.extraData.lastTestTime;
        if (!ltt.min) {
            ltt.min = new Date();
            ltt.max = ltt.min.addDays(-30);
        }

        this.lastTestTimeEntry = FilterDialog.FilterEntry(roomList, "Last Test Time", "lastTestTime", EntryType=QDateTimeEdit);
        this.lastTestTimeEntry.setToolTip(
            "if no range, searches for never tested rooms and rooms before this date-time. Else searches for rooms tested within the range, starting from the righthand datetime"
        );
        this.layout.addWidget(this.lastTestTimeEntry);

        this.tagsEntry = FilterDialog.TagFilterEntry(roomList);
        this.layout.addWidget(this.tagsEntry);

        this.setLayout(this.layout);
    }

    closeEvent(evt) {
        this.roomList.setExtraFilter(undefined, force=true);
        this.roomList.changeFilter();
        QWidget.closeEvent(this, evt);
    }
}

class StatisticsDialog extends QDialog {
    class EntityStatisticsEntry {
        class EntityStatItem extends QTableWidgetItem {
            constructor(entry, property, formatAsPercent=false) {
                super();
                this.entry = entry;
                this.property = property;
                this.sortValue = this.entry[this.property];
                this.formatAsPercent = formatAsPercent;
                this.setFlags(Qt.ItemIsEnabled);
            }

            __lt__(otherItem) {
                if (this.sortValue !== undefined &&
                    otherItem instanceof StatisticsDialog.EntityStatisticsEntry.EntityStatItem &&
                    otherItem.sortValue !== undefined) {
                    return this.sortValue < otherItem.sortValue;
                }
                else {
                    return super(QTableWidgetItem, this).__lt__(otherItem);
                }
            }

            updateValue() {
                this.sortValue = this.entry[this.property];
                if (this.formatAsPercent) {
                    this.setText(":{.2%}".format(this.sortValue));
                }
                else {
                    this.setText(Math.round(this.sortValue, 2).toString());
                }
            }
        }

        constructor(parent, config=EntityLookup.EntityConfig, tag=undefined) {
            this.parent = parent;
            this.table = this.parent.statisticsTable;
            this.config = config;
            this.tag = tag;
            this.includedintag = false;

            this.appearCount = 0;
            this.appearPercent = 0;
            this.averageDifficulty = 0;
            this.averageWeight = 0;

            this.rooms = [];

            this.pixmap = QPixmap(config.imagePath);

            this.table.insertRow(0);
            this.nameWidget = QTableWidgetItem();
            this.nameWidget.setFlags(Qt.ItemIsEnabled);

            if (this.tag) {
                this.nameWidget.setText(this.tag.label ?? this.tag.tag);
            }
            else {
                this.nameWidget.setText(this.config.name);
            }

            this.nameWidget.setIcon(QIcon(this.pixmap));
            this.table.setItem(0, 0, this.nameWidget);

            this.propertyWidgets = [];
            properties = [
                "appearCount",
                "appearPercent",
                "averageDifficulty",
                "averageWeight",
            ];
            column = 1;
            for (const property of properties) {
                widget = StatisticsDialog.EntityStatisticsEntry.EntityStatItem(this, property, property === "appearPercent");
                this.table.setItem(0, column, widget);
                this.propertyWidgets.push(widget);
                column++;
            }
        }

        updateWidgets(overallStats, filter, useAverage) {
            roomStats = this.parent.getStatsForRooms(this.rooms, filter);

            this.appearCount = roomStats.Count;
            if (overallStats.SumWeight > 0) {
                this.appearPercent = roomStats.SumWeight / overallStats.SumWeight;
            }
            else {
                this.appearPercent = 0;
            }

            if (useAverage) {
                this.averageDifficulty = roomStats.AverageDifficulty;
                this.averageWeight = roomStats.AverageWeight;
            }
            else {
                this.averageDifficulty = roomStats.ModeDifficulty;
                this.averageWeight = roomStats.ModeWeight;
            }

            for (const widget of this.propertyWidgets) {
                widget.updateValue();
            }

            hidden = this.appearCount < filter.AppearCountThreshold;
            if (filter.CombatEntitiesOnly) {
                hidden = hidden || this.config.matches(tags=["InNonCombatRooms"]);
            }
            if (filter.GroupSimilarEntities) {
                hidden = hidden || this.includedintag;
            }
            else {
                hidden = hidden || this.tag !== undefined;
            }

            this.table.setRowHidden(this.nameWidget.row(), hidden);
        }
    }

    constructor(parent, roomList=RoomSelector) {
        super(parent);
        this.setWindowTitle("Room Statistics");

        this.roomList = roomList;

        this.layout = QVBoxLayout();

        generalStatsBox = QGroupBox("General Stats");
        generalStatsBoxLayout = QVBoxLayout();
        this.generalStatsLabel = QLabel();
        generalStatsBoxLayout.addWidget(this.generalStatsLabel);
        generalStatsBox.setLayout(generalStatsBoxLayout);
        this.layout.addWidget(generalStatsBox);

        filterBox = QGroupBox("Filter");
        filterBoxLayout = QVBoxLayout();

        generalFilterCheckBoxesLayout = QHBoxLayout();
        this.selectedRoomsToggle = QCheckBox("Selected Rooms");
        this.selectedRoomsToggle.setToolTip(
            "if checked, statistics are only evaluated for selected rooms\nif you have no rooms selected, has no effect."
        );
        this.selectedRoomsToggle.toggled.connect(this.refresh);
        generalFilterCheckBoxesLayout.addWidget(this.selectedRoomsToggle);
        this.combatEntityToggle = QCheckBox("Combat Entities");
        this.combatEntityToggle.setToolTip(
            "if checked, hides non-combat related entities, like grids and pickups";
        );
        this.combatEntityToggle.toggled.connect(this.refresh);
        generalFilterCheckBoxesLayout.addWidget(this.combatEntityToggle);
        this.forceIndividualEntitiesToggle = QCheckBox("Force Individual Entities");
        this.forceIndividualEntitiesToggle.setToolTip(
            "Forces each entity entry to get its own row, rather than combining variants of the same entity"
        );
        this.forceIndividualEntitiesToggle.toggled.connect(this.refresh);
        generalFilterCheckBoxesLayout.addWidget(this.forceIndividualEntitiesToggle);
        this.modeAverageToggle = QCheckBox("Show Averages");
        this.modeAverageToggle.setToolTip(
            "if checked, displays the average difficulty / weight of the rooms each entity is in, rather than the most common"
        );
        this.modeAverageToggle.toggled.connect(this.refresh);
        generalFilterCheckBoxesLayout.addWidget(this.modeAverageToggle);
        filterBoxLayout.addLayout(generalFilterCheckBoxesLayout);

        difficultyFilterBox = QGroupBox("Room Difficulty");
        difficultyFilterBoxLayout = QHBoxLayout();
        this.difficultyCheckboxes = [];
        filterableDifficulties = [ 1, 5, 10, 15, 20 ];
        for (const difficulty of filterableDifficulties) {
            checkbox = QCheckBox(str(difficulty));
            checkbox.setChecked(true);
            checkbox.toggled.connect(this.refresh);
            this.difficultyCheckboxes.push(checkbox);
            difficultyFilterBoxLayout.addWidget(checkbox);
        }
        difficultyFilterBox.setLayout(difficultyFilterBoxLayout);
        filterBoxLayout.addWidget(difficultyFilterBox);

        appearCountThresholdLabel = QLabel("Appear Count Threshold:");
        filterBoxLayout.addWidget(appearCountThresholdLabel);

        this.appearCountThresholdSpinner = QSpinBox();
        this.appearCountThresholdSpinner.setRange(1, (2**31) - 1);
        this.appearCountThresholdSpinner.valueChanged.connect(this.refresh);
        filterBoxLayout.addWidget(this.appearCountThresholdSpinner);

        filterBox.setLayout(filterBoxLayout);
        this.layout.addWidget(filterBox);

        entityStatsBox = QGroupBox("Entity Stats");
        entityStatsBoxLayout = QVBoxLayout();
        this.statsEntries = [];
        this.statisticsTable = QTableWidget();
        this.statisticsTable.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents);
        entityStatsBoxLayout.addWidget(this.statisticsTable);
        entityStatsBox.setLayout(entityStatsBoxLayout);
        this.layout.addWidget(entityStatsBox);

        this.populateTable();

        this.setLayout(this.layout);

        this.adjustSize();
    }

    getStatsForRooms(rooms, roomFilter=undefined) {
        count = 0;
        sumRoomDifficulties = 0;
        sumRoomWeights = 0;
        difficulties = {}
        weights = {}
        for (room of rooms) {
            if (roomFilter) {
                if (!roomFilter.AllowedDifficulties.includes(room.difficulty)) {
                    continue;
                }
                if (roomFilter.Rooms) {
                    if (!roomFilter.Rooms.includes(room)) {
                        continue;
                    }
                }
            }

            count++;
            sumRoomDifficulties += room.difficulty;
            sumRoomWeights += room.weight;

            if (!difficulties.includes(room.difficulty)) {
                difficulties[room.difficulty] = 0;
            }

            difficulties[room.difficulty]++;

            if (!weights.includes(room.weight)) {
                weights[room.weight] = 0;
            }

            weights[room.weight]++;
        }

        if (count === 0) {
            return {
                Count: 0,
                SumDifficulty: 0,
                AverageDifficulty: 0,
                ModeDifficulty: 0,
                SumWeight: 0,
                AverageWeight: 0,
                ModeWeight: 0,
            };
        }

        return {
            Count: count,
            SumDifficulty: sumRoomDifficulties,
            AverageDifficulty: sumRoomDifficulties / count,
            ModeDifficulty: Math.max(difficulties, key=difficulties.get),
            SumWeight: sumRoomWeights,
            AverageWeight: sumRoomWeights / count,
            ModeWeight: Math.max(weights, key=weights.get),
        };
    }

    populateTable() {
        this.statisticsTable.setSortingEnabled(false);
        this.statisticsTable.clear();
        this.statisticsTable.setColumnCount(5);

        // if (this.roomList.selectedRooms().length > 0) {
        //    rooms = this.roomList.orderedSelectedRooms()

        rooms = this.roomList.getRooms();

        overallStats = this.getStatsForRooms(rooms);
        this.generalStatsLabel.setText(`Rooms: ${overallStats.Count}
Most Common Difficulty: ${overallStats.ModeDifficulty} (average: ${Math.round(overallStats.AverageDifficulty, 2)})
Most Common Weight: ${overallStats.ModeWeight} (average: ${Math.round(overallStats.AverageWeight, 2)})`
        );

        entities = {}
        tags = {}
        this.statsEntries = [];
        for (const room of rooms) {
            for (const config of room.palette.values()) {
                if (!(config.uniqueid in entities)) {
                    entities[config.uniqueid] = StatisticsDialog.EntityStatisticsEntry(this, config);
                    this.statsEntries.push(entities[config.uniqueid]);
                }

                for (const tag of config.tags.values()) {
                    if (tag.statisticsgroup) {
                        if (!(tag.tag in tags)) {
                            tags[tag.tag] = StatisticsDialog.EntityStatisticsEntry(this, config, tag);
                            this.statsEntries.push(tags[tag.tag]);
                        }

                        if (tags[tag.tag].rooms.has(room)) {
                            tags[tag.tag].rooms.add(room);
                        }

                        entities[config.uniqueid].includedintag = true;
                    }
                }

                entities[config.uniqueid].rooms.push(room);
            }
        }

        this.refresh();

        this.statisticsTable.setSortingEnabled(true);
        this.statisticsTable.sortItems(1, Qt.DescendingOrder);
        this.statisticsTable.verticalHeader().hide();
        this.statisticsTable.resizeColumnsToContents();
    }

    refresh() {
        rooms = this.roomList.getRooms();

        roomFilter = {
            AllowedDifficulties: {},
            Rooms: false,
            AppearCountThreshold: this.appearCountThresholdSpinner.value(),
            CombatEntitiesOnly: this.combatEntityToggle.isChecked(),
            GroupSimilarEntities: !this.forceIndividualEntitiesToggle.isChecked(),
        };

        if (this.selectedRoomsToggle.isChecked() && this.roomList.selectedRooms().length > 0) {
            rooms = this.roomList.selectedRooms();
            roomFilter.Rooms = rooms;
        }

        for (const checkbox of this.difficultyCheckboxes) {
            if (checkbox.isChecked()) {
                roomFilter.AllowedDifficulties[parseInt(checkbox.text())] = true;
            }
        }

        filteredStats = this.getStatsForRooms(rooms, roomFilter);

        for (const stats of this.statsEntries) {
            stats.updateWidgets(filteredStats, roomFilter, this.modeAverageToggle.isChecked());
        }

        if (this.modeAverageToggle.isChecked()) {
            this.statisticsTable.setHorizontalHeaderLabels([
                "Entity",
                "Room Count",
                "Appear Chance",
                "Average Difficulty",
                "Average Weight",
            ]);
        }
        else {
            this.statisticsTable.setHorizontalHeaderLabels([
                "Entity",
                "Room Count",
                "Appear Chance",
                "Common Difficulty",
                "Common Weight",
            ]);
        }
    }
}

//////////////////////////
//      Main Window     //
//////////////////////////

class MainWindow extends QMainWindow {
    keyPressEvent(event) {
        super.keyPressEvent(event);
        if (event.key() === Qt.Key_Alt) {
            this.roomList.mirrorButtonOn();
        }
        if (event.key() === Qt.Key_Shift) {
            this.roomList.mirrorYButtonOn();
        }
    }

    keyReleaseEvent(event) {
        super.keyReleaseEvent(event);
        if (event.key() === Qt.Key_Alt) {
            this.roomList.mirrorButtonOff();
        }
        if (event.key() === Qt.Key_Shift) {
            this.roomList.mirrorYButtonOff();
        }
    }

    constructor() {
        super();

        this.setWindowTitle("Basement Renovator");
        this.setIconSize(QSize(16, 16));

        this.#path = undefined;

        this.dirty = false;

        this.wroteModFolder = false;
        this.disableTestModTimer = undefined;

        this.scene = RoomScene(this);

        this.clipboard = undefined;
        this.setAcceptDrops(true);

        this.editor = RoomEditorWidget(this.scene);
        this.setCentralWidget(this.editor);

        this.fixupLookups();

        this.setupDocks();
        this.setupMenuBar();
        this.setupStatusBar();

        this.setGeometry(100, 500, 1280, 600);

        this.restoreState(settings.value("MainWindowState", this.saveState()), 0);
        this.restoreGeometry(settings.value("MainWindowGeometry", this.saveGeometry()));

        this.resetWindow = { state: this.saveState(), geometry: this.saveGeometry() };

        // Setup a new map
        this.newMap();
        this.clean();
    }

    get path() {
        return this.#path;
    }

    set path(val) {
        oldPath = this.path;
        this.#path = val;
        if (this.path !== oldPath) {
            this.updateTitlebar();
        }
    }

    dragEnterEvent(evt) {
        if (evt.mimeData().hasFormat("text/uri-list")) {
            evt.setAccepted(true);
        }
    }

    dropEvent(evt) {
        files = evt.mimeData().text().split("\n");
        s = files[0];
        target = urllib.request.url2pathname(urllib.parse.urlparse(s).path);
        this.openWrapper(target);
        evt.acceptProposedAction();
    }

    static FIXUP_PNGS = [
        "resources/UI/",
        "resources/Entities/5.100.0 - Collectible.png",
        "resources/Backgrounds/Door.png",
        "resources/Backgrounds/DisabledDoor.png",
        "resources/Entities/questionmark.png",
    ];

    fixupLookups() {
        fixIconFormat = settings.value("FixIconFormat") === "1";
        if (!fixIconFormat) {
            return;
        }

        savedPaths = {}

        function fixImage(path) {
            if (!(path in savedPaths)) {
                savedPaths[path] = true;
                formatFix = QImage(path);
                formatFix.save(path);
            }
        }

        for (const fixupPath of MainWindow.FIXUP_PNGS) {
            dirPath = Path(fixupPath);
            if (dirPath.is_dir()) {
                for (const dirPath, dirNames, filenames of os.walk(dirPath)) {
                    for (const filename of filenames) {
                        path = os.path.join(dirPath, filename);
                        fixPath = Path(path);
                        if (fixPath.is_file() && fixPath.suffix === ".png") {
                            fixImage(path);
                        }
                    }
                }
            }
            else if (dirPath.is_file() && dirPath.suffix === ".png") {
                fixImage(fixupPath);
            }
            else {
                printf(`${fixupPath} is not a valid directory or png file`);
            }
        }

        entities = xmlLookups.entities.lookup();
        for (const config of entities) {
            if (config.imagePath) {
                fixImage(config.imagePath);
            }
            if (config.editorImagePath) {
                fixImage(config.editorImagePath);
            }
        }

        nodes = xmlLookups.stages.lookup();
        nodes.extend(xmlLookups.roomTypes.lookup());

        for (const node of nodes) {
            gfxs = node.findall("Gfx");
            if (node.get("BGPrefix") !== undefined) {
                gfx.push(node);
            }

            for (const gfx of gfxs) {
                for (const [ key, imgPath ] of xmlLookups.getGfxData(gfx).Paths.entries()) {
                    if (imgPath && os.path.isfile(imgPath)) {
                        fixImage(imgPath);
                    }
                }

                for (const ent of gfx.findall("Entity")) {
                    imgPath = ent.get("Image");
                    if (imgPath && os.path.isfile(imgPath)) {
                        fixImage(imgPath);
                    }
                }
            }
        }
    }

    setupFileMenuBar() {
        f = this.fileMenu;

        f.clear();
        this.fa = f.addAction("New", this.newMap, QKeySequence("Ctrl+N"));
        this.fc = f.addAction("Open (XML)...", this.openMap, QKeySequence("Ctrl+O"));
        this.fm = f.addAction("Import (STB)...", this.importMap, QKeySequence("Ctrl+Shift+O"));
        this.fb = f.addAction("Open/Import by Stage", this.openMapDefault, QKeySequence("Ctrl+Alt+O"));
        f.addSeparator();
        this.fd = f.addAction("Save", this.saveMap, QKeySequence("Ctrl+S"));
        this.fe = f.addAction("Save As...", this.saveMapAs, QKeySequence("Ctrl+Shift+S"));
        this.fk = f.addAction("Export to STB", () => this.exportSTB(), QKeySequence("Shift+Alt+S"));
        this.fk = f.addAction("Export to STB (Rebirth)", () => this.exportSTB(stbType="Rebirth"));
        f.addSeparator();
        this.fk = f.addAction("Copy Screenshot to Clipboard", () => this.screenshot("clipboard"), QKeySequence("F10"));
        this.fg = f.addAction("Save Screenshot to File...", () => this.screenshot("file"), QKeySequence("Ctrl+F10"));
        f.addSeparator();
        this.fh = f.addAction("Set Resources Path", this.setDefaultResourcesPath, QKeySequence("Ctrl+Shift+P"));
        this.fi = f.addAction("Reset Resources Path", this.resetResourcesPath, QKeySequence("Ctrl+Shift+R"));
        f.addSeparator();
        this.fj = f.addAction("Set Hooks", this.showHooksMenu);
        this.fl = f.addAction("Autogenerate mod content (discouraged)", () => this.toggleSetting("ModAutogen"));
        this.fl.setCheckable(true);
        this.fl.setChecked(settings.value("ModAutogen") === "1");
        f.addSeparator();

        recent = settings.value("RecentFiles", []);
        for (const r of recent) {
            f.addAction(os.path.normpath(r), this.openRecent).setData(r);
        }

        f.addSeparator();

        this.fj = f.addAction("Exit", this.close, QKeySequence.Quit);
    }

    setupMenuBar() {
        mb = this.menuBar();

        this.fileMenu = mb.addMenu("&File");
        this.setupFileMenuBar();

        this.e = mb.addMenu("Edit");
        this.ea = this.e.addAction("Copy", this.copy, QKeySequence.Copy);
        this.eb = this.e.addAction("Cut", this.cut, QKeySequence.Cut);
        this.ec = this.e.addAction("Paste", this.paste, QKeySequence.Paste);
        this.ed = this.e.addAction("Select All", this.selectAll, QKeySequence.SelectAll);
        this.ee = this.e.addAction("Deselect", this.deSelect, QKeySequence("Ctrl+D"));
        this.e.addSeparator();
        this.ef = this.e.addAction("Clear Filters", this.roomList.clearAllFilter, QKeySequence("Ctrl+K"));
        this.eg = this.e.addAction("Pin Entity Filter", () => this.toggleSetting("PinEntityFilter"), QKeySequence("Ctrl+Alt+K"));
        this.eg.setCheckable(true);
        this.eg.setChecked(settings.value("PinEntityFilter") === "1");
        this.nonCombatFilter = this.e.addAction("Non-Combat Room Filter", () => {
            this.toggleSetting("NonCombatRoomFilter");
            this.roomList.changeFilter();
        });
        this.nonCombatFilter.setCheckable(true);
        this.nonCombatFilter.setChecked(settings.value("NonCombatRoomFilter") === "1");
        this.el = this.e.addAction("Snap to Room Boundaries", () => this.toggleSetting("SnapToBounds", onDefault=true));
        this.el.setCheckable(true);
        this.el.setChecked(settings.value("SnapToBounds") !== "0");
        this.em = this.e.addAction("Export to STB on Save (slower saves)", () => this.toggleSetting("ExportSTBOnSave"));
        this.em.setCheckable(true);
        this.em.setChecked(settings.value("ExportSTBOnSave") === "1");
        this.e.addSeparator();
        this.eh = this.e.addAction("Bulk Replace Entities", this.showReplaceDialog, QKeySequence("Ctrl+R"));
        this.ei = this.e.addAction("Sort Rooms by ID", this.sortRoomIDs);
        this.ej = this.e.addAction("Sort Rooms by Name", this.sortRoomNames);
        this.ek = this.e.addAction("Recompute Room IDs", this.recomputeRoomIDs, QKeySequence("Ctrl+B"));
        this.showStatistics = this.e.addAction("View Room Statistics", this.showStatisticsMenu);

        v = mb.addMenu("View");
        this.wa = v.addAction("Show Grid", () => this.toggleSetting("GridEnabled", onDefault=true), QKeySequence("Ctrl+G"));
        this.wa.setCheckable(true);
        this.wa.setChecked(settings.value("GridEnabled") !== "0");
        this.wg = v.addAction("Show Out of Bounds Grid", () => this.toggleSetting("BoundsGridEnabled"));
        this.wg.setCheckable(true);
        this.wg.setChecked(settings.value("BoundsGridEnabled") === "1");
        this.wh = v.addAction("Show Grid Indexes", () => this.toggleSetting("ShowGridIndex"));
        this.wh.setCheckable(true);
        this.wh.setChecked(settings.value("ShowGridIndex") === "1");
        this.wi = v.addAction("Show Grid Coordinates", () => this.toggleSetting("ShowCoordinates"));
        this.wi.setCheckable(true);
        this.wi.setChecked(settings.value("ShowCoordinates") === "1");
        v.addSeparator();
        this.we = v.addAction("Show Room Info", () => this.toggleSetting("StatusEnabled", onDefault=true), QKeySequence("Ctrl+I"));
        this.we.setCheckable(true);
        this.we.setChecked(settings.value("StatusEnabled") !== "0");
        this.wd = v.addAction("Use Bitfont Counter", () => this.toggleSetting("BitfontEnabled", onDefault=true));
        this.wd.setCheckable(true);
        this.wd.setChecked(settings.value("BitfontEnabled") !== "0");
        this.hideDuplicateEntities = v.addAction("Hide Duplicate Entities", () => {
            this.toggleSetting("HideDuplicateEntities");
            this.EntityPalette.updateTabs();
        });
        this.hideDuplicateEntities.setCheckable(true);
        this.hideDuplicateEntities.setChecked(settings.value("HideDuplicateEntities") === "1");
        v.addSeparator();
        this.wb = v.addAction("Hide Entity Painter", this.showPainter, QKeySequence("Ctrl+Alt+P"));
        this.wc = v.addAction("Hide Room List", this.showRoomList, QKeySequence("Ctrl+Alt+R"));
        this.wf = v.addAction("Reset Window Defaults", this.resetWindowDefaults);
        v.addSeparator();

        r = mb.addMenu("Test");
        this.ra = r.addAction("Test Current Room - InstaPreview", this.testMapInstapreview, QKeySequence("Ctrl+P"));
        this.rb = r.addAction("Test Current Room - Replace Stage", this.testMap, QKeySequence("Ctrl+T"));
        this.rc = r.addAction("Test Current Room - Replace Start", this.testStartMap, QKeySequence("Ctrl+Shift+T"));
        r.addSeparator();
        this.re = r.addAction("Test Configuration", this.showTestConfigMenu);
        this.rd = r.addAction("Enable Test Mod Dialog", () => this.toggleSetting("DisableTestDialog"));
        this.rd.setCheckable(true);
        this.rd.setChecked(settings.value("DisableTestDialog") !== "1");

        h = mb.addMenu("Help");
        this.ha = h.addAction("About Basement Renovator", this.aboutDialog);
        this.hb = h.addAction("Basement Renovator Documentation", this.goToHelp);
        // this.hc = h.addAction('Keyboard Shortcuts')
    }

    setupDocks() {
        this.roomList = RoomSelector();
        this.roomListDock = QDockWidget("Rooms");
        this.roomListDock.setWidget(this.roomList);
        this.roomListDock.visibilityChanged.connect(this.updateDockVisibility);
        this.roomListDock.setObjectName("RoomListDock");

        this.roomList.list.currentItemChanged.connect(this.handleSelectedRoomChanged);

        this.addDockWidget(Qt.RightDockWidgetArea, this.roomListDock);

        this.EntityPalette = EntityPalette();
        this.EntityPaletteDock = QDockWidget("Entity Palette");
        this.EntityPaletteDock.setWidget(this.EntityPalette);
        this.EntityPaletteDock.visibilityChanged.connect(this.updateDockVisibility);
        this.EntityPaletteDock.setObjectName("EntityPaletteDock");

        this.EntityPalette.objChanged.connect(this.handleObjectChanged);
        this.EntityPalette.objReplaced.connect(this.handleObjectReplaced);

        this.addDockWidget(Qt.LeftDockWidgetArea, this.EntityPaletteDock);
    }

    setupStatusBar() {
        this.statusBar = QStatusBar();
        this.statusBar.setStyleSheet("QStatusBar::item { border: undefined; }");
        tooltipElements = [
            { label: ": Select",                         icons: [[0, 0]] },
            { label: ": Move Selection",                 icons: [[64, 0]] },
            { label: ": Multi Selection",                icons: [[0, 0], [16, 16]] },
            { label: ": Replace with Palette selection", icons: [[0, 0], [32, 16]] },
            { label: ": Place Object",                   icons: [[32, 0]] },
            {
                label: ": Edit Spike&Chain + Fissure spawner properties",
                icons: [[16, 0]],
            },
        ];

        q = QImage();
        q.load("resources/UI/uiIcons.png");
        for (const infoObj of tooltipElements) {
            for (const subicon of infoObj["icons"]) {
                iconObj = QLabel();
                iconObj.setPixmap(QPixmap.fromImage(q.copy(subicon[0], subicon[1], 16, 16)));
                iconObj.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum);
                this.statusBar.addWidget(iconObj);
            }
            label = QLabel(infoObj["label"]);
            label.setContentsMargins(0, 0, 20, 0);
            label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding);
            label.setAlignment(Qt.AlignTop);
            this.statusBar.addWidget(label);
        }

        this.setStatusBar(this.statusBar);
    }

    restoreEditMenu() {
        a = this.e.actions();
        this.e.insertAction(a[1], this.ea);
        this.e.insertAction(a[2], this.eb);
        this.e.insertAction(a[3], this.ec);
        this.e.insertAction(a[4], this.ed);
        this.e.insertAction(a[5], this.ee);
    }

    updateTitlebar() {
        if (this.path === "") {
            effectiveName = "Untitled Map";
        }
        else {
            if (platform.system().includes("Windows")) {
                effectiveName = os.path.normpath(this.path);
            }
            else {
                effectiveName = os.path.basename(this.path);
            }
        }

        this.setWindowTitle(`${effectiveName} - Basement Renovator`);
    }

    checkDirty() {
        if (this.dirty === false) {
            return false;
        }

        msgBox = QMessageBox(
            QMessageBox.Warning,
            "File is not saved",
            "Completing this operation without saving could cause loss of data.",
            QMessageBox.NoButton,
            this,
        );
        msgBox.addButton("Continue", QMessageBox.AcceptRole);
        msgBox.addButton("Cancel", QMessageBox.RejectRole);
        if (msgBox.exec_() === QMessageBox.AcceptRole) {
            this.clean();
            return false;
        }

        return true;
    }

    dirt() {
        this.setWindowIcon(QIcon("resources/UI/BasementRenovator-SmallDirty.png"));
        this.dirty = true;
    }

    clean() {
        this.setWindowIcon(QIcon("resources/UI/BasementRenovator-Small.png"));
        this.dirty = false;
    }

    storeEntityList(room=this.roomList.selectedRoom()) {
        if (!room) {
            return;
        }

        spawns = room.gridSpawns.map(() => []);

        width, height = room.info.dims;

        for (const y of range(height)) {
            for (const e of this.scene.roomRows[y].childItems()) {
                spawns[Room.Info.gridIndex(e.entity.x, e.entity.y, width)].push(e);
            }
        }

        palette = {}
        for (const [ i, spawn ] of Object.entries(spawns)) {
            for (const e of spawn) {
                if (!(e.entity.config.uniqueid in palette)) {
                    palette[e.entity.config.uniqueid] = e.entity.config;
                }
            }

            spawns[i] = spawn.sort((a, b) => a.zValue - b.zValue).map(e => [
                e.entity.Type,
                e.entity.Variant,
                e.entity.Subtype,
                e.entity.weight,
            ]);
        }

        room.gridSpawns = spawns;
        room.palette = palette;
    }

    /**
     * Handler for the main window close event
     */
    closeEvent(event) {
        this.disableTestMod();

        if (this.checkDirty()) {
            event.ignore();
        }
        else {
            settings = QSettings("settings.ini", QSettings.IniFormat);

            // Save our state
            settings.setValue("MainWindowGeometry", this.saveGeometry());
            settings.setValue("MainWindowState", this.saveState(0));

            event.accept();

            app.quit();
        }
    }

    ////////////////////////
    // Slots for (Widgets //
    ////////////////////////

    handleSelectedRoomChanged(current, prev) {
        if (!current) {
            return;
        }

        // Encode the current room, just of case there are changes
        if (prev) {
            this.storeEntityList(prev);

            // Clear the current room mark
            prev.setData(100, false);
        }

        // Clear the room && reset the size
        this.scene.clear();
        this.scene.newRoomSize(current.info.shape);
        current.setRoomBG();
        this.scene.updateRoomDepth(current);

        this.editor.resizeEvent(QResizeEvent(this.editor.size(), this.editor.size()));

        // Make some doors
        current.clearDoors();

        // Spawn those entities
        for (const [ stack, x, y ] of current.spawns()) {
            for (const ent of stack) {
                e = Entity(x, y, ent[0], ent[1], ent[2], ent[3], respawning=true);
            }
        }

        // Make the current Room mark for (clearer multi-selection
        current.setData(100, true);
    }

    handleObjectChanged(entity, setFilter=true) {
        this.editor.objectToPaint = entity;
        if (setFilter) {
            this.roomList.setEntityFilter(entity);
        }
    }

    handleObjectReplaced(entity) {
        for (const item of this.scene.selectedItems()) {
            item.setData(int(entity.ID), int(entity.variant), int(entity.subtype));
            item.update();
        }

        this.dirt();
    }

    //////////////////////////
    // Slots for Menu Items //
    //////////////////////////

    // File
    ////////////////////////////////////////////////

    newMap() {
        if (this.checkDirty()) {
            return;
        }
        this.roomList.list.clear();
        this.scene.clear();
        this.path = "";

        this.dirt();
        this.roomList.changeFilter();
    }

    setDefaultResourcesPath() {
        settings = QSettings("settings.ini", QSettings.IniFormat);
        if (!settings.contains("ResourceFolder")) {
            settings.setValue("ResourceFolder", this.findResourcePath());
        }
        resPath = settings.value("ResourceFolder");
        resPathDialog = QFileDialog();
        resPathDialog.setFilter(QDir.Hidden);
        newResPath = QFileDialog.getExistingDirectory(this, "Select directory", resPath);

        if (newResPath !== "") {
            settings.setValue("ResourceFolder", newResPath);
        }
    }

    resetResourcesPath() {
        settings = QSettings("settings.ini", QSettings.IniFormat);
        settings.remove("ResourceFolder");
        settings.setValue("ResourceFolder", this.findResourcePath());
    }

    showHooksMenu() {
        hooks = HooksDialog(this);
        hooks.show();
    }

    showTestConfigMenu() {
        testConfig = TestConfigDialog(this);
        testConfig.show();
    }

    showStatisticsMenu() {
        statistics = StatisticsDialog(this, this.roomList);
        statistics.show();
    }

    openMapDefault() {
        if (this.checkDirty()) {
            return;
        }

        selectMaps = {};
        for (const x of xmlLookups.stages.lookup(baseGamePath=true)) {
            selectMaps[x.get("Name")] = x.get("BaseGamePath");
        }

        selectedMap, selectedMapOk = QInputDialog.getItem(
            this, "Map selection", "Select floor", selectMaps.keys(), 0, false
        );
        this.restoreEditMenu();

        if (!selectedMapOk) {
            return;
        }

        mapFileName = selectMaps[selectedMap] + ".stb";
        roomPath = os.path.join(
            os.path.expanduser(this.findResourcePath()), "rooms", mapFileName
        );

        if (!QFile.exists(roomPath)) {
            this.setDefaultResourcesPath();
            roomPath = os.path.join(
                os.path.expanduser(this.findResourcePath()), "rooms", mapFileName
            );
            if (!QFile.exists(roomPath)) {
                QMessageBox.warning(
                    this,
                    "Error",
                    "Failed opening stage. Make sure that the resources path is set correctly (see File menu) and that the proper STB file is present in the rooms directory.",
                );
                return;
            }
        }

        // load the xml version if (available
        xmlVer = roomPath.substr(0, roomPath.length - 3) + "xml";
        if (QFile.exists(xmlVer)) {
            roomPath = xmlVer;
        }

        this.openWrapper(roomPath);
    }

    getRecentFolder() {
        startPath = "";

        // if a file is currently open, first default to the directory that the current file is in
        if (this.path !== "") {
            dir_of_file_currently_open = os.path.dirname(this.path);
            return dir_of_file_currently_open;
        }

        settings = QSettings("settings.ini", QSettings.IniFormat);

        // Get the folder containing the last open file if you can
        // and it's not a default stage
        stagePath = os.path.join(settings.value("ResourceFolder", ""), "rooms");
        recent = settings.value("RecentFiles", []);
        for (const recPath of recent) {
            lastPath, file = os.path.split(recPath);
            if (lastPath !== stagePath) {
                startPath = lastPath;
                break;
            }
        }

        // Get the mods folder if you can, no sense looking in rooms for explicit open
        if (startPath === "") {
            modPath = findModsPath();
            if (os.path.isdir(modPath)) {
                startPath = modPath;
            }
        }

        return os.path.expanduser(startPath);
    }

    updateRecent(path) {
        recent = settings.value("RecentFiles", []);
        while (recent.count(path) > 0) {
            recent.remove(path);
        }

        recent.insert(0, path);
        while (recent.length > 10) {
            recent.pop();
        }

        settings.setValue("RecentFiles", recent);
        this.setupFileMenuBar();
    }

    openMapImpl(title, fileTypes, addToRecent=true) {
        if (this.checkDirty()) {
            return false;
        }

        target, ext = QFileDialog.getOpenFileName(this, title, this.getRecentFolder(), fileTypes);
        this.restoreEditMenu();

        // Looks like nothing was selected
        if (!target) {
            return false;
        }

        this.openWrapper(target, addToRecent=addToRecent);
        return true;
    }

    openMap() {
        this.openMapImpl("Open Room File", "XML File (*.xml)");
    }

    importMap(target=undefined) {
        // part of openWrapper re-saves the file if it was not xml
        this.openMapImpl("Import Rooms", "Stage Binary (*.stb);;TXT File (*.txt)", addToRecent=false);
    }

    openRecent() {
        if (this.checkDirty()) {
            return;
        }

        path = this.sender().data();
        this.restoreEditMenu();

        this.openWrapper(path);
    }

    openWrapper(path, addToRecent=true) {
        printf(path);
        file, ext = os.path.splitext(path);
        isXml = ext === ".xml";

        if (!isXml) {
            newPath = `${file}.xml`;
            if (os.path.exists(newPath)) {
                reply = QMessageBox.question(
                    this,
                    "Import Map",
                    `"${newPath}" already exists; importing this file will overwrite it. Are you sure you want to import?`,
                    QMessageBox.Yes | QMessageBox.No,
                );
                if (reply === QMessageBox.No) {
                    return;
                }
            }
        }

        this.path = path;

        roomFile = undefined;
        try {
            roomFile = this.open(addToRecent=addToRecent && isXml);
        }
        catch(e) {
            if (e instanceof FileNotFoundError) {
                QMessageBox.warning(this, "Error", "Failed opening rooms. The file does not exist.");
            }
            else if (e instanceof NotImplementedError) {
                printf(e);
                QMessageBox.warning(
                    this,
                    "Error",
                    "This is not a valid STB file. (e.g. Rebirth or Afterbirth format) It may be one of the prototype STB files accidentally included of the AB+ release.",
                );
            }
            else {
                printf(e);
                QMessageBox.warning(
                    this,
                    "Error",
                    `Failed opening rooms.\n${e}`,
                );
            }
        }

        if (!roomFile) {
            return;
        }

        this.roomList.list.clear();
        this.scene.clear();

        this.roomList.file = roomFile;
        for (const room of roomFile.rooms) {
            this.roomList.list.addItem(room);
        }

        this.clean();
        this.roomList.changeFilter();

        if (!isXml) {
            this.saveMap();
        }
    }

    open(path=this.path, addToRecent=true) {
        roomFile = undefined;

        ext = os.path.splitext(path)[1];
        if (ext === ".xml") {
            roomFile = StageConvert.xmlToCommon(path);
        }
        else if (ext === ".txt") {
            roomFile = StageConvert.txtToCommon(path, xmlLookups.entities);
        }
        else {
            roomFile = StageConvert.stbToCommon(path);
        }

        rooms = roomFile.rooms;

        seenSpawns = {}
        for (const room of rooms) {
            function sameDoorLocs(a, b) {
                for (const [ ad, bd ] of zip(a, b)) {
                    if (ad[0] !== bd[0] || ad[1] !== bd[1]) {
                        return false;
                    }
                }
                return true;
            }

            normalDoors = sorted(room.info.shapeData["Doors"], key=Room.DoorSortKey);
            sortedDoors = sorted(room.info.doors, key=Room.DoorSortKey);
            if (normalDoors.length !== sortedDoors.length || !sameDoorLocs(normalDoors, sortedDoors)) {
                printf(`Invalid doors of room ${room.getPrefix()}: Expected ${normalDoors}, Got ${sortedDoors}`);
            }

            for (const [ stackedEnts, ex, ey ] of room.spawns()) {
                if (!room.info.isInBounds(ex, ey)) {
                    printf(`Found entity with out of bounds spawn loc in room ${room.getPrefix()}: ${ex-1}, ${ey-1}`);
                }

                for (const ent of stackedEnts) {
                    eType, eSubtype, eVariant = ent.Type, ent.Subtype, ent.Variant;
                    if (seenSpawns.has(eType, eSubtype, eVariant)) {
                        config = xmlLookups.entities.lookupOne(eType, eVariant, eSubtype);
                        if (config === undefined || config.invalid) {
                            printf(`Room ${room.getPrefix()} has invalid entity '${
                                config === undefined ? 'UNKNOWN' : config.name
                            }'! (${eType}.${eVariant}.${eSubtype})`);
                        }
                        seenSpawns[(eType, eSubtype, eVariant)] = config === undefined || config.invalid;
                    }
                }
            }
        }

        roomFile.rooms = rooms.map((coreRoom) => {
            palette = {}
            gridSpawns = [];
            for (gridSpawn of coreRoom.gridSpawns) {
                spawns = [];
                for (spawn of gridSpawn) {
                    spawns.push([spawn.Type, spawn.Variant, spawn.Subtype, spawn.weight]);

                    config = xmlLookups.entities.lookupOne(spawn.Type, spawn.Variant, spawn.Subtype);
                    if (config && !(config.uniqueid in palette)) {
                        palette[config.uniqueid] = config;
                    }
                }

                gridSpawns.push(spawns);
            }

            r = Room(
                coreRoom.name,
                gridSpawns,
                palette,
                coreRoom.difficulty,
                coreRoom.weight,
                coreRoom.info.type,
                coreRoom.info.variant,
                coreRoom.info.subtype,
                coreRoom.info.shape,
                coreRoom.info.doors,
            );
            r.xmlProps = dict(coreRoom.xmlProps);
            r.lastTestTime = coreRoom.lastTestTime;
            return r;
        });

        // Update recent files
        if (addToRecent) { // && ext === '.xml') { // if (a non-xml was deliberately opened, add it to recent;
            this.updateRecent(path);
        }

        return roomFile;
    }

    saveMap(forceNewName=false) {
        target = this.path;

        if (!target || forceNewName) {
            dialogDir = target === "" ? this.getRecentFolder() : os.path.dirname(target);
            target, ext = QFileDialog.getSaveFileName(this, "Save Map", dialogDir, "XML (*.xml)");
            this.restoreEditMenu();

            if (!target) {
                return;
            }

            this.path = target;
        }

        try {
            this.save(this.roomList.getRooms(), fileObj=this.roomList.file, updateActive=true);
        }
        catch (e) {
            printf(e);
            QMessageBox.warning(this, "Error", "Saving failed. Try saving to a new file instead.");
        }

        this.clean();
        this.roomList.changeFilter();

        settings = QSettings("settings.ini", QSettings.IniFormat);
        if (settings.value("ExportSTBOnSave") === "1") {
            this.exportSTB();
        }
    }

    saveMapAs() {
        this.saveMap(forceNewName=true);
    }

    exportSTB(stbType=undefined) {
        target = this.path;

        if (!target) {
            this.saveMap();
            target = this.path;
        }

        try {
            target = os.path.splitext(target)[0] + ".stb";
            this.save(this.roomList.getRooms(), target, updateRecent=false, stbType=stbType);
        }
        catch (e) {
            printf(e);
            QMessageBox.warning(this, "Error", `Exporting failed.\n${e}`);
        }
    }

    save(
        rooms,
        path=os.path.splitext(this.path)[0] + ".xml",
        fileObj=undefined,
        updateActive=false,
        updateRecent=true,
        isPreview=false,
        stbType=undefined,
    ) {
        this.storeEntityList();

        function entItemToCore(e, i, w) {
            x = i % w;
            y = (i / w) | 0;
            return new EntityData(x, y, e[0], e[1], e[2], e[3]);
        }

        function roomItemToCore(room) {
            realWidth = room.info.dims[0];
            spawns = room.gridSpawns.map((stack, i) =>
                stack.map(e => entItemToCore(e, i, realWidth))
            );
            r = RoomData(
                room.name,
                spawns,
                room.difficulty,
                room.weight,
                room.info.type,
                room.info.variant,
                room.info.subtype,
                room.info.shape,
                room.info.doors,
            );
            r.xmlProps = dict(room.xmlProps);
            r.lastTestTime = room.lastTestTime;
            return r;
        }

        rooms = rooms.map(roomItemToCore);

        ext = os.path.splitext(path)[1];
        if (ext === ".xml") {
            StageConvert.commonToXML(path, rooms, file=fileObj, isPreview=isPreview);
        }
        else {
            if (stbType === "Rebirth") {
                StageConvert.commonToSTBRB(path, rooms)  // cspell: disable-line
            }
            else {
                StageConvert.commonToSTBAB(path, rooms)  // cspell: disable-line
            }
        }
        if (updateActive) {
            this.path = path;
        }

        if (updateRecent && ext === ".xml") {
            this.updateRecent(path);

            // if (a save doesn't update the recent list, it's probably !a real save
            // so only do hooks of this case
            settings = QSettings("settings.ini", QSettings.IniFormat);
            saveHooks = settings.value("HooksSave");
            if (saveHooks) {
                fullPath = os.path.abspath(path);
                for (const hook of saveHooks) {
                    path, name = os.path.split(hook);
                    try {
                        subprocess.run([hook, fullPath, "--save"], cwd=path, timeout=60);
                    }
                    catch (e) {
                        printf("Save hook failed! Reason:", e);
                    }
                }
            }
        }
    }

    replaceEntities(sreplaced, replacement) {
        this.storeEntityList();

        numEnts = 0;
        numRooms = 0;

        function checkEq(a, b) {
            return a[0] === b[0] && (b[1] < 0 || a[1] === b[1]) && (b[2] < 0 || a[2] === b[2]);
        }

        function fixEnt(a, b) {
            a[0] = b[0];
            if (b[1] >= 0) {
                a[1] = b[1];
            }
            if (b[2] >= 0) {
                a[2] = b[2];
            }
        }

        for (i of range(this.roomList.list.count())) {
            currentRoom = this.roomList.list.item(i);

            n = 0;
            for (stack, x, y of currentRoom.spawns()) {
                for (const ent of stack) {
                    if (checkEq(ent, replaced)) {
                        fixEnt(ent, replacement);
                        n += 1;
                    }
                }
            }

            if (n > 0) {
                numRooms += 1;
                numEnts += n;
            }
        }

        room = this.roomList.selectedRoom();
        if (room) {
            this.handleSelectedRoomChanged(room, undefined);
            this.scene.update();
        }

        this.dirt();
        QMessageBox.information(
            undefined,
            "Replace",
            numEnts > 0 ?
                `Replaced ${numEnts} entities of ${numRooms} rooms` :
                "No entities to replace!",
        );
    }

    sortRoomIDs() {
        this.sortRoomsByKey(x =>
            a.info.type - b.info.type ||
            a.info.variant - b.info.variant
        );
    }

    sortRoomNames() {
        this.sortRoomsByKey((a, b) =>
            a.info.type - b.info.type ||
            a.name.localeCompare(b.name) ||
            a.info.variant - b.info.variant
        );
    }

    sortRoomsByKey(less) {
        roomList = this.roomList.list;
        selection = roomList.currentItem();
        roomList.setCurrentItem(undefined, QItemSelectionModel.ClearAndSelect);

        rooms = [ roomList.takeItem(roomList.count() - 1) for x of range(roomList.count()) ].sort(less);

        for (const room of rooms) {
            roomList.addItem(room);
        }

        this.dirt();
        roomList.setCurrentItem(selection, QItemSelectionModel.ClearAndSelect);
        roomList.scrollToItem(selection);
    }

    recomputeRoomIDs() {
        roomsByType = {}

        roomList = this.roomList.list;

        for (const i of range(roomList.count())) {
            room = roomList.item(i);

            if (!(room.info.type in roomsByType)) {
                roomsByType[room.info.type] = room.info.variant;
            }

            room.info.variant = roomsByType[room.info.type];
            room.setToolTip();

            roomsByType[room.info.type]++;
        }

        this.dirt();
        this.scene.update();
    }

    screenshot(mode) {
        filename = undefined;
        if (mode === "file") {
            filename = QFileDialog.getSaveFileName(this, "Choose a new filename", "untitled.png", "Portable Network Graphics (*.png)")[0];
            if (filename === "") {
                return;
            }
        }

        g = settings.value("GridEnabled");
        settings.setValue("GridEnabled", "0");

        ScreenshotImage = QImage(
            this.scene.sceneRect().width(),
            this.scene.sceneRect().height(),
            QImage.Format_ARGB32,
        );
        ScreenshotImage.fill(Qt.transparent);

        RenderPainter = QPainter(ScreenshotImage);
        this.scene.render(
            RenderPainter, QRectF(ScreenshotImage.rect()), this.scene.sceneRect();
        );
        RenderPainter.end();

        if (mode === "file") {
            ScreenshotImage.save(filename, "PNG", 50);
        }
        else if (mode === "clipboard") {
            QApplication.clipboard().setImage(ScreenshotImage, QClipboard.Clipboard);
        }

        settings.setValue("GridEnabled", g);
    }

    getTestModPath() {
        modFolder = findModsPath();
        name = "basement-renovator-helper";
        return os.path.join(modFolder, name);
    }

    makeTestMod(forceClean?: boolean) {
        folder = this.getTestModPath();
        roomPath = os.path.join(folder, "resources", "rooms");
        contentRoomPath = os.path.join(folder, "content", "rooms");

        if ((forceClean || !mainWindow.wroteModFolder) && os.path.isdir(folder)) {
            try {
                shutil.rmtree(folder);
            }
            catch (e) {
                printf("Error clearing old mod data:", e);
            }
        }

        // delete the old files
        if (os.path.isdir(folder)) {
            dis = os.path.join(folder, "disable.it");
            if (os.path.isfile(dis)) {
                os.unlink(dis);
            }

            for (const path of [roomPath, contentRoomPath]) {
                for (let f of os.listdir(path)) {
                    f = os.path.join(path, f);
                    try {
                        if (os.path.isfile(f)) {
                            os.unlink(f);
                        }
                    }
                    catch {}
                }
            }
        }
        // otherwise, make it fresh
        else {
            try {
                shutil.copytree("./resources/modtemplate", folder);
                os.makedirs(roomPath);
                os.makedirs(contentRoomPath);
                mainWindow.wroteModFolder = true;
            }
            catch (e) {
                printf("Could not copy mod template!", e);
                return [ "", e ];
            }
        }

        return [ folder, roomPath ];
    }

    writeTestData(folder, testType, floorInfo, testRooms) {
        with open(os.path.join(folder, "roomTest.lua"), "w") as testData) {
            quot = '\\"';
            bs = "\\";
            strFix = x => `"${x.replace(bs, bs + bs).replace('"', quot)}"`;

            char = undefined;
            commands = [];
            if (settings.value("TestConfigDisabled") !== "1") {
                char = settings.value("TestCharacter");
                if (char) {
                    char = strFix(char);
                }

                commands = settings.value("TestCommands", []);
            }

            roomsStr = testRooms.map(testRoom => `\
{
    Name = ${strFix(testRoom.name)},
    Type = ${testRoom.info.type},
    Variant = ${testRoom.info.variant},
    Subtype = ${testRoom.info.subtype},
    Shape = ${testRoom.info.shape}
}
\
            `).join(",\n\t");

            testData.write(`\
return {
    TestType = ${strFix(testType)},
    Character = ${char ?? 'nil'}, -- only used in Repentance
    Commands = { ${commands.map(strFix).join(', ')} },
    Stage = ${floorInfo.get('Stage')},
    StageType = ${floorInfo.get('StageType')},
    StageName = ${strFix(floorInfo.get('Name'))},
    IsModStage = ${floorInfo.get('BaseGamePath') === undefined ? 'true' : 'false'},
    RoomFile = ${strFix(str(Path(this.path)) || 'N/A')},
    Rooms = {
    ${roomsStr}
    }
}
\
            `);
        }
    }

    disableTestMod(modPath = this.getTestModPath()) {
        if (!os.path.isdir(modPath)) {
            return;
        }

        with open(os.path.join(modPath, "disable.it"), "w") {
            pass;
        }
    }

    // Test by replacing the rooms of the relevant floor
    testMap() {
        function setup(modPath, roomsPath, floorInfo, rooms, version) {
            if (!["Afterbirth+", "Repentance"].includes(version)) {
                QMessageBox.warning(this, "Error", `Stage Replacement not supported for ${version}!`);
                throw new Error();
            }

            basePath = floorInfo.get("BaseGamePath");
            if (basePath === undefined) {
                QMessageBox.warning(this, "Error", "Custom stages cannot be tested with Stage Replacement, since they don't have a room file to replace.");
                throw new Error();
            }

            if (floorInfo.get("Name") === "Blue Womb") {
                QMessageBox.warning(this, "Error", "Blue Womb cannot be tested with Stage Replacement, since it doesn't have normal room generation.");
                throw new Error();
            }

            // Set the selected rooms to max weight, best spawn difficulty, default type, && enable all the doors
            newRooms = rooms.map(room => new Room(
                room.name,
                room.gridSpawns,
                room.palette,
                5,
                1000.0,
                1,
                room.info.variant,
                room.info.subtype,
                room.info.shape,
            ));

            // Needs a padding room if (all are skinny
            padMe = newRooms.find(testRoom => [2, 3, 5, 7].includes(testRoom.info.shape)) !== undefined;
            if (padMe) {
                newRooms.push(Room(difficulty=10, weight=0.1));
            }

            // Make a new STB with a blank room
            path = os.path.join(roomsPath, basePath + ".stb");
            this.save(newRooms, path, updateRecent=false);

            // Prompt to restore backup
            message = "This method will not work properly if you have other mods that add rooms to the floor.";
            if (padMe) {
                message += "\n\nAs the room has a non-standard shape, you may have to reset a few times for your room to appear.";
            }

            return [ [], newRooms, message ];
        }

        this.testMapCommon("StageReplace", setup);
    }

    // Test by replacing the starting room
    testStartMap() {
        function setup(modPath, roomsPath, floorInfo, testRoom, version) {
            if (testRoom.length > 1) {
                QMessageBox.warning(this, "Error", "Cannot test multiple rooms with Starting Room Replacement!");
                throw new Error();
            }
            testRoom = testRoom[0];

            if (!["Afterbirth+", "Repentance"].includes(version)) {
                QMessageBox.warning(this, "Error", `Starting Room Replacement is not supported for ${version}!`);
                throw new Error();
            }

            // Sanity check for 1x1 room
            if ([2, 7, 9].includes(testRoom.info.shape)) {
                QMessageBox.warning(this, "Error", "Room shapes 2 and 7 (Long and narrow) and 9 (L shaped with upper right corner missing) can't be tested as the Start Room.");
                throw new Error();
            }

            resourcePath = this.findResourcePath();
            if (resourcePath === "") {
                QMessageBox.warning(this, "Error", "The resources folder could !be found. Please try reselecting it.");
                throw new Error();
            }

            roomPath = os.path.join(resourcePath, "rooms", "00.special rooms.stb");

            // Parse the special rooms, replace the spawns
            if (!QFile.exists(roomPath)) {
                QMessageBox.warning(this, "Error", "Missing 00.special rooms.stb from resources. Please unpack your resource files.");
                throw new Error();
            }

            startRoom = undefined;
            roomFile = this.open(roomPath, false);
            for (const room of roomFile.rooms) {
                if (room.name.includes("Start Room")) {
                    room.info.shape = testRoom.info.shape;
                    room.gridSpawns = testRoom.gridSpawns;
                    startRoom = room;
                    break;
                }
            }

            if (!startRoom) {
                QMessageBox.warning(this, "Error", "00.special rooms.stb is not a valid STB file.");
                throw new Error();
            }

            path = os.path.join(roomsPath, "00.special rooms.stb");

            // Resave the file
            this.save(roomFile.rooms, path, updateRecent=false);

            return [], [startRoom], "";
        }

        this.testMapCommon("StartingRoom", setup);
    }

    // Test by launching the game directly into the test room, skipping the menu
    testMapInstapreview() {
        function setup(modPath, roomsPath, floorInfo, rooms, version) {
            testfile = "instapreview.xml";
            path = Path(modPath) / testfile;
            path = path.resolve();

            roomsToUse = rooms;

            // if (there's a base game room file, override that. otherwise use special rooms
            newRooms = undefined;
            if (rooms.length > 1) {
                if (version === "Afterbirth+" && rooms.some(testRoom => testRoom.info.type === 0)) {
                    QMessageBox.warning(this, "Error", `${version} does not support the null room type.`);
                    throw new Error();
                }

                baseSpecialPath = "00.special rooms";
                extraInfo = xmlLookups.stages.lookup(
                    stage=floorInfo.get("Stage"),
                    stageType=floorInfo.get("StageType"),
                    baseGamePath=true,
                );
                basePath = floorInfo.get("BaseGamePath") ?? extraInfo[-1].get("BaseGamePath");

                // Set the selected rooms to have descending ids from max
                // this should avoid any id conflicts
                baseId = (2**31) - 1;
                newRooms = rooms.map((room, i) => new Room(
                    `${room.name} [Real ID: ${room.info.variant}]`,
                    room.gridSpawns,
                    room.palette,
                    room.difficulty,
                    room.weight,
                    room.info.type,
                    baseId - i,
                    room.info.subtype,
                    room.info.shape,
                    room.info.doors,
                ));

                if (basePath !== baseSpecialPath) {
                    specialRooms = newRooms.filter(room => room.info.type !== 1);
                    normalRooms = newRooms.filter(room => room.info.type <= 1);

                    multiRoomPath = os.path.join(modPath, "content", "rooms", baseSpecialPath + ".stb");
                    this.save(specialRooms, multiRoomPath, updateRecent=false);
                    multiRoomPath = os.path.join(modPath, "content", "rooms", basePath + ".stb");
                    this.save(normalRooms, multiRoomPath, updateRecent=false);
                }
                else {
                    multiRoomPath = os.path.join(modPath, "content", "rooms", basePath + ".stb");
                    this.save(newRooms, multiRoomPath, updateRecent=false);
                }

                roomsToUse = newRooms;
            }

            // Because instapreview is xml, no special allowances have to be made for rebirth
            this.save([roomsToUse[0]], path, updateRecent=false, isPreview=true);

            if (["Rebirth", "Antibirth"].includes(version)) {
                return [
                    [
                        "-room", path,
                        "-floorType", floorInfo.get("Stage"),
                        "-floorAlt", floorInfo.get("StageType"),
                        "-console",
                    ],
                    undefined,
                    "",
                ];
            }

            return [
                [
                    `--load-room=${path}`,
                    `--set-stage=${floorInfo.get('Stage')}`,
                    `--set-stage-type=${floorInfo.get('StageType')}`,
                ],
                newRooms,
                "",
            ];
        }

        this.testMapCommon("InstaPreview", setup);
    }

    findExecutablePath() {
        if (platform.system().includes("Windows")) {
            installPath = findInstallPath();
            if (installPath) {
                exeName = "isaac-ng.exe";
                if (QFile.exists(os.path.join(installPath, "isaac-ng-rebirth.exe"))) {
                    exeName = "isaac-ng-rebirth.exe";
                }
                return os.path.join(installPath, exeName);
            }
        }

        return "";
    }

    findResourcePath() {
        resourcesPath = "";

        if (QFile.exists(settings.value("ResourceFolder"))) {
            resourcesPath = settings.value("ResourceFolder");
        }
        else {
            installPath = findInstallPath();
            version = getGameVersion();

            if (installPath.length !== 0) {
                resourcesPath = os.path.join(installPath, "resources");
            }
            // Fallback Resource Folder Locating
            else {
                resourcesPathOut = QFileDialog.getExistingDirectory(this, `Please Locate The Binding of Isaac: ${version} Resources Folder`);
                if (!resourcesPathOut) {
                    QMessageBox.warning(this, "Error", "Couldn't locate resources folder and no folder was selected.");
                    return;
                }
                else {
                    resourcesPath = resourcesPathOut;
                }
                if (resourcesPath === "") {
                    QMessageBox.warning(this, "Error", "Couldn't locate resources folder and no folder was selected.");
                    return;
                }
                if (!QDir(resourcesPath).exists) {
                    QMessageBox.warning(this, "Error", "Selected folder does not exist or is not a folder.");
                    return;
                }
                if (!QDir(os.path.join(resourcesPath, "rooms")).exists) {
                    QMessageBox.warning(this, "Error", "Could not find rooms folder of selected directory.");
                    return;
                }
            }

            // Looks like nothing was selected
            if (resourcesPath.length === 0) {
                QMessageBox.warning(this, "Error", `Could not find The Binding of Isaac: ${version} Resources folder (${resourcesPath})`);
                return "";
            }

            settings.setValue("ResourceFolder", resourcesPath);
        }

        // Make sure 'rooms' exists
        roomsdir = os.path.join(resourcesPath, "rooms");
        if (!QDir(roomsdir).exists) {
            os.mkdir(roomsdir);
        }
        return resourcesPath;
    }

    killIsaac() {
        for (const p of psutil.process_iter()) {
            try {
                if (p.name().lowerCase().includes("isaac")) {
                    p.terminate();
                }
            }
            catch {
                // This is totally kosher, I'm just avoiding zombies.
            }
        }
    }

    testMapCommon(testType, setupFunc) {
        rooms = this.roomList.selectedRooms();
        if (!rooms) {
            QMessageBox.warning(this, "Error", "No rooms were selected to test.");
            return;
        }

        settings = QSettings("settings.ini", QSettings.IniFormat);
        version = getGameVersion();

        // Floor type
        // TODO: cache this when loading a file
        floorInfo = (xmlLookups.stages.lookup(path=mainWindow.path) ??
                     xmlLookups.stages.lookup(name="Basement"))[-1];

        forceCleanModFolder = settings.value("HelperModDev") === "1";
        modPath, roomPath = this.makeTestMod(forceCleanModFolder);
        if (modPath === "") {
            QMessageBox.warning(this, "Error", "The basement renovator mod folder could not be copied over: " + roomPath);
            return;
        }

        // Ensure that the room data is up to date before writing
        this.storeEntityList();

        // Call unique code for the test method
        launchArgs, extraMessage = undefined, undefined;
        try {
            // setup raises an exception if it can't continue
            launchArgs, roomsOverride, extraMessage = setupFunc(
                modPath, roomPath, floorInfo, rooms, version
            ) ?? [[], undefined, ""];
        }
        catch (e) {
            printf("Problem setting up test:", e);
            return;
        }

        testRooms = roomsOverride ?? rooms;
        this.writeTestData(modPath, testType, floorInfo, testRooms);

        testfile = "testroom.xml";
        testPath = Path(modPath) / testfile;
        testPath = testPath.resolve();
        this.save(testRooms, testPath, fileObj=this.roomList.file, updateRecent=false);

        // Trigger test hooks
        testHooks = settings.value("HooksTest");
        if (testHooks) {
            tp = testPath.toString();
            for (const hook of testHooks) {
                wd, script = os.path.split(hook);
                try {
                    subprocess.run([hook, tp, "--test"], cwd=wd, timeout=30);
                }
                catch (e) {
                    printf("Test hook failed! Reason:", e);
                }
            }
        }

        // Launch Isaac
        installPath = findInstallPath();
        if (!installPath) {
            QMessageBox.warning(this, "Error", "Your install path could not be found! You may have the wrong directory, reconfigure in settings.ini");
            return;
        }

        now = new Date();
        for (const room of rooms) {
            room.lastTestTime = now;
        }
        this.dirt()  // dirty for test timestamps

        try {
            // try to run through steam to avoid steam confirmation popup, else run isaac directly
            // if there exists drm free copies, allow the direct exe launch method
            steamPath = undefined;
            if (version !== "Antibirth" && settings.value("ForceExeLaunch") !== "1") {
                steamPath = getSteamPath() ?? "";
            }

            if (steamPath) {
                exePath = `${steamPath}\\Steam.exe`;
            }
            else {
                exePath = this.findExecutablePath();
            }

            if (exePath && QFile.exists(exePath) && settings.value("ForceUrlLaunch") !== "1") {
                if (steamPath) {
                    launchArgs = ["-applaunch", "250900"].concat(launchArgs);
                }

                appArgs = [exePath].concat(launchArgs);
                printf("Test) { Running executable", " ".join(appArgs));
                subprocess.Popen(appArgs, cwd=installPath);
            }
            else {
                args = launchArgs.map(x => x.includes(" ") ? `"${x}"` : x).join(" ");
                urlArgs = urllib.parse.quote(args);
                urlArgs = urlArgs.replace(/\//g, "%2F");

                url = `steam://rungameid/250900//${urlArgs}`;
                printf("Test: Opening url", url);
                webbrowser.open(url);
            }
        }
        catch (e) {
            printf(e);
            QMessageBox.warning(this, "Error", `Failed to test with ${testType}: ${e}`);
            return;
        }

        settings = QSettings("settings.ini", QSettings.IniFormat);
        if (settings.value("DisableTestDialog") === "1") {
            // disable mod in 5 minutes
            this.disableTestModTimer = setTimeout(() => this.disableTestMod(modPath), 5 * 60 * 1000);
            if (extraMessage) {
                QMessageBox.information(this, "BR Test", extraMessage);
            }
        }
        else {
            // Prompt to disable mod and perform cleanup
            // for some reason, if the dialog blocks on the button click,
            // e.g. QMessageBox.information() or msg.exec(), isaac crashes on launch.
            // This is probably a bug of python or Qt
            msg = QMessageBox(QMessageBox.Information, "Disable BR",
                (extraMessage ? extraMessage + "\n\n" : "") + 'Press "OK" when done testing to disable the BR helper mod.',
            QMessageBox.Ok, this);

            function fin(button) {
                result = msg.standardButton(button);
                if (result === QMessageBox.Ok) {
                    this.disableTestMod(modPath);
                }

                this.killIsaac();
            }

            msg.buttonClicked.connect(fin);
            msg.open();
        }
    }

    // Edit
    ////////////////////////////////////////////////

    selectAll() {
        path = QPainterPath();
        path.addRect(this.scene.sceneRect());
        this.scene.setSelectionArea(path);
    }

    deSelect() {
        this.scene.clearSelection();
    }

    copy() {
        this.clipboard = [];
        for (const item of this.scene.selectedItems()) {
            this.clipboard.push([
                item.entity.x,
                item.entity.y,
                item.entity.Type,
                item.entity.Variant,
                item.entity.Subtype,
                item.entity.weight,
            ]);
        }
    }

    cut() {
        this.clipboard = [];
        for (const item of this.scene.selectedItems()) {
            this.clipboard.push([
                item.entity.x,
                item.entity.y,
                item.entity.Type,
                item.entity.Variant,
                item.entity.Subtype,
                item.entity.weight,
            ]);
            item.remove();
        }
    }

    paste() {
        if (!this.clipboard) {
            return;
        }

        this.scene.clearSelection();
        for (const item of this.clipboard) {
            ent = new Entity(...item);
            ent.setSelected(true);
        }

        this.dirt();
    }

    showReplaceDialog() {
        replaceDialog = ReplaceDialog();
        if (replaceDialog.exec() !== QDialog.Accepted) {
            return;
        }

        this.replaceEntities(replaceDialog.fromEnt.getEnt(), replaceDialog.toEnt.getEnt());
    }

    // Miscellaneous
    ////////////////////////////////////////////////

    toggleSetting(setting, onDefault=false) {
        settings = QSettings("settings.ini", QSettings.IniFormat);
        a, b = onDefault ? ("0", "1") : ("1", "0");
        settings.setValue(setting, settings.value(setting) === a ? b : a);
        this.scene.update();
    }

    showPainter() {
        if (this.EntityPaletteDock.isVisible()) {
            this.EntityPaletteDock.hide();
        }
        else {
            this.EntityPaletteDock.show();
        }

        this.updateDockVisibility();
    }

    showRoomList() {
        if (this.roomListDock.isVisible()) {
            this.roomListDock.hide();
        }
        else {
            this.roomListDock.show();
        }

        this.updateDockVisibility();
    }

    updateDockVisibility() {
        if (this.EntityPaletteDock.isVisible()) {
            this.wb.setText("Hide Entity Painter");
        }
        else {
            this.wb.setText("Show Entity Painter");
        }

        if (this.roomListDock.isVisible()) {
            this.wc.setText("Hide Room List");
        }
        else {
            this.wc.setText("Show Room List");
        }
    }

    resetWindowDefaults() {
        this.restoreState(this.resetWindow["state"], 0);
        this.restoreGeometry(this.resetWindow["geometry"]);
    }

    // Help
    ////////////////////////////////////////////////

    aboutDialog() {
        caption = "About the Basement Renovator";

        text = (<div>
            <h1>Basement Renovator</h1>
            <p>Basement Renovator is a room editor for the Binding of Isaac: Rebirth and its DLCs and mods. You can use it to either edit existing rooms or create new ones.</p>
            <p>To edit the game's existing rooms, you must have unpacked the .stb files by using the game's resource extractor. (On Windows, this is located at "C:\\Program Files (x86)\\Steam\\steamapps\\common\\The Binding of Isaac Rebirth\\tools\\ResourceExtractor\\ResourceExtractor.exe".)</p>
            <p>Basement Renovator was originally programmed by Tempus (u/Chronometrics). It is open source and hosted on <a href='https://github.com/Basement-Renovator/Basement-Renovator'>GitHub</a>.</p>
        </div>);

        msg = QMessageBox.about(mainWindow, caption, text);
    }

    goToHelp() {
        QDesktopServices().openUrl(QUrl("https://github.com/Basement-Renovator/Basement-Renovator/"));
    }
}


function applyDefaultSettings(settings, defaults) {
    for (const [ key, val ] of defaults.entries()) {
        if (settings.value(key) === undefined) {
            settings.setValue(key, val);
        }
    }
}


export default function main() {
    // TODO: port to node versions
    min_version = [3, 7];
    if (!(sys.version_info[0] > min_version[0] || (
        sys.version_info[0] === min_version[0] &&
        sys.version_info[1] >= min_version[1]
    ))) {
        throw new NotImplementedError(
            `Basement Renovator requires minimum Python ${min_version[0]}.${min_version[1]}, your version: ${sys.version_info[0]}.${sys.version_info[0]}`
        );
    }

    // Application
    app = QApplication(sys.argv);
    app.setWindowIcon(QIcon("resources/UI/BasementRenovator.png"));

    cmdParser = QCommandLineParser();
    cmdParser.setApplicationDescription("Basement Renovator is a room editor for The Binding of Isaac: Rebirth and its DLCs and mods");
    cmdParser.addHelpOption();

    cmdParser.addPositionalArgument("file", "optional file to open on launch, otherwise opens most recent file");

    cmdParser.process(app);

    settings = QSettings("settings.ini", QSettings.IniFormat);

    applyDefaultSettings(settings, { SnapToBounds: "1", ExportSTBOnSave: "1" });

    // XML Globals
    version = getGameVersion();
    xmlLookups = MainLookup(version, settings.value("Verbose") === "1");
    if (settings.value("DisableMods") !== "1") {
        loadMods(
            settings.value("ModAutogen") === "1",
            findInstallPath(),
            settings.value("ResourceFolder", ""),
        );
    }

    printSectionBreak();
    printf("INITIALIZING MAIN WINDOW");
    mainWindow = MainWindow();

    settings.setValue("FixIconFormat", "0");

    startFile = undefined;

    args = cmdParser.positionalArguments();
    if (args) {
        startFile = args[0];
    }
    else {
        recent = settings.value("RecentFiles", []);
        if (recent) {
            startFile = recent[0];
        }
    }

    if (startFile && os.path.exists(startFile)) {
        mainWindow.openWrapper(startFile);
    }

    mainWindow.show();

    sys.exit(app.exec());
}
