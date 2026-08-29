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
const FILTERED_TITLE = "Title not displayed";
const MAX_RESPONSE_BYTES = 64 * 1024;
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

  for (const size of ["large", "extralarge", "medium", "small"]) {
    const image = safeUrl(images[size], SAFE_IMAGE_HOST);
    if (image) {
      return image;
    }
  }

  return null;
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

      if (!rawTitle) {
        throw new Error("Upstream response did not include a song title");
      }

      const titleWasFiltered = matcher.hasMatch(rawTitle);
      const song = {
        title: titleWasFiltered ? FILTERED_TITLE : rawTitle,
        titleWasFiltered,
        artist: cleanText(upstream.artist, 120),
        image: pickImage(upstream.image),
        url: titleWasFiltered ? null : safeUrl(upstream.url, SAFE_TRACK_HOST),
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
