import _ from 'lodash';

import * as Palette from './palette';
import * as RoomList from './room-list';
import type { RoomFile } from 'packages/common/core';
import { Stack } from '@mui/material';

function App({ rooms }: { rooms?: RoomFile }) {
    const lookups = window.resources();
    return (<Stack direction='row' style={{
        position: 'absolute',
        left: 10,
        right: 10,
        top: 10,
        bottom: 10
    }}>
        <Palette.Layout entities={lookups.entities} />
        <RoomList.Layout rooms={rooms} style={{
            overflowY: 'scroll',
            minWidth: '200px'
        }} />
    </Stack>);
}

export default App;
