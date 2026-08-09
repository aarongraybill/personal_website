image_dir <- "images"
dir.create(image_dir, recursive = TRUE, showWarnings = FALSE)

redwood_url <- file.path(image_dir, "redwood_leaf_mask.png")


img <-
  magick::image_read(redwood_url) |>
  # rembg masks use white for foreground; the geometry code below expects the
  # branch to be black on white so it can locate the stem in the bottom row.
  magick::image_negate() |>
  magick::image_background("white", flatten = TRUE) |>
  magick::image_convert(type = "Bilevel") |>
  magick::image_rotate(-90) |>
  magick::image_trim()

# Center the visible end of the stem, rather than balancing the number of black
# pixels on either side of the image midpoint. Once the stem is centered, a
# 180-degree copy has exactly the same attachment point.
img_inf <- magick::image_info(img)
last_row <- magick::image_data(img, channels = "gray")[1, , img_inf$height]
stem_pixels <- which(as.integer(last_row) == 0L)

if (length(stem_pixels) == 0L) {
  stop("No black stem pixels were found in the bottom row after rotation")
}

stem_center <- mean(range(stem_pixels))

# Pixel coordinates are one-based, so the center of a width-w image is
# (w + 1) / 2. Add padding to only the side needed to put the stem there.
padding_difference <- round(img_inf$width + 1 - 2 * stem_center)
left_padding <- max(padding_difference, 0L)
right_padding <- max(-padding_difference, 0L)

if (left_padding + right_padding > 0L) {
  padded_width <- img_inf$width + left_padding + right_padding
  canvas <- magick::image_blank(
    width = padded_width,
    height = img_inf$height,
    color = "white"
  )
  img <- magick::image_composite(
    canvas,
    img,
    operator = "over",
    offset = sprintf("+%d+0", left_padding)
  )
}

# resize so it's easier to do math on
img <- magick::image_resize(img, "149x")


img_rot <- img |> magick::image_rotate(180)

# image_append joins the full-size images directly, without montage geometry,
# resizing, spacing, or an extra background around the seam.
tile_unit <- magick::image_append(c(img, img_rot), stack = TRUE)

horizontal_stripes = 50
vertical_stripes = 16
tile_width <- magick::image_info(tile_unit)$width
row_height <- magick::image_info(tile_unit)$height
row_width <- horizontal_stripes * tile_width
stagger <- tile_width %/% 2

# Build one extra tile so the staggered crop still contains image content across
# its full width rather than exposing a blank strip at the edge.
horizontal_stripe <- tile_unit |> rep(horizontal_stripes + 1)
for (i in seq_along(horizontal_stripe)){
  if (i %% 2 == 0){
    horizontal_stripe[i] <- magick::image_flop(horizontal_stripe[i])
  }
}
horizontal_stripe <- magick::image_append(horizontal_stripe, stack = FALSE)

aligned_row <- magick::image_crop(
  horizontal_stripe,
  geometry = sprintf("%dx%d+0+0", row_width, row_height)
)
staggered_row <- magick::image_crop(
  horizontal_stripe,
  geometry = sprintf("%dx%d+%d+0", row_width, row_height, stagger)
)

rows <- rep(
  c(aligned_row, staggered_row),
  ceiling(vertical_stripes / 2)
)[seq_len(vertical_stripes)]
canvas <- magick::image_append(rows, stack = TRUE)


target_width <- 1200
target_height <- 630

# The trees currently point vertically. The angle between the vertical side of
# the output rectangle and its diagonal is atan(width / height), equivalently
# acos(height / diagonal). Positive ImageMagick angles rotate clockwise.
rot_angle <- atan2(target_width, target_height) * 180 / pi

output_canvas <-
  canvas |>
  magick::image_background("white") |>
  magick::image_rotate(rot_angle) |>
  magick::image_crop(
    geometry = sprintf("%dx%d", target_width, target_height),
    gravity = "center"
  )

output_canvas |>
  magick::image_negate() |>
  magick::image_convert(type = "Bilevel") |>
  magick::image_write(
    file.path(image_dir, "redwood_mask.png"),
    format = "png"
  )
