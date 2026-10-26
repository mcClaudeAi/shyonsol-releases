# Shilluminati Online for Android (Solana dApp Store)

This folder builds the Android app: a web shell (a WebView app, made with Solana Mobile's `webshell` CLI) that opens
shyonsol.io full screen. Inside it the phone's own wallet connects through Mobile Wallet Adapter (the site loads
`assets/vendor/wmwa.js` only when the user agent says "Solana Mobile Web Shell", see `assets/wallets.js`).
The build runs on GitHub (Actions > Build Android app) and attaches the signed APK to a Release.

- `twa-manifest.json`: the app's package id and version. Bump `appVersionCode` (and `appVersionName`) for every new upload to the store.
- `res/`: our launcher icon, splash and colors, copied over the generated defaults on every build.
- The signing key is never in this repo. It comes from two repository secrets:
  - `ANDROID_KEYSTORE_B64`: the keystore file, base64
  - `ANDROID_KEYSTORE_PASSWORD`: its password
- Without those secrets the build still runs, signed with a throwaway key, and the Release is marked TEST. Don't submit a TEST build.
- Every future update must be signed with the same key, or the store will refuse it.
- The earlier Trusted Web Activity build is retired: browsers are blocking the local wallet link it needs, and the store recommends the web shell.
