export { isDeepStrictEqual as deepEqual } from 'util';

export type ValueOf<T> = T[keyof T];

export type IsEqual<T, U> =
    (<G>() => G extends T ? 1 : 0) extends
    (<G>() => G extends U ? 1 : 0) ?
        T extends U ?
            U extends T ? true : false
        : false
    : false;

type DecayImpl<T> =
    T extends number ? number :
    T extends string ? string :
    T extends boolean ? boolean :
    T extends null ? null :
    T extends undefined ? undefined :
    T extends (...args: Array<any>) => any ? T :
    T extends Array<infer U>|ReadonlyArray<infer U> ? Array<Decay<U>> :
    Decay<keyof T> extends number ? Record<number, Decay<ValueOf<T>>> :
    {
        -readonly [K in keyof T]: Decay<T[K]>;
    };

/**
 * Simplifies the type T recursively as much as possible into primitive types
 * Inspired by C++'s `std::decay<T>`
 * Can be used in generic functions to fluently use `as const` values
 */
export type Decay<T> = T extends infer U ? DecayImpl<U> : never;

type ChoiceImpl<T> = {
    [K in keyof T]: Pick<T, K>;
}[keyof T];

export type Choice<T> = T extends infer U ? ChoiceImpl<U> : never;

/**
 * Used to constrain `as const` literals to match a certain unconstrained type
 */
export function constrainLiteral<T>() {
    return function<V extends T>(v: Readonly<V>): V {
        return v;
    };
}

export type Point = {
    x: number;
    y: number;
};

export type Size = {
    width: number;
    height: number;
};

export type Vector2 = [ number, number ];

export namespace Vector {

export function add(a: Point, b: Point): Point {
    return {
        x: a.x + b.x,
        y: a.y + b.y,
    };
}

export function sub(a: Point, b: Point): Point {
    return {
        x: a.x - b.x,
        y: a.y - b.y,
    };
}

export function mul(a: Point, s: number): Point {
    return {
        x: a.x * s,
        y: a.y * s,
    };
}

export function dot(a: Point, b: Point): number {
    return a.x * b.x + a.y * b.y;
}

}

export function* range(n: number, m?: number): IterableIterator<number> {
    const min = m !== undefined ? n : 0;
    const max = m !== undefined ? m : n;
    for (let i = min; i < max; ++i) {
        yield i;
    }
}

export const printf = console.log.bind(console);

export function printSectionBreak(): void {
    printf(Array.from(range(50)).map(() => "-").join(""));
}


export function bitFill(count: number): number {
    return (1 << count) - 1;
}


export function bitGet(bits: number, startBit: number, count: number): number {
    bits = bits >> startBit;
    bits &= bitFill(count)
    return bits;
}


export function bitSet(bits: number, sourceBits: number, startBit: number, count: number): number {
    sourceBits = bitGet(sourceBits, 0, count) << startBit;
    bits &= ~(bitFill(count) << startBit);
    return bits | sourceBits;
}

export function checkFloat(s: string | number) {
    return !Number.isNaN(Number.parseFloat(s + ''));
}


export function checkInt(s: string | number) {
    return checkFloat(s) && (+s | 0) === +s;
}

export function vectorFromAngle(angle: number): Vector2 {
    const radians = angle * (Math.PI / 180);
    return [ Math.cos(radians), Math.sin(radians) ];
}


export function angleFromVector(x: number, y: number): number {
    return Math.atan2(y, x) * (180 / Math.PI);
}
