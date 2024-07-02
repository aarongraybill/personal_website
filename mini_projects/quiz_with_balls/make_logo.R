library(dplyr)
library(ggplot2)
library(ggchameleon)

# Here lies my probably wrong and mega janky interpretation of
# how a ball might slide down a curve based on:
# https://physics.stackexchange.com/a/617110
# All errors are my own
f <- function(x) 1/sqrt(2*pi)*exp(-x^2/2)
f_prime <- function(x) 1/sqrt(2*pi)*exp(-x^2/2)*(-x)
f_double_prime <- function(x) {
  (1/sqrt(2*pi)*exp(-x^2/2)*(-x)*(-x))+(-1/sqrt(2*pi)*exp(-x^2/2))
}
x <- 0.1
x_dot <- 0

x_double_dot <- function(x, x_dot, g = 1){
  numerator = f_prime(x)*(x_dot^2 * f_double_prime(x) + g)
  denominator = 1 + ((f_prime(x))^2)
  
  return(-numerator/denominator)
}
x0 <- 0
x_dot0 <- 0.1
simulate <- function(x0, x_dot0, g = 1, max_iter = 10000, delta_t = .001){
  x_list <- c(x0)
  x <- x0
  x_dot <- x_dot0
  for (i in 1:max_iter){
    xdd <- x_double_dot(x,x_dot,g)
    x_dot <- x_dot+(xdd * delta_t)
    x <- x+(x_dot*delta_t)
    x_list <- c(x_list,x)
  }
  
  return(x_list)
}

x_list <- simulate(x0, x_dot0)

df <-
  data.frame(x = x_list,
             y = f(x_list)) |> 
  filter(row_number()%%800 == 1) |> 
  filter(x<3.5) |> 
  mutate(x_nudge = 0,
         y_nudge = 0) |> 
  mutate(rn = row_number())

y_nudge <- c(13,15, 16, 21, 26, 32, 30, 19, 15, 15)/1000
df$y_nudge[1:length(y_nudge)] <- y_nudge

  
line_data <- 
  data.frame(x = seq(min(df$x)-.25, max(df$x)+.1, length.out = 100))|> 
  mutate(y = dnorm(x))

p <- ggplot(df, aes(x+x_nudge, y+y_nudge)) + 
  geom_area(data = line_data, aes(x=x,y=y), 
            alpha = .4, 
            fill = the$main_palette$main,
            color = the$main_palette$main) + 
  geom_point(aes(alpha = rn^3), size=8, color = the$main_palette$secondary)+
  geom_point(aes(), shape =1, size = 8, color = the$main_palette$main)+
  #geom_point(aes(x=x,y=y, alpha = abs(x)), size = 8, color = "pink")+
  theme_void()+
  scale_alpha_continuous(range = c(.1,1))+
  labs(alpha = NULL)+
  theme(legend.position = "none")

ggsave(filename  = "pdf_with_balls.svg", plot = p, width = 4, height = 4)
