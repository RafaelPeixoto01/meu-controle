import js from '@eslint/js'
import globals from 'globals'
import tseslint from 'typescript-eslint'
import reactHooks from 'eslint-plugin-react-hooks'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  // Artefatos compilados (.js em src/) e build ficam fora do lint
  globalIgnores(['dist', 'src/**/*.js']),
  {
    files: ['src/**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
    ],
    languageOptions: {
      globals: globals.browser,
    },
    rules: {
      // CR-035: regra que teria prevenido o CR-034 — sempre error
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
      // CR-035: warn — padrão pré-existente em 8 componentes (reset de estado
      // de formulário na abertura de modais); refatorar é risco fora do escopo
      'react-hooks/set-state-in-effect': 'warn',
    },
  },
])
