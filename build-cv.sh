#!/usr/bin/env bash
# Enter strict mode where bash exits if there's an error
set -euo pipefail

# setup path to latex executable
export PATH="$HOME/Library/TinyTeX/bin/universal-darwin:$PATH"

# Make the PDF binary reproducible by pinning TeX's timestamps and trailer IDs.
export SOURCE_DATE_EPOCH=0
export FORCE_SOURCE_DATE=1
export TZ=UTC

# build pdf
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error Graybill_CV/main.tex
# clean up intermediates
latexmk -cd -c Graybill_CV/main.tex

# copy resulting pdf to project root
cp Graybill_CV/main.pdf Graybill_CV.pdf
