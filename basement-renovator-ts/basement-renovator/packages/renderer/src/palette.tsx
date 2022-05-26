import { Divider, Stack } from '@mui/material';
import _ from 'lodash';
import type { Entity, EntityGroup } from 'packages/common/config/br-config';
import type { EntityLookup } from 'packages/common/lookup';
import DockLayout, { BoxData, LayoutData, TabData } from 'rc-dock';
import * as React from 'react';

type FCC<T = {}> = React.FC<React.PropsWithChildren<T>>;

const Icon: React.FC<{
    src: string;
    alt?: string;
}> = ({ src, alt, ...rest }) => {
    return (<img src={src} alt={alt} title={alt} {...rest} />);
};

const EntityIcon: React.FC<{
    entity: Entity;
}> = ({ entity, ...rest }) => {
    return (<div style={{
        margin: '5px',
    }}><Icon src={entity.imagePath} alt={entity.name} {...rest} /></div>);
}

const SectionHeader: React.FC<React.PropsWithChildren<{}>> = ({ children, ...rest }) => (<Stack style={{
    height: '50px',
    backgroundColor: '#eee',
    justifyContent: 'center'
}} {...rest}>
    <div><Divider><b>{children}</b></Divider></div>
</Stack>);

const LabelledGroup: FCC<{
    label: string;
}> = ({ children, label, ...rest }) => (<Stack style={{
    width: '100%'
}} {...rest}>
    <SectionHeader>{label}</SectionHeader>
    <Stack direction='row' flexWrap='wrap' alignItems={'end'}>{children}</Stack>
</Stack>)

const TabContent: FCC = ({ children, ...rest }) => (
<div style={{ overflowY: 'scroll', height: '100%' }}>
    <Stack {...rest}>{children}</Stack>
</div>);

export function layout(entities: EntityLookup): BoxData {
    const expandEnts = (g: EntityGroup | Entity, ignoreLabel?: boolean): React.ReactNode | React.ReactNode[] => {
        //if (g instanceof EntityGroup) {
        if ("groupentries" in g) {
            if (g.entries.length === 0) {
                return [];
            }

            if (g.label && !ignoreLabel) {
                return (<LabelledGroup key={g.name} label={g.label}>{
                    expandEnts(g, true) as React.ReactNode[]
                }</LabelledGroup>);
            }

            return _.flattenDeep(g.entries.sort((a, b) => {
                const al = "groupentries" in a && a.label ? 1 : 0;
                const bl = "groupentries" in b && b.label ? 1 : 0;
                return al - bl;
            }).map(e => expandEnts(e)));
        }
        return <EntityIcon key={g.name} entity={g} />;
    }

    const tabs = entities.tabs.map<TabData>(tab => ({
        id: tab.name,
        title: tab.label ?? tab.name,
        group: 'ENTITIES',
        content: (<TabContent key={tab.name}>{
            tab.groupentries.map(group => expandEnts(group))
        }</TabContent>)
    }));

    return {
        mode: 'horizontal',
        children: [ { tabs } ],
    };
}