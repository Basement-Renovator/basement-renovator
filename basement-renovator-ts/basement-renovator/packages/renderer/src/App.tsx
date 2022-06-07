import React from 'react';
import _ from 'lodash';
import "rc-dock/dist/rc-dock.css";

import * as Palette from './palette';
import { Stack } from '@mui/material';

function App() {
    return (<Stack direction='row' style={{
        position: 'absolute',
        left: 10,
        right: 10,
        top: 10,
        bottom: 10
    }}>
        <Palette.Layout entities={window.resources().entities} />
    </Stack>);
}

export default App;
