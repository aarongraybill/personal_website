if (utils::packageVersion("systemfonts") < "1.2.0") {
  stop("create_favicon.R requires systemfonts 1.2.0 or newer")
}

font_dir <- tempfile("atkinson-hyperlegible-")
dir.create(font_dir)
on.exit(unlink(font_dir, recursive = TRUE), add = TRUE)

# Download the actual font file. It is used only while this script is running;
# the generated SVG contains paths and has no runtime font dependency.
systemfonts::get_from_google_fonts(
  "Atkinson Hyperlegible",
  dir = font_dir,
  woff2 = FALSE
)

font_files <- list.files(
  font_dir,
  pattern = "\\.(otf|ttf)$",
  full.names = TRUE,
  recursive = TRUE,
  ignore.case = TRUE
)
regular_font <- font_files[
  grepl("regular", basename(font_files), ignore.case = TRUE) &
    !grepl("(bold|italic)", basename(font_files), ignore.case = TRUE)
]

if (length(regular_font) != 1L) {
  stop("Could not identify the downloaded Atkinson Hyperlegible Regular font")
}

font_path <- regular_font[[1L]]
font_size <- 126

glyph_path <- function(character, x, baseline, anchor = c("start", "end")) {
  anchor <- match.arg(anchor)
  glyph <- systemfonts::glyph_info(
    character,
    path = font_path,
    index = 0,
    size = font_size
  )
  outline <- systemfonts::glyph_outline(
    glyph$index,
    path = font_path,
    index = 0,
    size = font_size,
    tolerance = 0.05
  )

  if (anchor == "end") {
    shaped <- systemfonts::shape_string(
      character,
      path = font_path,
      index = 0,
      size = font_size,
      res = 72
    )
    x <- x - shaped$metrics$width[[1L]]
  }

  contours <- split(outline, outline$contour)
  commands <- vapply(contours, function(contour) {
    coordinates <- paste(
      sprintf("%.2f %.2f", x + contour$x, baseline - contour$y),
      collapse = " L "
    )
    paste0("M ", coordinates, " Z")
  }, character(1))

  paste(commands, collapse = " ")
}

a_path <- glyph_path("A", x = 5, baseline = 99.54, anchor = "start")
g_path <- glyph_path("G", x = 164.67, baseline = 169.17, anchor = "end")

favicon_svg <- c(
  "<?xml version='1.0' encoding='UTF-8' ?>",
  "<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180' viewBox='0 0 180 180'>",
  "  <g fill='#55CE58' fill-rule='evenodd' stroke='#000D4D' stroke-width='10.08'",
  "     stroke-linejoin='round' paint-order='stroke fill'>",
  sprintf("    <path d='%s'/>", a_path),
  sprintf("    <path d='%s'/>", g_path),
  "  </g>",
  "</svg>"
)

writeLines(favicon_svg, "favicon.svg")

# magick::image_read_svg depends on rsvg, so we library it to hint
# to renv that this code depends on rsvg
library(rsvg)
svg_fav <- magick::image_read_svg("favicon.svg", width = 96, height = 96)
svg_fav <- magick::image_background(svg_fav, "none")
magick::image_write(svg_fav, "../../favicon.ico", format = "ico")
