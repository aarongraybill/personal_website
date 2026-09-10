# Font sources

This directory is the canonical source for every font used by the website and
CV. `scripts/font-manifests/fonts.sha256` fixes the exact bytes expected by the
build.

The reproducible open-font inputs are pinned to these upstream Git commits:

- Alegreya Sans SC: `google/fonts` at
  `4e974a60e8278f045db8e341817dbc61abf6158e`
- Atkinson Hyperlegible Next: `googlefonts/atkinson-hyperlegible-next` at
  `7925f50f649b3813257faf2f4c0b381011f434f1`
- Atkinson Hyperlegible Mono: `googlefonts/atkinson-hyperlegible-next-mono` at
  `154d50362016cc3e873eb21d242cd0772384c8f9`
- Cormorant Garamond: `google/fonts` at
  `6a386aadc0a33dd3d810b833d9c5105345cbb0e6`

`make fonts` re-downloads those files and verifies every font.

`make font-assets` verifies this directory and copies the Atkinson Hyperlegible
Next variable webfonts and license into `assets/`. Quarto runs that local,
offline step automatically before every render. Alegreya Sans SC and Atkinson
Hyperlegible Mono are used only in the PDF CV, so they are not copied into the
web assets.
