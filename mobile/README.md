# Cosmic Memory Mobile

Native iOS/Android companion built with Capacitor from the static assets in `www/`.

## Features

- offline-first local memory storage;
- remember, search/recall, tags, and importance;
- owner-controlled deletion and full local erase;
- JSON export/import for portable user-owned copies;
- responsive dark interface designed for phones and tablets;
- Android and iOS native shells generated from the same source.

## Local development

```bash
cd mobile
npm install
npx cap add android
npx cap add ios
npx cap copy
```

Open the generated native projects with Android Studio or Xcode as needed.

## Distribution

GitHub Actions builds an installable Android APK and an unsigned iOS Simulator `.app` archive. Shipping to a physical iPhone, TestFlight, or the App Store requires Apple Developer signing/provisioning credentials. See `docs/DISTRIBUTION.md`.

The mobile companion uses a lightweight local JSON store. It does not claim binary compatibility with the canonical SQLite database. Use JSON export/import or an application-specific bridge when exchanging records with the Python library.
