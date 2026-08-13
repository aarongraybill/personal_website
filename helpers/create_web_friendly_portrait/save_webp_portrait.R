# Generate the responsive portrait assets used by index.qmd. The script resolves
# paths relative to itself, so it works from the repository root, RStudio, or the
# helper directory.
script_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
script_path <- if (length(script_arg)) {
  normalizePath(sub("^--file=", "", script_arg[[1]]))
} else {
  normalizePath("save_webp_portrait.R")
}

helper_dir <- dirname(script_path)
# Loading this project explicitly makes the helper runnable from any working
# directory. Disabling renv's temporary sandbox avoids an unnecessary lock for
# this standalone script; package isolation still comes from the project library.
Sys.setenv(
  RENV_PROJECT = helper_dir,
  RENV_CONFIG_SANDBOX_ENABLED = "FALSE"
)
source(file.path(helper_dir, "renv", "activate.R"))

library(webp)
library(tiff)
library(jpeg)

repo_root <- normalizePath(file.path(helper_dir, "..", ".."))
source_path <- file.path(helper_dir, "portrait.tif")
output_dir <- file.path(repo_root, "assets")

widths <- c(480L, 800L)
jpeg_quality <- 0.85 # jpeg::writeJPEG uses a 0-1 scale.
webp_quality <- 82   # webp::write_webp uses a 0-100 scale.

if (!file.exists(source_path)) {
  stop("Source portrait not found: ", source_path)
}

# Bilinear interpolation keeps this helper limited to the jpeg and webp
# packages while producing smoother downscaling than nearest-neighbour sampling.
resize_bilinear <- function(image, target_width) {
  source_height <- dim(image)[1]
  source_width <- dim(image)[2]
  channels <- dim(image)[3]
  target_height <- as.integer(round(source_height * target_width / source_width))

  x <- seq(1, source_width, length.out = target_width)
  y <- seq(1, source_height, length.out = target_height)
  x0 <- floor(x)
  x1 <- pmin(x0 + 1L, source_width)
  y0 <- floor(y)
  y1 <- pmin(y0 + 1L, source_height)
  x_weight <- x - x0
  y_weight <- y - y0

  row0 <- rep(y0, each = target_width)
  row1 <- rep(y1, each = target_width)
  col0 <- rep(x0, times = target_height)
  col1 <- rep(x1, times = target_height)
  wx <- rep(x_weight, times = target_height)
  wy <- rep(y_weight, each = target_width)

  resized <- array(0, dim = c(target_height, target_width, channels))

  for (channel in seq_len(channels)) {
    top_left <- image[cbind(row0, col0, channel)]
    top_right <- image[cbind(row0, col1, channel)]
    bottom_left <- image[cbind(row1, col0, channel)]
    bottom_right <- image[cbind(row1, col1, channel)]

    values <-
      top_left * (1 - wx) * (1 - wy) +
      top_right * wx * (1 - wy) +
      bottom_left * (1 - wx) * wy +
      bottom_right * wx * wy

    resized[, , channel] <- matrix(
      values,
      nrow = target_height,
      ncol = target_width,
      byrow = TRUE
    )
  }

  resized
}

portrait <- readTIFF(source_path)

if (length(dim(portrait)) != 3L || dim(portrait)[3] != 3L) {
  stop("Expected an RGB JPEG source image.")
}

if (max(widths) > dim(portrait)[2]) {
  stop("Requested output width exceeds the source width; refusing to upscale.")
}

for (width in widths) {
  resized <- resize_bilinear(portrait, width)
  jpeg_path <- file.path(output_dir, sprintf("me-%d.jpg", width))
  webp_path <- file.path(output_dir, sprintf("me-%d.webp", width))

  writeJPEG(resized, target = jpeg_path, quality = jpeg_quality)
  write_webp(resized, target = webp_path, quality = webp_quality)

  message(sprintf(
    "Wrote %s and %s (%d x %d)",
    basename(jpeg_path),
    basename(webp_path),
    dim(resized)[2],
    dim(resized)[1]
  ))
}
