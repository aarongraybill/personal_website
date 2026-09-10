#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"

bash scripts/verify-fonts.sh

install -m 0644 \
  'fonts/Atkinson Hyperlegible Next/webfonts/AtkinsonHyperlegibleNext[wght].woff2' \
  assets/AtkinsonHyperlegibleNext-Variable.woff2
install -m 0644 \
  'fonts/Atkinson Hyperlegible Next/webfonts/AtkinsonHyperlegibleNext-Italic[wght].woff2' \
  assets/AtkinsonHyperlegibleNext-VariableItalic.woff2
install -m 0644 \
  'fonts/Atkinson Hyperlegible Next/OFL.txt' \
  assets/AtkinsonHyperlegibleNext-OFL.txt

cmp -s \
  'fonts/Atkinson Hyperlegible Next/webfonts/AtkinsonHyperlegibleNext[wght].woff2' \
  assets/AtkinsonHyperlegibleNext-Variable.woff2
cmp -s \
  'fonts/Atkinson Hyperlegible Next/webfonts/AtkinsonHyperlegibleNext-Italic[wght].woff2' \
  assets/AtkinsonHyperlegibleNext-VariableItalic.woff2
cmp -s \
  'fonts/Atkinson Hyperlegible Next/OFL.txt' \
  assets/AtkinsonHyperlegibleNext-OFL.txt
