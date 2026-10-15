# Shilluminati Online for Android (Solana dApp Store)

This folder builds the Android app: a Trusted Web Activity that opens shyonsol.io full screen.
The build runs on GitHub (Actions > Build Android app) and attaches the signed APK to a Release.

- `twa-manifest.json`: the app's name, colors, icons and version. Bump `appVersionCode` (and `appVersionName`) for every new upload to the store.
- The signing key is never in this repo. It comes from two repository secrets:
  - `ANDROID_KEYSTORE_B64`: the keystore file, base64
  - `ANDROID_KEYSTORE_PASSWORD`: its password
- Without those secrets the build still runs, signed with a throwaway key, and the Release is marked TEST. Don't submit a TEST build.
- shyonsol.io serves `/.well-known/assetlinks.json` with this key's fingerprint, which is what lets the app open the site with no browser bar.
