import { Box, Stack, Tab as MTab, TabProps, Tabs } from '@mui/material';
import _ from 'lodash';
import React from 'react';

type FCC<T = {}> = React.FC<React.PropsWithChildren<T>>;

export const Tab: FCC<Omit<TabProps, 'children'>> = (props) => (<div {...props} />);

const MonoTabPanel: FCC<{
    index: number;
    value: number;
}> = ({ children, value, index, ...rest }) => {
    return (<div role="tabpanel" hidden={value !== index} {...rest}>{
        children
    }</div>);
};

export const TabPanel: FCC<{
    value?: number;
    style?: React.CSSProperties;
}> = ({ children, value, ...rest }) => {
    const [val, setValue] = React.useState(value ?? 0);

    return (<Stack {...rest}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={val} onChange={(e, newValue) => setValue(newValue)}>{
                React.Children.map(children, (child) => {
                    if (!React.isValidElement(child)) {
                        return false;
                    }
                    return (<MTab {..._.omit(child.props, 'children')} />);
                })
            }</Tabs>
        </Box>
        <Box flexGrow='1' style={{
            overflowY: 'scroll'
        }}>{
            React.Children.map(children, (child, index) => React.isValidElement(child) &&
                (<MonoTabPanel value={val} index={index}>{child.props.children}</MonoTabPanel>)
            )
        }</Box>
    </Stack>)
};