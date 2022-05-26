import { Divider, Stack } from '@mui/material';
import _ from 'lodash';
import type { Entity, EntityGroup } from 'packages/common/config/br-config';
import type { EntityLookup } from 'packages/common/lookup';
import DockLayout, { BoxData, LayoutData, TabData } from 'rc-dock';
import * as React from 'react';

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

const SectionHeader: React.FC<React.PropsWithChildren<{}>> = ({ children, ...rest }) => (<Stack style={{
    height: '50px',
    justifyContent: 'center'
}} {...rest}>
    <div><Divider><b>{children}</b></Divider></div>
</Stack>);

export function layout(entities: EntityLookup): BoxData {
    const expandEnts = (g: EntityGroup | Entity): Entity | Entity[] => {
        //if (g instanceof EntityGroup) {
        if ("groupentries" in g) {
            return g.entries.map(expandEnts) as Entity[];
        }
        return g;
    }

    const tabs = entities.tabs.map<TabData>(tab => ({
        id: tab.name,
        title: tab.label,
        group: 'ENTITIES',
        content: (<div style={{ overflowY: 'scroll', height: '100%' }}><Stack key={tab.name}>{
            tab.groupentries.map(group => (<Stack key={group.name}>
                <SectionHeader>{group.label}</SectionHeader>
                <Stack direction='row' flexWrap='wrap'>{
                    _.flattenDeep([ expandEnts(group) ])
                    .map(e =>(<div key={e.name}><EntityIcon entity={e} /></div>))
                }</Stack>
            </Stack>))
        }</Stack></div>)
    }));

    return {
        mode: 'horizontal',
        children: [ { tabs } ],
    };
}