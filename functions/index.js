import { onRequest } from "firebase-functions/v2/https";
import {
  albumArtHandler,
  whatsPlayingHandler,
} from "./whats-playing.js";

const sharedOptions = {
  region: "us-west1",
  timeoutSeconds: 5,
  memory: "256MiB",
  maxInstances: 3,
  concurrency: 40,
  cors: false,
};

export const whatsPlaying = onRequest(
  sharedOptions,
  whatsPlayingHandler,
);

export const albumArt = onRequest(
  sharedOptions,
  albumArtHandler,
);
