import React from 'react';
import _ from 'lodash';
import DockLayout, { LayoutData } from 'rc-dock';
import * as Palette from './palette';

function App() {
    const box: LayoutData = {
        dockbox: {
            mode: 'horizontal',
            children: [
                Palette.layout(window.resources().entities),
                { mode: 'vertical', children: [] },
            ],
        }
    };

    return (<DockLayout defaultLayout={box} style={{
        position: 'absolute',
        left: 10,
        right: 10,
        top: 10,
        bottom: 10
    }} />);
}

export default App;
