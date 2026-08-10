# Changelog

All notable changes to this project will be documented in this file. The
project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Temporary AppIndicator process for showing usage immediately without a
  GNOME Wayland logout.

### Changed

- Refresh interval preferences are now displayed and edited in minutes while
  retaining the existing seconds-based setting for compatibility.

## [0.1.0] - 2026-08-10

### Added

- GNOME Shell panel indicator for the primary Codex usage window.
- Configurable display mode, reset time, icon, and refresh interval.
- Short-lived Codex app-server JSONL client with strict response validation.
- Standalone text and JSON command-line output.
- Offline unit and subprocess integration tests.
- Source packaging, installation targets, CI, and project documentation.

[Unreleased]: https://github.com/noah-be/gnome-codex-usage-indicator/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/noah-be/gnome-codex-usage-indicator/releases/tag/v0.1.0
