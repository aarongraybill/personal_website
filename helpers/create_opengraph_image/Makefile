.DEFAULT_GOAL := all

PYTHON := $(firstword $(wildcard renv/python/virtualenvs/*/bin/python))
R_LIBRARY := $(firstword $(wildcard renv/library/*/R-*/*))
RSCRIPT := R_LIBS_USER="$(abspath $(R_LIBRARY))" Rscript --vanilla
IMAGE_DIR := images
ORIGINAL := $(IMAGE_DIR)/redwood_leaf_original.jpg
LEAF_MASK := $(IMAGE_DIR)/redwood_leaf_mask.png
REDWOOD_MASK := $(IMAGE_DIR)/redwood_mask.png
BATIK_CANVAS := $(IMAGE_DIR)/batik_canvas.png
OPENGRAPH := $(IMAGE_DIR)/opengraph.png

.PHONY: all
all: $(OPENGRAPH)

$(IMAGE_DIR):
	mkdir -p $@

$(LEAF_MASK): create_rembg_mask.py | $(IMAGE_DIR)
	$(PYTHON) create_rembg_mask.py
	@test -f $(ORIGINAL)

$(REDWOOD_MASK): $(LEAF_MASK) make_redwood_mask.R | $(IMAGE_DIR)
	$(RSCRIPT) make_redwood_mask.R

$(BATIK_CANVAS): $(REDWOOD_MASK) batik.py image_helpers.py | $(IMAGE_DIR)
	$(PYTHON) batik.py

$(OPENGRAPH): $(BATIK_CANVAS) compose_opengraph.py ../../assets/me-800.jpg
	$(PYTHON) compose_opengraph.py
