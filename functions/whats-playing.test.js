import assert from "node:assert/strict";
import test from "node:test";
import {
  createAlbumArtHandler,
  createWhatsPlayingHandler,
} from "./whats-playing.js";

function createResponse() {
  return {
    headers: {},
    statusCode: null,
    body: null,
    set(name, value) {
      this.headers[name] = value;
      return this;
    },
    status(code) {
      this.statusCode = code;
      return this;
    },
    json(value) {
      this.body = value;
      return this;
    },
    send(value) {
      this.body = value;
      return this;
    },
  };
}

test("returns a safe, cacheable song payload", async () => {
  const response = createResponse();
  const handler = createWhatsPlayingHandler({
    loadUpstream: async () => ({
      artist: "Olivia Rodrigo",
      image: {
        large: "https://lastfm-img.freetls.fastly.net/i/u/174s/cover.jpg",
      },
      name: "serena joy",
      nowplaying: "true",
      url: "https://www.last.fm/music/Olivia+Rodrigo/_/serena+joy",
    }),
  });

  await handler({ method: "GET" }, response);

  assert.equal(response.statusCode, 200);
  assert.equal(response.body.title, "serena joy");
  assert.equal(response.body.titleWasFiltered, false);
  assert.equal(response.body.artist, "Olivia Rodrigo");
  assert.equal(response.body.artistWasFiltered, false);
  assert.equal(response.body.nowPlaying, true);
  assert.match(response.body.url, /^https:\/\/www\.last\.fm\//);
  const image = new URL(response.body.image, "https://www.aarongraybill.com");
  assert.equal(image.origin, "https://www.aarongraybill.com");
  assert.equal(image.pathname, "/api/album-art");
  assert.equal(
    image.searchParams.get("src"),
    "https://lastfm-img.freetls.fastly.net/i/u/174s/cover.jpg",
  );
  assert.match(response.headers["Cache-Control"], /stale-while-revalidate=300/);
});

test("withholds an obscene song title", async () => {
  const response = createResponse();
  const handler = createWhatsPlayingHandler({
    loadUpstream: async () => ({
      artist: "Example Artist",
      image: {},
      name: "fuuuuuuuck this song",
      nowplaying: null,
      url: "https://www.last.fm/music/example",
    }),
  });

  await handler({ method: "GET" }, response);

  assert.equal(response.statusCode, 200);
  assert.equal(response.body.title, "Title not displayed");
  assert.equal(response.body.titleWasFiltered, true);
  assert.equal(response.body.url, null);
});

test("withholds an obscene artist name", async () => {
  const response = createResponse();
  const handler = createWhatsPlayingHandler({
    loadUpstream: async () => ({
      artist: "Fuuuuuuuck Ensemble",
      image: {},
      name: "A safe title",
      nowplaying: null,
      url: "https://www.last.fm/music/Fuuuuuuuck+Ensemble/_/A+safe+title",
    }),
  });

  await handler({ method: "GET" }, response);

  assert.equal(response.statusCode, 200);
  assert.equal(response.body.title, "A safe title");
  assert.equal(response.body.titleWasFiltered, false);
  assert.equal(response.body.artist, "Artist not displayed");
  assert.equal(response.body.artistWasFiltered, true);
  assert.equal(response.body.url, null);
});

test("rejects untrusted image and track URLs", async () => {
  const response = createResponse();
  const handler = createWhatsPlayingHandler({
    loadUpstream: async () => ({
      artist: "Example Artist",
      image: { large: "https://example.com/tracker.gif" },
      name: "A safe title",
      url: "https://example.com/not-lastfm",
    }),
  });

  await handler({ method: "GET" }, response);

  assert.equal(response.statusCode, 200);
  assert.equal(response.body.image, null);
  assert.equal(response.body.url, null);
});

test("fails quietly when the upstream service is unavailable", async () => {
  const response = createResponse();
  const handler = createWhatsPlayingHandler({
    loadUpstream: async () => {
      throw new Error("Upstream response 502");
    },
    logger: { error() {} },
  });

  await handler({ method: "GET" }, response);

  assert.equal(response.statusCode, 503);
  assert.match(response.body.error, /temporarily unavailable/);
});

test("allows only GET requests", async () => {
  const response = createResponse();
  const handler = createWhatsPlayingHandler();

  await handler({ method: "POST" }, response);

  assert.equal(response.statusCode, 405);
  assert.equal(response.headers.Allow, "GET");
});

test("proxies trusted album art with cache and security headers", async () => {
  const response = createResponse();
  const source = "https://lastfm-img.freetls.fastly.net/i/u/174s/cover.jpg";
  const body = Buffer.from("fake jpeg bytes");
  let loadedSource = null;
  const handler = createAlbumArtHandler({
    loadImage: async (url) => {
      loadedSource = url;
      return { body, contentType: "image/jpeg" };
    },
  });

  await handler({ method: "GET", query: { src: source } }, response);

  assert.equal(response.statusCode, 200);
  assert.equal(loadedSource, source);
  assert.equal(response.body, body);
  assert.equal(response.headers["Content-Type"], "image/jpeg");
  assert.equal(response.headers["Content-Length"], String(body.length));
  assert.equal(response.headers["Cross-Origin-Resource-Policy"], "same-origin");
  assert.match(response.headers["Cache-Control"], /s-maxage=31536000/);
});

test("rejects untrusted album-art proxy sources without fetching them", async () => {
  const response = createResponse();
  let loadWasCalled = false;
  const handler = createAlbumArtHandler({
    loadImage: async () => {
      loadWasCalled = true;
      throw new Error("This should not run");
    },
  });

  await handler({
    method: "GET",
    query: { src: "https://example.com/tracker.gif" },
  }, response);

  assert.equal(response.statusCode, 400);
  assert.equal(loadWasCalled, false);
  assert.equal(response.headers["Cache-Control"], "no-store");
});

test("rejects trusted hosts outside the Last.fm image path", async () => {
  const response = createResponse();
  let loadWasCalled = false;
  const handler = createAlbumArtHandler({
    loadImage: async () => {
      loadWasCalled = true;
      throw new Error("This should not run");
    },
  });

  await handler({
    method: "GET",
    query: { src: "https://lastfm-img.freetls.fastly.net/not-album-art.jpg" },
  }, response);

  assert.equal(response.statusCode, 400);
  assert.equal(loadWasCalled, false);
});

test("allows only GET requests for album art", async () => {
  const response = createResponse();
  const handler = createAlbumArtHandler();

  await handler({ method: "POST", query: {} }, response);

  assert.equal(response.statusCode, 405);
  assert.equal(response.headers.Allow, "GET");
});

test("fails quietly when album art is unavailable", async () => {
  const response = createResponse();
  const handler = createAlbumArtHandler({
    loadImage: async () => {
      throw new Error("Upstream response 503");
    },
    logger: { error() {} },
  });

  await handler({
    method: "GET",
    query: {
      src: "https://lastfm-img.freetls.fastly.net/i/u/174s/cover.jpg",
    },
  }, response);

  assert.equal(response.statusCode, 502);
  assert.match(response.body.error, /temporarily unavailable/);
  assert.equal(response.headers["Cache-Control"], "no-store");
});
