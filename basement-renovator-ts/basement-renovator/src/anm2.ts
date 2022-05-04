import fs from 'fs';
import pathlib, { ParsedPath } from 'path';
import * as XML from './xml';

import sharp, { Sharp } from 'sharp';
import * as matrix from 'transformation-matrix';

type Vector = { x: number; y: number; };
type Rect = {
    left: number;
    right: number;
    top: number;
    bottom: number;
};

function combineRects(dest: Rect, rect: Rect): void {
    if (rect.left < dest.left) {
        dest.left = rect.left;
    }
    if (rect.right > dest.right) {
        dest.right = rect.right;
    }
    if (rect.top < dest.top) {
        dest.top = rect.top;
    }
    if (rect.bottom > dest.bottom) {
        dest.bottom = rect.bottom;
    }
}

/**
 * @param args
 * @param args.rotation degrees
 * @returns [ transformed image, transformation matrix (without translate) ]
 */
function transform(img: Sharp, args: Partial<{
    rotation: number; // degrees
    scale: Vector;
    translate: Vector;
}>): [ Sharp, matrix.Matrix ] {
    let mat = matrix.identity();
    if (args.rotation !== undefined) {
        mat = matrix.transform(mat, matrix.rotateDEG(args.rotation));
    }
    if (args.scale) {
        mat = matrix.transform(mat, matrix.scale(args.scale.x, args.scale.y));
    }

    return [ (img as any).affine([
        [ mat.a, mat.c ],
        [ mat.b, mat.d ],
    ], {
        idx: args.translate?.x,
        idy: args.translate?.y,
        background: '#0000',
        interpolator: (sharp as any).interpolators.nearest,
    }), mat ];
}

type Frame = { attrib: {
    XPivot?: number;
    YPivot?: number;
    XPosition: number;
    YPosition: number;
    XScale: number;
    YScale: number;
    Rotation: number;

    XCrop?: number;
    YCrop?: number;
    Width?: number;
    Height?: number;

    Delay: number;
    Visible: boolean;
    Interpolated: boolean;

    RedTint: number;
    GreenTint: number;
    BlueTint: number;
    AlphaTint: number;

    RedOffset: number;
    GreenOffset: number;
    BlueOffset: number;
}; };

type LayerAnimation = {
    attrib: {
        LayerId: number;
        Visible: boolean;
    };
    Frame?: Frame[];
};

type Animation = {
    attrib: {
        Name: string;
        FrameNum: number;
        Loop: boolean;
    };
    RootAnimation: {
        Frame: Frame[];
    };
    LayerAnimations: {
        LayerAnimation?: LayerAnimation[];
    };
    //NullAnimations: any[];
    //Triggers: any[];
};

type Anm2 = {
    AnimatedActor: {
        Content: {
            Spritesheets: {
                Spritesheet: Array<{
                    attrib: {
                        Path: string;
                        Id: number;
                    };
                }>;
            };
            Layers: {
                Layer: Array<{
                    attrib: {
                        Name: string;
                        Id: number;
                        SpritesheetId: number;
                    };
                }>;
            };
            //Nulls: { Null: Array<any>; };
            //Events: { Event: Array<any>; };
        };
        Animations: {
            attrib: { DefaultAnimation: string; };
            Animation: Animation[];
        };
    };
};

type Image = {
    image: any;
    pivot: Vector;
    position: Vector;
    rotation: number;
    scale: Vector;
    crop: Vector;
    width: number;
    height: number;
};

class Anim {
    node: any = undefined;
    len = 0;
    frame = -1;
    rootFrames: Frame[] = [];
    frameLayers: LayerAnimation[] = [];

    set(node: Animation) {
        this.node = node;
        // TODO: disable root for overlays?
        this.rootFrames = node.RootAnimation.Frame ?? [];
        this.frameLayers = node.LayerAnimations.LayerAnimation ?? [];
        this.len = node.attrib.FrameNum;
        this.frame = 0;
    }
}

export default class Config {
    fullPath: string;
    path: ParsedPath;
    resourcePath: string;
    tree: Anm2["AnimatedActor"];

    anim = new Anim();
    overlayAnim: Anim | undefined;

    spritesheets: string[];
    layers: number[];
    animations: Animation[];
    defaultAnim: string;

    useScaling = true

    constructor(anmPath: string, resourcePath: string) {
        this.fullPath = pathlib.resolve(anmPath);
        this.path = pathlib.parse(this.fullPath);
        this.resourcePath = resourcePath;

        const fileContents = fs.readFileSync(this.fullPath, { encoding: "utf-8" });
        if (!fileContents) {
            throw Error("Invalid anm2! " + this.path);
        }

        const parser = new XML.Parser<Anm2>([
            'Spritesheet',
            'Layer',
            'Null',
            'Event',
            'Animation',
            'LayerAnimation',
            'NullAnimation',
            'Trigger',
            'Frame',
        ]);
        this.tree = parser.decode(fileContents).AnimatedActor;

        this.spritesheets = this.tree.Content.Spritesheets.Spritesheet.map(x => x.attrib.Path);
        this.layers = this.tree.Content.Layers.Layer.map(x => x.attrib.SpritesheetId);
        this.animations = this.tree.Animations.Animation;
        this.defaultAnim = this.tree.Animations.attrib.DefaultAnimation;
    }

    getAnim(name: string) {
        if (!name) {
            return undefined;
        }
        return this.animations.find(x => x.attrib.Name === name);
    }

    setAnimation(animName?: string) {
        const anim = this.getAnim(animName ?? this.defaultAnim);
        if (!anim) {
            throw Error(`Invalid animation! ${animName ?? '[Default]'}`);
        }
        this.anim.set(anim);
    }

    setOverlay(animName: string) {
        const anim = this.getAnim(animName);
        if (!anim) {
            throw Error(`Invalid animation! ${animName}`);
        }
        if (!this.overlayAnim) {
            this.overlayAnim = new Anim();
        }
        this.overlayAnim.set(anim);
    }

    static getFrameNode(frames: Frame[], frameNumber: number) {
        let currFrame = 0
        for (const frame of frames) {
            currFrame += +frame.attrib.Delay;
            if (currFrame > frameNumber) {
                return frame;
            }
        }

        return frames[frames.length - 1];
    }

    extractFrame(frameLayers: LayerAnimation[], frameNumber: number): Image[] {
        const imgs: Image[] = [];
        let ignoreCount = 0
        for (const layer of frameLayers) {
            if (!layer.attrib.Visible) {
                ignoreCount += 1;
                continue;
            }

            const frame = Config.getFrameNode(layer.Frame ?? [], frameNumber);
            if (!frame.attrib.Visible) {
                ignoreCount += 1;
                continue;
            }

            let image: string | undefined = this.spritesheets[this.layers[layer.attrib.LayerId]] ?? "";

            let sheetPath = undefined;
            if (typeof image === 'string') {
                sheetPath = image;
                image = pathlib.resolve(pathlib.join(this.path.dir, image))
                if (!image || !fs.existsSync(image)) {
                    image = image.replace(/.*resources/, this.resourcePath);
                    image = fs.existsSync(image) ? image : undefined;
                }
            }

            if (image !== undefined) {
                // Here's the anm specs
                imgs.push({
                    image,
                    pivot: { // applied before rotation
                        x: -frame.attrib.XPivot!,
                        y: -frame.attrib.YPivot!,
                    },
                    rotation: frame.attrib.Rotation,
                    position: { // applied after rotation
                        x: frame.attrib.XPosition,
                        y: frame.attrib.YPosition,
                    },
                    crop: {
                        x: frame.attrib.XCrop!,
                        y: frame.attrib.YCrop!,
                    },
                    scale: {
                        x: this.useScaling ? frame.attrib.XScale / 100 : 1,
                        y: this.useScaling ? frame.attrib.YScale / 100 : 1,
                    },
                    width: frame.attrib.Width!,
                    height: frame.attrib.Height!,
                });
            }
            else {
                console.log("Bad image! ", sheetPath, image);
            }
        }

        if (imgs.length === 0) {
            console.log("Frame could not be generated from animation due to", ignoreCount > 0 ? "visibility" : "missing files");
        }

        return imgs;
    }

    async render({
        noScale=false,
        trim=true,
    }: {
        noScale?: boolean;
        trim?: boolean;
    } = {}) {
        const imgs: Array<Image & {
            sourceImage?: Sharp;
            finalRect?: Rect;
        }> = [];

        const root = Config.getFrameNode(this.anim.rootFrames, this.anim.frame);
        if (root?.attrib.Visible) {
            imgs.push(...this.extractFrame(this.anim.frameLayers, this.anim.frame));
        }

        if (this.overlayAnim) {
            imgs.push(...this.extractFrame(this.overlayAnim.frameLayers, this.overlayAnim.frame));
        }

        if (imgs.length === 0) {
            return undefined;
        }

        const imgCache: Record<string, Sharp> = {}

        // Fetch each layer and establish the needed dimensions for the final image
        let completeRect: Rect = {
            left: Number.POSITIVE_INFINITY, right:  Number.NEGATIVE_INFINITY,
            top:  Number.POSITIVE_INFINITY, bottom: Number.NEGATIVE_INFINITY,
        };
        for (const img of imgs) {
            // Load the Image
            let imgBlob: Sharp | undefined = undefined;
            if (typeof img.image === 'string') {
                imgBlob = imgCache[img.image];
                if (imgBlob === undefined) {
                    imgBlob = sharp(img.image);
                    imgCache[img.image] = imgBlob;
                    // imgBlob.save(image);
                }
            }
            else {
                imgBlob = sharp(img.image);
            }

            const cropRect: Rect = {
                left:   img.crop.x,
                right:  img.crop.x + img.width,
                top:    img.crop.y,
                bottom: img.crop.y + img.height,
            };

            let mat: matrix.Matrix;
            [ img.sourceImage, mat ] = transform(imgBlob.extract({
                left:   cropRect.left,
                top:    cropRect.top,
                width:  cropRect.right  - cropRect.left,
                height: cropRect.bottom - cropRect.top,
            }), {
                rotation: img.rotation,
                scale: noScale ? undefined : img.scale,
                translate: img.pivot,
            });

            // reset translation
            cropRect.right -= cropRect.left;
            cropRect.bottom -= cropRect.top;
            cropRect.left = cropRect.top = 0;
            const fRect = matrix.applyToPoints(mat, [
                { x: 0,              y: 0},
                { x: cropRect.right, y: 0 },
                { x: 0,              y: cropRect.bottom },
                { x: cropRect.right, y: cropRect.bottom },
            ]).reduce<Rect>((r, p) => {
                combineRects(r, {
                    left: p.x,
                    right: p.x,
                    top: p.y,
                    bottom: p.y,
                });
                return r;
            }, {
                left: Number.POSITIVE_INFINITY, right:  Number.NEGATIVE_INFINITY,
                top:  Number.POSITIVE_INFINITY, bottom: Number.NEGATIVE_INFINITY,
            });

            // apply final translation
            fRect.left   += img.position.x;
            fRect.right  += img.position.x;
            fRect.top    += img.position.y;
            fRect.bottom += img.position.y;

            combineRects(completeRect, fRect);
            img.finalRect = fRect;
        }

        // Create the destination
        let renderedImg = sharp({
            create: {
                background: "#0000",
                width:  completeRect.right  - completeRect.left,
                height: completeRect.bottom - completeRect.top,
                channels: 4,
            },
        });

        // Paint all the layers to it
        for (const img of imgs) {
            // Transfer the crop area to the pixmap
            renderedImg = renderedImg.composite([{
                input: await img.sourceImage!.toBuffer(),
                left: img.finalRect!.left - completeRect.left,
                top:  img.finalRect!.top  - completeRect.top,
            }]);
        }

        if (root) {
            [ renderedImg ] = transform(renderedImg, {
                rotation: root.attrib.Rotation,
                scale: noScale ? undefined : {
                    x: root.attrib.XScale / 100,
                    y: root.attrib.YScale / 100,
                },
                translate: {
                    x: root.attrib.XPosition,
                    y: root.attrib.YPosition,
                },
            });
        }

        return renderedImg;
    }
}
