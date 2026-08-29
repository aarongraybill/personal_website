import { onRequest } from "firebase-functions/v2/https";
import { whatsPlayingHandler } from "./whats-playing.js";

export const whatsPlaying = onRequest(
  {
    region: "us-west1",
    timeoutSeconds: 5,
    memory: "256MiB",
    maxInstances: 3,
    concurrency: 40,
    cors: false,
  },
  whatsPlayingHandler,
);
