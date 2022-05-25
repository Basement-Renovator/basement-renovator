import React from 'react';
import { HBox, VBox, SplitPanel } from './panel';
import type { Entity } from '../../common/config/br-config';
import _ from 'lodash';
import DockLayout, { LayoutData } from 'rc-dock';

const Icon: React.FC<{
    src: string;
    alt?: string;
}> = ({ src, alt, ...rest }) => {
    return (<img src={src} alt={alt} {...rest} />);
};

const EntityIcon: React.FC<{
    entity: Entity;
}> = ({ entity, ...rest }) => {
    return (<Icon src={entity.imagePath} alt={entity.name} {...rest} />);
}

function App() {
    const contents = _.flatten(_.values(window.resources().entities.entityListByType).map(ents => ents.map(e => (<div key={e.name}><EntityIcon entity={e} /></div>))));
    console.log('loading...', contents);

    const box: LayoutData = {
        dockbox: {
            mode: 'horizontal',
            children: [ {
                mode: 'vertical',
                children: [ {
                    tabs: [ { id: 'entities', title: 'Entities', content: (<div style={{
                        backgroundColor: 'yellow'
                    }}>{contents}</div>) } ]
                } ]
            }, {
                mode: 'vertical',
                children: [],
            } ],
        }
    };

    return (<DockLayout defaultLayout={box} />);
}

export default App;
