PAGE_WIDTH=5
PAGE_HEIGHT=1
NEEDLE_FRAC = 1/100
N_STRIPES = 5
# ensure there's an odd number of stripes plotted
stopifnot(N_STRIPES %% 2 == 1)

needle_width = PAGE_WIDTH * NEEDLE_FRAC
stripe_width = PAGE_WIDTH / N_STRIPES

# ensure needles are shorter than stripes
stopifnot(needle_width < stripe_width)

# https://en.wikipedia.org/wiki/Buffon%27s_needle_problem
# seed set according to theoretical prob of needle crossing
set.seed((2/pi) * (needle_width / stripe_width))

N=5000
sim_df <- data.frame(
  # center of needle
  x = runif(N, 0, PAGE_WIDTH),
  y = runif(N, 0, PAGE_HEIGHT),
  # orientation
  theta = runif(N, 0, 2*pi),
  r = needle_width
)


shading <- seq(from = 0, to = PAGE_WIDTH, by = stripe_width)
stripe_1_starts <- shading[1:length(shading) %% 2 == 1]
stripe_1_ends <- shading[1:length(shading) %% 2 == 0]

stripe_2_starts <- stripe_1_ends[-length(stripe_1_ends)]
stripe_2_ends <- stripe_1_starts[-1]

library(ggplot2)
background_p <- 
  ggplot()+
  geom_rect(aes(xmin = stripe_1_starts, xmax = stripe_1_ends, ymin = 0, ymax = PAGE_HEIGHT), fill = "#EEEEEE")+
  geom_rect(aes(xmin = stripe_2_starts, xmax = stripe_2_ends, ymin = 0, ymax = PAGE_HEIGHT), fill = "#FFFFFF")+
  geom_spoke(data = sim_df, aes(x = x, y = y, angle = theta, radius = r),
             col = "#000D4D", alpha = .3, linewidth = needle_width * 2)+
  coord_cartesian(xlim = c(0, PAGE_WIDTH), ylim = c(0, PAGE_HEIGHT))+
  theme_void()+
  scale_x_continuous(expand = c(0, 0))+
  scale_y_continuous(expand = c(0, 0))


# Now Render Email
email <- readLines('email.txt')
chars <- strsplit(email, '')[[1]]
text_df <- data.frame(letter = chars)
text_df$x <- seq(from = 0, to = PAGE_WIDTH*.98, length.out = nrow(df))

y_scale <- PAGE_WIDTH/PAGE_HEIGHT * 2
text_df$y <- sin(df$x*2*pi/PAGE_WIDTH * 4)/y_scale
text_df$y <- text_df$y - mean(text_df$y) + (PAGE_HEIGHT / 2)

library(showtext)
library(curl)
library(jsonlite)
font_add_google("Intel One Mono",
                db_cache = F)
showtext_auto()
showtext_opts(dpi = 300)

p <- 
  background_p+
  geom_text(data = text_df, aes(x=x,y=y,label = letter),
            size = PAGE_WIDTH, color = "#000D4D", alpha = .7,
            hjust = 0, family = "Intel One Mono")


ggsave('email_image.png',p, width = PAGE_WIDTH, height = PAGE_HEIGHT)

