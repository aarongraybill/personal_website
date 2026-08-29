import assert from "node:assert/strict";
import test from "node:test";
import { createWhatsPlayingHandler } from "./whats-playing.js";

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
  assert.equal(response.body.artist, "Olivia Rodrigo");
  assert.equal(response.body.nowPlaying, true);
  assert.match(response.body.url, /^https:\/\/www\.last\.fm\//);
  assert.match(response.body.image, /^https:\/\/lastfm-img\./);
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
