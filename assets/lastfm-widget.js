(() => {
  function albumArtUrl(value) {
    if (typeof value !== "string") {
      return null;
    }

    try {
      const url = new URL(value, window.location.origin);
      return url.origin === window.location.origin
        && url.pathname === "/api/album-art"
        ? url.toString()
        : null;
    } catch {
      return null;
    }
  }

  const section = document.getElementById("lastfm-section");
  const widget = document.getElementById("lastfm-widget");

  if (!section || !widget) {
    return;
  }

  const art = document.getElementById("lastfm-art");
  const artPlaceholder = document.getElementById("lastfm-art-placeholder");
  const status = document.getElementById("lastfm-status");
  const track = document.getElementById("lastfm-track");
  const artist = document.getElementById("lastfm-artist");
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 4500);

  fetch("/api/whats-playing", {
    headers: { Accept: "application/json" },
    signal: controller.signal
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Recently played music is unavailable");
      }

      return response.json();
    })
    .then((song) => {
      if (!song || typeof song.title !== "string" || !song.title.trim()) {
        return;
      }

      status.textContent = song.nowPlaying ? "Listening now" : "Recently listened";
      track.textContent = song.title;
      artist.textContent = typeof song.artist === "string" ? song.artist : "";

      if (typeof song.url === "string" && song.url) {
        track.href = song.url;
        track.target = "_blank";
        track.rel = "noopener noreferrer";
        track.setAttribute("aria-label", `${song.title} by ${song.artist || "unknown artist"} on Last.fm`);
      }

      const image = albumArtUrl(song.image);
      if (image) {
        art.src = image;
        art.alt = `Album art for ${song.title}${song.artist ? ` by ${song.artist}` : ""}`;
        art.hidden = false;
      } else {
        artPlaceholder.hidden = false;
      }

      section.hidden = false;
    })
    .catch(() => {
      // The music section is optional; leave it hidden if unavailable.
    })
    .finally(() => window.clearTimeout(timeout));
})();
