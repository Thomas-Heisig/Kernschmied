// Minimal Vitest globals for editor/TS support when dev-deps aren't installed.
declare namespace VitestGlobals {
  type Fn = (...args: any[]) => any;
}

declare const describe: (name: string, fn: VitestGlobals.Fn) => void;
declare const it: (name: string, fn: VitestGlobals.Fn) => void;
declare const test: (name: string, fn: VitestGlobals.Fn) => void;
declare const expect: any;
declare const beforeEach: (fn: VitestGlobals.Fn) => void;
declare const afterEach: (fn: VitestGlobals.Fn) => void;
declare const vi: any;

declare module 'vitest' {
  export const describe: typeof describe;
  export const it: typeof it;
  export const test: typeof test;
  export const expect: typeof expect;
  export const beforeEach: typeof beforeEach;
  export const afterEach: typeof afterEach;
  export const vi: typeof vi;
}

export {};
