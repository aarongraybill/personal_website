#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
font_stage_dir="$(mktemp -d "${TMPDIR:-/tmp}/personal-website-fonts.XXXXXX")"
trap 'rm -rf "$font_stage_dir"' EXIT

fetch_font() {
  source_url="$1"
  destination="$2"
  expected_sha256="$3"
  staged_file="$font_stage_dir/download"

  curl -fsSL "$source_url" -o "$staged_file"
  printf '%s  %s\n' "$expected_sha256" "$staged_file" | shasum -a 256 -c -
  mkdir -p "$(dirname "$project_dir/$destination")"
  install -m 0644 "$staged_file" "$project_dir/$destination"
}

alegreya_commit='4e974a60e8278f045db8e341817dbc61abf6158e'
alegreya_base="https://raw.githubusercontent.com/google/fonts/$alegreya_commit/ofl/alegreyasanssc"

fetch_font "$alegreya_base/OFL.txt" \
  'fonts/Alegreya Sans SC/OFL.txt' \
  '0677891e6a143f297350d260ad766ad33bfc18ed5fa4f213acf648d6b597ec1a'
fetch_font "$alegreya_base/AlegreyaSansSC-Light.ttf" \
  'fonts/Alegreya Sans SC/AlegreyaSansSC-Light.ttf' \
  '64088b83af22b58e945f56c494e39fffd9b4565ed2bddbbd849963ae2bdda4e3'

next_commit='7925f50f649b3813257faf2f4c0b381011f434f1'
next_base="https://raw.githubusercontent.com/googlefonts/atkinson-hyperlegible-next/$next_commit"

fetch_font "$next_base/OFL.txt" \
  'fonts/Atkinson Hyperlegible Next/OFL.txt' \
  'aca6a428580965d2297d1b718042dd427c2a9443ece3b0d02d758e161e0c4030'
fetch_font "$next_base/fonts/otf/AtkinsonHyperlegibleNext-Regular.otf" \
  'fonts/Atkinson Hyperlegible Next/otf/AtkinsonHyperlegibleNext-Regular.otf' \
  '64fbbff682bdb28e7cd0e237b23c13a6e5d8d2aeb88d06fb0c80635fcefce0bc'
fetch_font "$next_base/fonts/otf/AtkinsonHyperlegibleNext-Bold.otf" \
  'fonts/Atkinson Hyperlegible Next/otf/AtkinsonHyperlegibleNext-Bold.otf' \
  'd74e11da52d35d9bff3786c04bbfde172a36674ef876b18660f39bf6410b9aab'
fetch_font "$next_base/fonts/otf/AtkinsonHyperlegibleNext-Italic.otf" \
  'fonts/Atkinson Hyperlegible Next/otf/AtkinsonHyperlegibleNext-Italic.otf' \
  '1166726f941f3de4b163dc5e455c2988a1b47734265704766e126cac3f0590f9'
fetch_font "$next_base/fonts/otf/AtkinsonHyperlegibleNext-BoldItalic.otf" \
  'fonts/Atkinson Hyperlegible Next/otf/AtkinsonHyperlegibleNext-BoldItalic.otf' \
  '640a604f2ce2225bafcd237ca16825ff08e2372672367c110fc9c3825a6137da'
fetch_font "$next_base/fonts/webfonts/AtkinsonHyperlegibleNext%5Bwght%5D.woff2" \
  'fonts/Atkinson Hyperlegible Next/webfonts/AtkinsonHyperlegibleNext[wght].woff2' \
  'abde1ad5cf78b9ac575ef90d991f2e9101eb0b3b6668bde9a00e2e1e27d99afd'
fetch_font "$next_base/fonts/webfonts/AtkinsonHyperlegibleNext-Italic%5Bwght%5D.woff2" \
  'fonts/Atkinson Hyperlegible Next/webfonts/AtkinsonHyperlegibleNext-Italic[wght].woff2' \
  '34491c5a87f711d314637962f69267d28c7df3ed498082c990cdfbbc02ebf3f2'

mono_commit='154d50362016cc3e873eb21d242cd0772384c8f9'
mono_base="https://raw.githubusercontent.com/googlefonts/atkinson-hyperlegible-next-mono/$mono_commit"

fetch_font "$mono_base/OFL.txt" \
  'fonts/Atkinson Hyperlegible Mono/OFL.txt' \
  '1ebb31cf7393164f20d10c1d48406cddb5314feff8465531cf1e4ba37e9dd740'
fetch_font "$mono_base/fonts/otf/AtkinsonHyperlegibleMono-Regular.otf" \
  'fonts/Atkinson Hyperlegible Mono/otf/AtkinsonHyperlegibleMono-Regular.otf' \
  'ccc9c3d7cd20a327f982cc26136681e5065d10bcfdaf80deff97d9c41dee998d'

cormorant_commit='6a386aadc0a33dd3d810b833d9c5105345cbb0e6'
cormorant_base="https://raw.githubusercontent.com/google/fonts/$cormorant_commit/ofl/cormorantgaramond"

fetch_font "$cormorant_base/OFL.txt" \
  'fonts/Cormorant Garamond/OFL.txt' \
  '60700d351cac4650c51f3f9db318d2a420f8b45052dba2715eb5fec41f0f6956'
fetch_font "$cormorant_base/CormorantGaramond-Medium.ttf" \
  'fonts/Cormorant Garamond/ttf/CormorantGaramond-Medium.ttf' \
  'c20509089926d9db5e5487fa1c06bca90e2563d31dc2d09670bb9f43205288f2'
fetch_font "$cormorant_base/CormorantGaramond-Bold.ttf" \
  'fonts/Cormorant Garamond/ttf/CormorantGaramond-Bold.ttf' \
  '2884048acfab68270fe2e5166dbdda0adbbb1032f31fe4928112167454395398'
fetch_font "$cormorant_base/CormorantGaramond-Italic.ttf" \
  'fonts/Cormorant Garamond/ttf/CormorantGaramond-Italic.ttf' \
  '50fccbdc299c232d25dd66868a2a2b55fd0e85d6238a58638986c5f66deca1bf'
fetch_font "$cormorant_base/CormorantGaramond-BoldItalic.ttf" \
  'fonts/Cormorant Garamond/ttf/CormorantGaramond-BoldItalic.ttf' \
  'a262693f28727bc2e50859f6a3cc94992e85b4df2ffec7ca3b846b6b5ef0c985'

bash "$project_dir/scripts/verify-fonts.sh"
