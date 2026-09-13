if (utils::packageVersion("systemfonts") < "1.2.0") {
  stop("create_favicon.R requires systemfonts 1.2.0 or newer")
}

font_path <- file.path(
  "..",
  "..",
  "fonts",
  "Atkinson Hyperlegible Next",
  "otf",
  "AtkinsonHyperlegibleNext-Regular.otf"
)

if (!file.exists(font_path)) {
  stop("Could not find the canonical Atkinson Hyperlegible Next Regular font")
}

font_path <- normalizePath(font_path)
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
