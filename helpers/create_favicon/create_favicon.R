library(systemfonts)
library(svglite)

s <- svglite::svgstring(
  web_fonts = list('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible&display=swap'),
  width = 2.5,
  height = 2.5,
  bg = "transparent")
scale = 10.5
#https://stackoverflow.com/a/19920666
par(mar = c(0,0,0,0), bg = NA)
plot(c(0), c(0), ann = F, bty = 'n', type = 'n', xaxt = 'n', yaxt = 'n', bg = "black")
TeachingDemos::shadowtext(x = -1.02, y = .97, "A", cex = scale,
                              col = "#55CE58", bg = "#000D4D", r = .06,
     family = "Atkinson+Hyperlegible", adj = c(0,1))
TeachingDemos::shadowtext(x = 1.1, y = -.95, "G", cex = scale,
                          col = "#55CE58", bg = "#000D4D", r = .06,
                          family = "Atkinson+Hyperlegible", adj = c(1,0))
writeLines(s(), 'favicon.svg')
invisible(dev.off())

svg_fav <- magick::image_read_svg('favicon.svg', width = 32, height = 32)
svg_fav <- magick::image_background(svg_fav, "none")
#print(svg_fav)
magick::image_write(svg_fav, '../../favicon.ico', format = 'ico')
