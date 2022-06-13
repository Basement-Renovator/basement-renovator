import { Stack, Tabs } from "@mui/material";
import type { Room, RoomFile } from "packages/common/core";
import { RoomShapeLookup , RoomTypeLookup} from "packages/common/lookup";
import React from "react";

type FCC<T = {}> = React.FC<React.PropsWithChildren<T>>;

const RoomShapeIcon: React.FC<{
    room: Room;
    roomShapes: RoomShapeLookup;
}> = ({room, roomShapes}) => {
    const roomShape = roomShapes.lookup({id: room.info.shapeData.id})[0];

    const doorIndicators = room.info.doors.map((door) => {
        if (door.exists) {
            const wallWithDoor = room.info.shapeData.walls.find((wall) => wall.doors.some((d) => (d.x === undefined || d.x === door.x) && (d.y === undefined || d.y === door.y)))
            return <div key={door.x.toString().concat(door.y.toString())} style={{
                position: "absolute",
                top: wallWithDoor?.normal.y === -1 ? "16px" : "0px",
                left: wallWithDoor?.normal.x === -1 ? "15px" : "-1px",
                height: wallWithDoor?.normal.x !== undefined ? "17px" : "2px",
                width: wallWithDoor?.normal.y !== undefined ? "17px" : "2px",
                backgroundColor: "rgb(255, 0, 0)"
            }}/>
        }
    })

    return (
        <div style={{
            position: "relative"
        }}>
            <img src={roomShape.attrib.Icon} draggable={false}/>
            {doorIndicators}
        </div>
    )
}

const RoomIcon: React.FC<{
    room: Room;
    roomShapes: RoomShapeLookup;
    roomTypes: RoomTypeLookup;
}> = ({room, roomShapes, roomTypes}) => {
    const roomType = roomTypes.lookup({room: room, showInMenu: true})[0];

    // Ignoring roomType 1 probably shouldn't be hardcoded here.
    return (
        <Stack direction="column" spacing={0} sx={{
            justifyContent: "center"
        }}>
            {(roomType && roomType.attrib.Type !== 1) ? <img src={roomType.attrib.Icon} draggable={false}/> : null}
            <RoomShapeIcon room={room} roomShapes={roomShapes}/>
        </Stack>
    )
}

const RoomListEntry: React.FC<{
    room: Room;
    roomShapes: RoomShapeLookup;
    roomTypes: RoomTypeLookup;
}> = ({ room, roomShapes, roomTypes, ...rest }) => {
    return (<Stack direction="row" sx={{
        color: room.difficulty === 20 ? 'rgb(190, 0, 255)' : `hsl(0, 100%, ${
            Math.min(Math.max(room.difficulty / 15, 0), 1) * 50
        }%)`,
        border: '1px solid #eee',
        padding: '5px',
        ':hover': {
            backgroundColor: '#ddf',
        }
    }} {...rest}>
        <RoomIcon room={room} roomShapes={roomShapes} roomTypes={roomTypes}/>
        <p>{`${room.info.variant} - `}</p>
        <p>{room.name}</p>
    </Stack>);
}

export const Layout: React.FC<{
    rooms?: RoomFile;
    roomShapes: RoomShapeLookup;
    roomTypes: RoomTypeLookup;
    style?: React.CSSProperties;
}> = ({rooms, roomShapes, roomTypes, ...rest }) => {
    return (<Stack {...rest}>{rooms?.rooms.map((room) => (
        <RoomListEntry key={window.crypto.randomUUID()} roomShapes={roomShapes} roomTypes={roomTypes} room={room} />
    )) ?? []}</Stack>);
};