import assert from 'assert';
import { Box, Divider, Stack } from '@mui/material';
import { default as SplitPane, Pane, PaneProps, SplitPaneProps } from 'react-split-pane';
import _ from 'lodash';
import React from 'react';
import { FlexboxProps as MuiFlexboxProps } from '@mui/system';

type Orientation = "horizontal" | "vertical";

type FlexboxProps = Partial<{
    grow: number;
    shrink: number;
    direction: Orientation;
    wrap: MuiFlexboxProps["flexWrap"];
    order: number;
    justify: MuiFlexboxProps["justifyContent"];
    justifyItems: MuiFlexboxProps["justifyItems"];
    align: MuiFlexboxProps["alignContent"];
    alignItems: MuiFlexboxProps["alignItems"];
    gap: CSSNumberish;
}>;

const FlexBox: React.FC<FlexboxProps & {
    children?: React.ReactNode;
} & Record<string, unknown>> = (props) => {
    const {
        grow: flexGrow,
        shrink: flexShrink,
        justify: justifyContent,
        justifyItems,
        align: alignContent,
        alignItems,
        direction: flexDirection,
        wrap: flexWrap,
        order,
        gap,
        children,
        ...rest
    } = props;

    return (<Stack
        flexGrow={flexGrow ?? 1}
        flexShrink={flexShrink}
        justifyContent={justifyContent ?? 'space-between'}
        justifyItems={justifyItems}
        alignContent={alignContent}
        alignItems={alignItems ?? 'stretch'}
        flexDirection={flexDirection === "horizontal" ? "row" : "column"}
        flexWrap={flexWrap}
        order={order}
        gap={gap}
        {...rest}
    >{children}</Stack>);
};

export const HBox: typeof FlexBox = (props) => (<FlexBox {...props} direction='horizontal' />);
export const VBox: typeof FlexBox = (props) => (<FlexBox {...props} direction='vertical' />);

export const SplitPanel: React.FC<FlexboxProps & SplitPaneProps & Record<string, unknown>> = (props) => {
    const { direction, split, ...rest } = props;
    return (<FlexBox component={SplitPane} split={direction === "horizontal" ? "vertical" : "horizontal"} {...rest} />);
};

// the current panel is always the left-most, top-most
// panels may ONLY look like this:
// <Panel component={RootTool}>
//   <Splitter />
//   ...
// </Panel>
// const Panel: React.FunctionComponent<{
//     left: number;
//     right: number;
//     top: number;
//     bottom: number;
//     component?: string | React.JSXElementConstructor<any>;
// }> = (props) => {
//     const rect = _.pick(props, "left", "right", "top", "bottom");

//     let split: {
//         dir: Orientation;
//         value: number;
//     } | undefined;
//     React.Children.forEach(props.children, (child) => {
//         if (!React.isValidElement(child)) {
//             return;
//         }

//         if (isInstance(child, Splitter)) {
//             if (split) {
//                 throw new Error("Cannot have splitters without interspersed panels");
//             }
//             split = {
//                 dir: child.props.orientation === 'vertical' ? 'vertical' : 'horizontal',
//                 value: child.props.value,
//             };
//         }
//         else if (isInstance(child, Panel)) {
//             if (!split) {
//                 throw new Error("No current split!");
//             }

//             child.props.left = rect.left;
//             child.props.right = rect.right;
//             child.props.bottom = rect.bottom;
//             child.props.top = rect.top;

//             if (split.dir === 'vertical') {
//                 rect.bottom *= split.value;
//                 child.props.top = rect.bottom;
//             }
//             else {
//                 rect.right *= split.value;
//                 child.props.left = rect.right;
//             }

//             split = undefined;
//         }
//     });

//     return React.createElement(props.component ?? Box, {
//         ...props,
//         ...rect,
//     }, props.children);
// }