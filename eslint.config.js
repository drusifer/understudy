import js from '@eslint/js';
import unicorn from 'eslint-plugin-unicorn';
import sonarjs from 'eslint-plugin-sonarjs';

// Mirrors recard's config (the code came from there) minus its browser-only
// sections. Two files run in a browser: the web example's app and the
// watch page's script.
export default [
  {
    ignores: ['node_modules/**', 'build/**', 'seed/**'],
  },
  js.configs.recommended,
  unicorn.configs['flat/recommended'],
  sonarjs.configs.recommended,
  {
    languageOptions: {
      ecmaVersion: 2024,
      sourceType: 'module',
      globals: {
        console: 'readonly',
        process: 'readonly',
        Buffer: 'readonly',
        fetch: 'readonly',
        setTimeout: 'readonly',
        clearTimeout: 'readonly',
        setInterval: 'readonly',
        clearInterval: 'readonly',
        structuredClone: 'readonly',
        crypto: 'readonly',
        performance: 'readonly',
        URL: 'readonly',
        URLSearchParams: 'readonly',
        AbortController: 'readonly',
        AbortSignal: 'readonly',
      },
    },
    rules: {
      // Same reasons as recard: null is a deliberate JSON-safe sentinel.
      // camelCase file names are the convention carried over from recard.
      'unicorn/filename-case': 'off',
      'unicorn/no-null': 'off',
      'unicorn/consistent-class-member-order': 'off',
      'unicorn/no-break-in-nested-loop': 'off',
      'no-unused-vars': ['error', { ignoreRestSiblings: true }],
      'sonarjs/no-unused-vars': 'off',
    },
  },
  {
    // The watch page's script runs in the browser (sprint 4, ARCH_SPRINT4 §7).
    // The dashboard's page too (sprint 6, ARCH_SPRINT6 §7).
    files: ['src/watch/page.mjs', 'src/dashboard/page.mjs'],
    languageOptions: { globals: { document: 'readonly', globalThis: 'readonly' } },
  },
  {
    // Browser tests pass functions to page.evaluate(); those run in the page.
    files: ['tests/browser/**/*.js'],
    languageOptions: { globals: { document: 'readonly' } },
  },
  {
    files: ['tests/**/*.js', 'tests/**/*.mjs'],
    rules: {
      'sonarjs/no-duplicate-string': 'off',
      'sonarjs/cognitive-complexity': 'off',
      'unicorn/consistent-function-scoping': 'off',
      'unicorn/no-await-expression-member': 'off',
    },
  },
];
