import _ from 'lodash';

import * as Palette from './palette';
import * as RoomList from './room-list';
import type { RoomFile } from 'packages/common/core';
import { Stack } from '@mui/material';

function App({ rooms }: { rooms?: RoomFile }) {
    return (<Stack direction='row' style={{
        position: 'absolute',
        left: 10,
        right: 10,
        top: 10,
        bottom: 10
    }}>
        <Palette.Layout entities={window.resources().entities} />
        <RoomList.Layout rooms={rooms} style={{
            overflowY: 'scroll',
            minWidth: '200px'
        }} />
    </Stack>);
}

export default App;
