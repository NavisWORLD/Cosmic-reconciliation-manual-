# Cross-Platform Distribution Manual

Cosmic Reconciliation Memory v1.2.0 adds a first-party binary distribution pipeline. The repository remains the source of truth; GitHub Actions builds platform-specific packages from that source and publishes them to the v1.2.0 GitHub Release after the distribution workflow passes.

## Release assets

### Windows

- `CosmicMemory-Windows-Setup.exe` — one-click Inno Setup installer. Installs the desktop memory manager, creates Start Menu integration, optionally creates a desktop shortcut, and can launch the app at the end of installation.
- `CosmicMemory.exe` — portable single-file desktop app for users who do not want an installer.

The Windows GUI opens local SQLite memory databases, stores and recalls memories, displays integrity/status information, and initializes/syncs/verifies portable USB memory.

### macOS

- `CosmicMemory-macOS.dmg` — drag/open distribution image containing `CosmicMemory.app`.
- `CosmicMemory-macOS.app.zip` — zipped `.app` bundle for direct extraction/testing.

The open-source build is not Apple-notarized. macOS may therefore show Gatekeeper warnings until a maintainer signs and notarizes the app with an Apple Developer identity.

### Android

- `CosmicMemory-Android.apk` — installable debug-signed APK built from the mobile companion.

The mobile app provides local memory creation, token-overlap recall, tags, importance, deletion, JSON export/import, and a vault view. The Python/SQLite package remains the canonical research implementation, while the mobile client is deliberately offline-first and lightweight.

### iOS

- `CosmicMemory-iOS-Simulator.app.zip` — unsigned iOS Simulator `.app` build.
- `mobile/` — complete Capacitor iOS/Android source used to generate the native projects.

A real iPhone `.ipa`, TestFlight build, or App Store package requires Apple Developer signing credentials and provisioning that cannot be embedded in a public repository. The workflow intentionally does not fake or bypass Apple's signing process. A maintainer can add signing secrets later and replace the simulator artifact with a signed archive.

## Build pipeline

`.github/workflows/distribution.yml` performs four independent builds:

1. Windows: PyInstaller → `CosmicMemory.exe` → Inno Setup installer.
2. macOS: PyInstaller → `CosmicMemory.app` → DMG + zipped app.
3. Android: Capacitor → generated Android project → Gradle APK.
4. iOS: Capacitor → generated iOS project → unsigned simulator `.app`.

Pull requests run all four builds as validation. A qualifying push to `main` runs the same build matrix and, only if every platform job succeeds, publishes/refreshes GitHub Release `v1.2.0` with the resulting assets.

## Desktop source

- `src/cosmic_reconciliation/desktop_app.py` — GUI implementation.
- `desktop/CosmicMemory.py` — packaging entry point.
- `desktop/windows_installer.iss` — Windows installer definition.

The installed Python package also provides:

```bash
cosmic-memory-desktop
```

for launching the GUI from a Python environment.

## Mobile source

`mobile/www/` contains the shared mobile user interface. Capacitor wraps those assets in native Android and iOS shells during CI. Mobile data stays local to the app unless the owner explicitly exports it.

## Release integrity

GitHub Actions refuses the release if an expected binary is missing. The release job expects at least:

- Windows portable EXE;
- Windows installer EXE;
- macOS DMG;
- macOS `.app` ZIP;
- Android APK;
- iOS Simulator `.app` ZIP.

This packaging layer is separate from the portable-memory integrity manifests inside the core project. Users should still use `cosmic-memory usb-verify` for portable memory drives.
