import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    threads: false,
    setupFiles: ['./src/setupTests.ts'],
  },
});
