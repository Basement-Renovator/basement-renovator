import { Stack, Tabs } from "@mui/material";
import type { Room, RoomFile } from "packages/common/core";
import React from "react";

type FCC<T = {}> = React.FC<React.PropsWithChildren<T>>;

const RoomListEntry: React.FC<{
    room: Room;
}> = ({ room, ...rest }) => {
    return (<Stack direction="row" sx={{
        color: room.difficulty === 20 ? 'rgb(190, 0, 255)' : `hsl(0, 100%, ${
            Math.min(Math.max(room.difficulty / 15, 0), 1) * 50
        }%)`,
        border: '1px solid #eee',
        padding: '5px',
        ':hover': {
            backgroundColor: '#ddf',
        },
    }} {...rest}>
        <p>{`${room.info.variant} - `}</p>
        <p>{room.name}</p>
    </Stack>);
}

export const Layout: React.FC<{
    rooms?: RoomFile;
    style?: React.CSSProperties;
}> = ({ rooms, ...rest }) => {
    return (<Stack {...rest}>{rooms?.rooms.map((room) => (
        <RoomListEntry key={window.crypto.randomUUID()} room={room} />
    )) ?? []}</Stack>);
};