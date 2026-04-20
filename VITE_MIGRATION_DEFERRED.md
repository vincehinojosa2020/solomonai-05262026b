# Vite Migration — Deferred (P1 → blocked on platform)

## Status
**DEFERRED**. Do not attempt without Emergent platform engineering alignment.

## Why Snyk recommends it
React Scripts (CRA) is unmaintained. Its pinned-but-outdated transitive deps (`nth-check`, `postcss`, `webpack-dev-server`, `serialize-javascript`, `underscore`, `@tootallnate/once`) keep surfacing new CVEs. Migrating the build tool to Vite removes these dependencies entirely.

## Why we cannot migrate today

`/app/frontend/craco.config.js` integrates two **webpack-specific** Emergent platform plugins:

1. **Visual Edits plugin** (`/app/frontend/plugins/visual-edits/`)
   - `dev-server-setup.js` — registers express middleware on the CRA dev server
   - `babel-metadata-plugin.js` — Babel plugin that tags every JSX node with source-map metadata used by the click-to-edit UI in the Emergent preview
   - **Impact if removed:** The "edit this element" arrow in the Emergent preview stops working.

2. **Health Check plugin** (`/app/frontend/plugins/health-check/`)
   - `webpack-health-plugin.js` — taps into webpack compiler hooks (`afterEmit`, `done`, `failed`)
   - `health-endpoints.js` — exposes `/__health` on the dev server
   - **Impact if removed:** Emergent's build-health signalling breaks.

Both plugins use webpack APIs (`compiler.hooks`, `devServer.setupMiddlewares`, `chunks`, `stats`). Vite uses Rollup for production builds and esbuild for dev, with a different plugin API. A naive port would lose functionality.

## Path forward (for Emergent platform team)

1. Port `visual-edits/babel-metadata-plugin.js` → a `vite-plugin-visual-edits` that hooks into `@vitejs/plugin-react`'s Babel pipeline (it accepts `babel.plugins`).
2. Port `dev-server-setup.js` → a Vite plugin using the `configureServer` hook (Express middleware works directly).
3. Port `webpack-health-plugin.js` → a Vite plugin using `buildStart`, `buildEnd`, `closeBundle` hooks.
4. Replace `craco.config.js` with `vite.config.js`:
   ```js
   import { defineConfig } from 'vite';
   import react from '@vitejs/plugin-react';
   import path from 'path';
   import { visualEdits, healthCheck } from '@emergent/vite-plugins';

   export default defineConfig({
     plugins: [react(), visualEdits(), healthCheck()],
     resolve: { alias: { '@': path.resolve(__dirname, 'src') } },
     server: { port: 3000, host: '0.0.0.0' },
     build: { outDir: 'build' },
   });
   ```
5. Codemod `process.env.REACT_APP_*` → `import.meta.env.VITE_*` (only 1 call site in the current codebase: `StripePaymentRequestButton.jsx`).
6. Move `public/index.html` → `index.html` at project root, remove `%PUBLIC_URL%` tokens.
7. Switch `package.json` scripts: `vite`, `vite build`, `vite preview`.
8. Migrate tests from `react-scripts test` (Jest) → `vitest`.

## App-level changes we CAN do safely now (already done)

- Pinned vulnerable transitive deps via yarn `resolutions` (underscore, serialize-javascript, nth-check ~2.1.1, postcss, @tootallnate/once).
- Removed server-side `python-jose`, `ecdsa`.
- All SAST/DAST hardening complete.

## Recommended escalation

Open a platform ticket against Emergent:
> "Publish `@emergent/vite-plugins` package (visual-edits + health-check) so customer apps can migrate off CRA as recommended by Snyk SCA."

Until that package exists, this app stays on CRA + yarn resolutions and accepts `eslint@8.x` + `inflight@1.0.6` as dev-only risks.
