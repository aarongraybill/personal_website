library(dplyr)
library(fluctuator)

tf <- tempfile(pattern = "temp_svg")

download.file("https://upload.wikimedia.org/wikipedia/commons/a/af/Puzzle-4.svg",tf)
# import example map
SVG <- read_svg(tf)

info_df <- SVG@summary %>% as.data.frame()

pieces_df <- info_df %>% 
  filter(grepl("^path",id))

nodes <- pieces_df$id

# Get Colors On Brand
colors <- ggchameleon:::gen_palette(length(nodes))

for (i in seq_along(nodes)){
  cur_sty <- get_attributes(SVG, node = nodes[i],node_attr = "id") %>% pull(style)
  cur_fill <- stringi::stri_extract(cur_sty, regex = "fill:#[0-9a-fA-F]+")
  
  SVG <- set_attributes(
    SVG,
    node = nodes[i],
    node_attr = "id",
    attr = "style",
    pattern = cur_fill,
    replacement = glue::glue("fill:{colors[i]}")
  )
}


write_svg(SVG, 'puzzle.svg')
