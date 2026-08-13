import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Provide a `jest` alias for older tests that still use `jest.fn()`
(globalThis as any).jest = vi;
