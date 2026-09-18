import {
  RegExpMatcher,
  englishDataset,
  englishRecommendedTransformers,
} from "obscenity";
import { readFileSync } from "node:fs";
import { request as httpsRequest } from "node:https";
import { rootCertificates } from "node:tls";

const UPSTREAM_URL = "https://www.ballix.net/whatsplaying/?user=aarongraybill";
const SAFE_IMAGE_HOST = /^lastfm-img\d*\.(?:freetls\.fastly\.net|akamaized\.net)$/i;
const SAFE_TRACK_HOST = /^(?:www\.)?last\.fm$/i;
const SAFE_IMAGE_PATH = /^\/i\/u\//;
const SAFE_IMAGE_TYPES = new Set([
  "image/gif",
  "image/jpeg",
  "image/png",
  "image/webp",
]);
const FILTERED_TITLE = "Title not displayed";
const FILTERED_ARTIST = "Artist not displayed";
const MAX_RESPONSE_BYTES = 64 * 1024;
const MAX_IMAGE_BYTES = 512 * 1024;
const upstreamIntermediate = readFileSync(
  new URL("./certs/sectigo-r36.pem", import.meta.url),
  "utf8",
);
const upstreamCertificateAuthorities = [
  ...rootCertificates,
  upstreamIntermediate,
];

const profanityMatcher = new RegExpMatcher({
  ...englishDataset.build(),
  ...englishRecommendedTransformers,
});

function cleanText(value, maxLength) {
  if (typeof value !== "string") {
    return "";
  }

  return value
    .replace(/[\u0000-\u001f\u007f]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, maxLength);
}

function safeUrl(value, allowedHost) {
  if (typeof value !== "string") {
    return null;
  }

  try {
    const url = new URL(value);
    return url.protocol === "https:" && allowedHost.test(url.hostname)
      ? url.toString()
      : null;
  } catch {
    return null;
  }
}

function pickImage(images) {
  if (!images || typeof images !== "object") {
    return null;
  }

  for (const size of ["extralarge", "large", "medium", "small"]) {
    const image = safeImageSource(images[size]);
    if (image) {
      return image;
    }
  }

  return null;
}

function albumArtProxyUrl(image) {
  return image
    ? `/api/album-art?src=${encodeURIComponent(image)}`
    : null;
}

function safeImageSource(value) {
  const image = safeUrl(value, SAFE_IMAGE_HOST);

  if (!image) {
    return null;
  }

  const url = new URL(image);
  return !url.username
    && !url.password
    && (!url.port || url.port === "443")
    && SAFE_IMAGE_PATH.test(url.pathname)
    && !url.search
    && !url.hash
    ? url.toString()
    : null;
}

function imageContentType(value) {
  if (typeof value !== "string") {
    return null;
  }

  const contentType = value.split(";", 1)[0].trim().toLowerCase();
  return SAFE_IMAGE_TYPES.has(contentType) ? contentType : null;
}

function isNowPlaying(value) {
  return value === true || value === "true" || value === "1";
}

function setJsonHeaders(response, cacheControl) {
  response.set("Cache-Control", cacheControl);
  response.set("Content-Type", "application/json; charset=utf-8");
  response.set("X-Content-Type-Options", "nosniff");
}

function loadUpstreamJson() {
  return new Promise((resolve, reject) => {
    const request = httpsRequest(
      UPSTREAM_URL,
      {
        ca: upstreamCertificateAuthorities,
        headers: {
          Accept: "application/json",
          "User-Agent": "aarongraybill.com recently-played widget",
        },
        method: "GET",
        timeout: 3500,
      },
      (upstreamResponse) => {
        if (upstreamResponse.statusCode !== 200) {
          upstreamResponse.resume();
          reject(new Error(`Upstream response ${upstreamResponse.statusCode}`));
          return;
        }

        let body = "";
        upstreamResponse.setEncoding("utf8");
        upstreamResponse.on("data", (chunk) => {
          body += chunk;
          if (Buffer.byteLength(body, "utf8") > MAX_RESPONSE_BYTES) {
            request.destroy(new Error("Upstream response was too large"));
          }
        });
        upstreamResponse.on("end", () => {
          try {
            resolve(JSON.parse(body));
          } catch (error) {
            reject(error);
          }
        });
      },
    );

    request.on("timeout", () => {
      request.destroy(new Error("Upstream request timed out"));
    });
    request.on("error", reject);
    request.end();
  });
}

function loadImageBytes(url) {
  return new Promise((resolve, reject) => {
    const request = httpsRequest(
      url,
      {
        headers: {
          Accept: "image/webp,image/png,image/jpeg,image/gif,image/*;q=0.8",
          "User-Agent": "aarongraybill.com album-art proxy",
        },
        method: "GET",
        timeout: 3500,
      },
      (upstreamResponse) => {
        if (upstreamResponse.statusCode !== 200) {
          upstreamResponse.resume();
          reject(new Error(`Album-art response ${upstreamResponse.statusCode}`));
          return;
        }

        const contentType = imageContentType(upstreamResponse.headers["content-type"]);
        if (!contentType) {
          upstreamResponse.resume();
          reject(new Error("Album-art response was not a supported image"));
          return;
        }

        const declaredLength = Number(upstreamResponse.headers["content-length"]);
        if (Number.isFinite(declaredLength) && declaredLength > MAX_IMAGE_BYTES) {
          upstreamResponse.resume();
          reject(new Error("Album-art response was too large"));
          return;
        }

        const chunks = [];
        let receivedBytes = 0;
        let responseWasRejected = false;

        upstreamResponse.on("data", (chunk) => {
          receivedBytes += chunk.length;

          if (receivedBytes > MAX_IMAGE_BYTES) {
            responseWasRejected = true;
            request.destroy(new Error("Album-art response was too large"));
            return;
          }

          chunks.push(chunk);
        });
        upstreamResponse.on("end", () => {
          if (!responseWasRejected) {
            resolve({
              body: Buffer.concat(chunks),
              contentType,
            });
          }
        });
      },
    );

    request.on("timeout", () => {
      request.destroy(new Error("Album-art request timed out"));
    });
    request.on("error", reject);
    request.end();
  });
}

export function createWhatsPlayingHandler({
  loadUpstream = loadUpstreamJson,
  matcher = profanityMatcher,
  logger = console,
} = {}) {
  return async (request, response) => {
    if (request.method !== "GET") {
      response.set("Allow", "GET");
      setJsonHeaders(response, "no-store");
      response.status(405).json({ error: "Method not allowed" });
      return;
    }

    try {
      const upstream = await loadUpstream();
      const rawTitle = cleanText(upstream.name, 160);
      const rawArtist = cleanText(upstream.artist, 120);

      if (!rawTitle) {
        throw new Error("Upstream response did not include a song title");
      }

      const titleWasFiltered = matcher.hasMatch(rawTitle);
      const artistWasFiltered = Boolean(rawArtist) && matcher.hasMatch(rawArtist);
      const song = {
        title: titleWasFiltered ? FILTERED_TITLE : rawTitle,
        titleWasFiltered,
        artist: artistWasFiltered ? FILTERED_ARTIST : rawArtist,
        artistWasFiltered,
        image: albumArtProxyUrl(pickImage(upstream.image)),
        url: titleWasFiltered || artistWasFiltered
          ? null
          : safeUrl(upstream.url, SAFE_TRACK_HOST),
        nowPlaying: isNowPlaying(upstream.nowplaying),
      };

      setJsonHeaders(
        response,
        "public, max-age=60, s-maxage=60, stale-while-revalidate=300",
      );
      response.status(200).json(song);
    } catch (error) {
      logger.error("Unable to load recently played music", error);
      setJsonHeaders(response, "public, max-age=30, s-maxage=30");
      response.status(503).json({
        error: "Recently played music is temporarily unavailable",
      });
    }
  };
}

export const whatsPlayingHandler = createWhatsPlayingHandler();

export function createAlbumArtHandler({
  loadImage = loadImageBytes,
  logger = console,
} = {}) {
  return async (request, response) => {
    if (request.method !== "GET") {
      response.set("Allow", "GET");
      setJsonHeaders(response, "no-store");
      response.status(405).json({ error: "Method not allowed" });
      return;
    }

    const source = typeof request.query?.src === "string"
      ? safeImageSource(request.query.src)
      : null;

    if (!source) {
      setJsonHeaders(response, "no-store");
      response.status(400).json({ error: "Invalid album-art source" });
      return;
    }

    try {
      const image = await loadImage(source);
      response.set(
        "Cache-Control",
        "public, max-age=86400, s-maxage=31536000, stale-while-revalidate=86400, immutable",
      );
      response.set("Content-Length", String(image.body.length));
      response.set("Content-Type", image.contentType);
      response.set("Cross-Origin-Resource-Policy", "same-origin");
      response.set("X-Content-Type-Options", "nosniff");
      response.status(200).send(image.body);
    } catch (error) {
      logger.error("Unable to proxy album art", error);
      setJsonHeaders(response, "no-store");
      response.status(502).json({ error: "Album art is temporarily unavailable" });
    }
  };
}

export const albumArtHandler = createAlbumArtHandler();
