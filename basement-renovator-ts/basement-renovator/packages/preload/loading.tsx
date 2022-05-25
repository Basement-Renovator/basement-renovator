import './loading.css';

import React from "react";

/**
 * https://tobiasahlin.com/spinkit
 * https://connoratherton.com/loaders
 * https://projects.lukehaas.me/css-loaders
 * https://matejkustec.github.io/SpinThatShit
 */
export const Loading: React.FC = (props) => {
    return (<div className='app-loading-wrap' {...props}>
        <div className='loaders-css__square-spin'>
            <div />
        </div>
    </div>);
};
