import js from '@eslint/js';
import unicorn from 'eslint-plugin-unicorn';
import sonarjs from 'eslint-plugin-sonarjs';

// Mirrors recard's config (the code came from there) minus its browser-only
// sections. Understudy is Node-only until a web target lands.
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
    // The web example's own app code runs in the page.
    files: ['examples/web/**/*.js'],
    languageOptions: { globals: { document: 'readonly', globalThis: 'readonly' } },
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
