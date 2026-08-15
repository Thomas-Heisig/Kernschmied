declare module 'clsx' {
  type ClassValue = string | number | boolean | null | undefined | { [key: string]: any } | ClassValue[];
  function clsx(...inputs: ClassValue[]): string;
  export default clsx;
}

// Minimal local declaration to help TypeScript resolve the module during editing/build.
