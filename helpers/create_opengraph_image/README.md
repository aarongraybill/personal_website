# Create The Opengraph Image

## Context

The image here uses leaves from a coast redwood tree to form a repeating 
pattern that is loosely inspired by the [*parang*](https://en.wikipedia.org/wiki/Parang_(batik))
batik motif. The repeating pattern is meant to emulate the tjap (stamps) that
are sometimes used in batik (though admittedly not for the parang pattern).

There's a lot of code that tries to simulate batik crack patterns, though its
effect of the final image is admittedly limited.

## Running

Get the dependenices through `renv::restore()`. Then run `make` in the terminal.
Generated image files are written to `images/`.

When you first run the code, it will likely download a very large ML model (~1Gb)
for removing the background in the image.
