import { Divider, Stack, Box, TextField } from '@mui/material';
import _ from 'lodash';
import type { Entity, EntityGroup } from 'packages/common/config/br-config';
import type { EntityLookup } from 'packages/common/lookup';
import * as React from 'react';
import { Tab, TabPanel } from './panel';

type FCC<T = {}> = React.FC<React.PropsWithChildren<T>>;

const Icon: React.FC<{
    src: string;
    alt?: string;
}> = ({ src, alt, ...rest }) => {
    return (<img src={src} alt={alt} title={alt} draggable={false} {...rest} />);
};

const EntityIcon: React.FC<{
    entity: Entity;
    search?: string;
}> = ({ entity, search, ...rest }) => {
    return (<Box 
        sx={{
            margin: '5px',
            ':hover': {
                backgroundColor: '#ddf'
            }
        }}
        hidden={search && !entity.name?.toLowerCase().includes(search) ? true : false}
    ><Icon src={entity.imagePath} alt={entity.name} {...rest} /></Box>);
}

const SectionHeader: React.FC<React.PropsWithChildren<{
    style?: React.CSSProperties;
    onClick?: React.MouseEventHandler;
}>> = ({ children, onClick, ...rest }) => (<Stack sx={{
    height: '50px',
    backgroundColor: '#eee',
    justifyContent: 'center',
    ':hover': {
        backgroundColor: '#ddf'
    }
}} {...rest}>
    <div onClick={onClick}><Divider><b>{children}</b></Divider></div>
</Stack>);

const LabelledGroup: FCC<{
    label: string;
}> = ({ children, label, ...rest }) => {
    const [ collapsed, setCollapsed ] = React.useState<boolean>(false);

    return (<Stack style={{
        width: '100%',
        userSelect: 'none',
    }} {...rest}>
        <SectionHeader onClick={() => setCollapsed(!collapsed)} style={{
            cursor: 'pointer',
        }}>{`${label}${collapsed ? ' ▶' : ''}`}</SectionHeader>
        <Stack direction='row' flexWrap='wrap' alignItems={'end'} style={
            collapsed ? { display: 'none' } : {}
        }>{children}</Stack>
    </Stack>);
};

export const Layout: React.FC<{
    entities: EntityLookup;
}> = ({ entities, ...rest }) => {
    const [search, setSearch] = React.useState<string>("");

    const expandEnts = (g: EntityGroup | Entity, ignoreLabel?: boolean, searchInput?: string): React.ReactNode | React.ReactNode[] => {
        //if (g instanceof EntityGroup) {
        if ("groupentries" in g) {
            if (g.entries.length === 0) {
                return [];
            }

            if (g.label && !ignoreLabel) {
                return (<LabelledGroup key={g.name} label={g.label}>{
                    expandEnts(g, true, searchInput) as React.ReactNode[]
                }</LabelledGroup>);
            }

            // Labelled groups are pushed to the back
            return _.flattenDeep(g.entries.sort((a, b) => {
                const al = "groupentries" in a && a.label ? 1 : 0;
                const bl = "groupentries" in b && b.label ? 1 : 0;
                return al - bl;
            }).map(e => expandEnts(e, ignoreLabel, searchInput)));
        }

        return <EntityIcon key={g.name} entity={g} search={searchInput} />;
    }

    const tabs = entities.tabs.map(tab => (<Tab key={tab.name} label={tab.label ?? tab.name}>
        <Stack key={tab.name}>{
            tab.groupentries.map(group => expandEnts(group))
        }</Stack>
    </Tab>));

    const searchTab = (<Tab key="entity-palette-search-tab" label="Search">
        <Stack key="entity-palette-search-tab" direction="row" flexWrap="wrap" alignItems="end">
            {expandEnts(entities.entityList, true, search)}
        </Stack>
    </Tab>)

    let searchInputHandler = (event: any) => {
        setSearch(event.target.value.toLowerCase());
    }

    return (
        <Stack key="entity-palette">
            <TabPanel style={{
                display: search !== "" ? "none": ""
            }} {...rest}>{tabs}</TabPanel>
            <TabPanel style={{
                display: search === "" ? "none": ""
            }} {...rest}>{searchTab}</TabPanel>
            <TextField id="entity-palette-search" label="Search" onChange={searchInputHandler} />
        </Stack>
    );
};