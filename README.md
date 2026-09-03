# Personal website

This is a Quarto website hosted with Firebase Hosting. The recently played
music widget is served by the pinned `whatsPlaying` and `albumArt` Firebase
functions.

## One-time Firebase setup

The Firebase project uses an Artifact Registry cleanup policy for `us-west1`.
Function build artifacts older than seven days are deleted automatically.

This policy is persistent and does not need to run during regular deployments.
To create or update it, run:

```bash
npx firebase-tools@latest functions:artifacts:setpolicy \
  --location us-west1 \
  --days 7
```

## Local preview

```bash
make preview
```

This installs the function dependencies, renders the website, and starts the
Firebase Hosting and Functions emulators. Quarto continues watching the source
files and re-renders them when they change, while the Hosting emulator serves
the contents of `_site` and routes `/api/whats-playing` and `/api/album-art` to
the local widget functions. Open the Hosting URL printed in the terminal
(normally `http://127.0.0.1:5000`) and refresh it after changes. Press `Ctrl+C`
to stop both the Quarto watcher and Firebase emulators.

## Render and deploy

Run the complete deployment pipeline from the project root:

```bash
make deploy
```

This runs the following commands:

```bash
npm --prefix functions ci
npm --prefix functions test
quarto render
npx firebase-tools@latest deploy --only hosting
```

This performs a clean installation of the function dependencies, runs the
function tests, renders the Quarto website into `_site`, and deploys Firebase
Hosting. Because both widget functions are pinned to the Hosting release,
Firebase also deploys those functions.

For initial authentication:

```bash
make login
```
