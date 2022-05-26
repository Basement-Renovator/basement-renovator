import { Divider, Stack } from '@mui/material';
import _ from 'lodash';
//import { Entity, EntityGroup } from 'packages/common/config/br-config';
//import { EntityLookup } from 'packages/common/lookup';
import DockLayout, { BoxData, LayoutData, TabData } from 'rc-dock';
import * as React from 'react';

type EntityLookup = ReturnType<typeof window.resources>["entities"];
type Entity = EntityLookup["entityListByType"][string];
type EntityGroup = EntityLookup["groups"][string];

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

const SectionHeader: React.FC<React.PropsWithChildren<{}>> = ({ children, ...rest }) => (<div style={{
    height: '40px',
}} {...rest}>
    <Divider>{children}</Divider>
</div>);

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
        content: (<Stack key={tab.name}>{
            tab.groupentries.map(group => (<Stack key={group.name}>
                <SectionHeader>{group.label}</SectionHeader>
                <Stack direction='row'>{
                    _.flattenDeep([ expandEnts(group) ])
                    .map(e =>(<div key={e.name}><EntityIcon entity={e} /></div>))
                }</Stack>
            </Stack>))
        }</Stack>)
    }));

    return {
        mode: 'horizontal',
        children: [ { tabs } ],
    };
}