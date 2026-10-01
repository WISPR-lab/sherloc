# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Structure:
Added for new features.
Changed for changes in existing functionality.
Deprecated for soon-to-be removed features.
Removed for now removed features.
Fixed for any bug fixes.
Security in case of vulnerabilities.

## [Unreleased]

### Changed
- Sherloc listens on 127.0.0.1 by default. Set `SHERLOC_HOST` and `SHERLOC_ALLOWED_HOSTS` to serve it elsewhere
- `pytest` runs from the repository root
- CI runs the test suite on pushes and pull requests. A lint ratchet (`tests/test_lint_ratchet.py`) fails on any new undefined name, invalid escape, mutable default argument, bare `except`, `shell=True` or `eval`; existing findings are recorded in `tests/lint_baseline.json`
- The stalkerware-indicators workflow uses the `sherloc/` paths and a single `token:` key (the duplicate key meant `IOC_UPDATE_KEY` was ignored), and its script exits non-zero when its requirements are missing
### Security
- Device serials and app ids are validated before they reach a shell command. Previously a crafted serial or app id, or a serial reported by a device, could run commands
- Fixed quoting in the Android and iOS uninstall commands that made `shlex.quote` ineffective
- Screenshot paths are limited to the screenshots directory
- Requests with a foreign `Host` header, a cross-origin `Origin` on state-changing methods, or a non-same-origin `Sec-Fetch-Site` are rejected, so another website cannot trigger scans, uninstalls, or data deletion
- `sherloc/static_data/pii.key` and `flask.secret` are no longer tracked by git and are ignored. Both files were public, so anyone could compute the `HSN_` device identifiers and forge session cookies. Keys are generated on first run with owner-only (0600) permissions, and a key file that still holds one of the previously published values is replaced. Existing installs get new keys after pulling, so stored `HSN_` identifiers will change. The old values remain in git history
- The PDF printout escapes notes, names and app text, and wkhtmltopdf no longer has local file access. Previously a note containing an `<iframe src="file://...">` tag put the contents of a local file into the report

## [v1.1.4] - November 4, 2025

### Added     
- "Open all dropdowns" buttons on TAQ and account check page
### Changed
- Only show relevant screenshot buttons on account check page
- Changed readme to account for Mac installation
- Account nickname changed to required username
- Changed names of consultation action buttons on homepage
### Deprecated
### Removed
### Fixed
- Patched issue with missing data and screenshot folders by adding during setup if needed
### Security

## [v1.1.3] - August 22, 2025

### Added     
### Changed
- Updated how screenshots show up on the printout for accounts and root
- Delete reports, too, when deleting client data
### Deprecated
### Removed
### Fixed
- Patched issue where some iPhones trigger duplicate column error during scan
- Patched issue where screenshots for apps are not separated by device
- Fix typo in the explanation of a successful root check
- Patched issue where Android scans try to access a folder that doesn't exist
### Security

## [v1.1.2] - August 14, 2025

### Added     
- Added LiveScreen (wifi.manager) to list of known spyware
### Changed
- Changed question about 2-factor (Issue 63)
- Changed wording of custody question (Issue 64)
- Moved client name input to homepage (Issue 66)
- Trimmed screenshot metadata in printout (Issue 65)
- Removed permissions from printout (Issue 69)
- Changed how root check is described by specifying what was checked.
### Deprecated
### Removed
### Fixed
### Security

## [v1.1.1] - August 8, 2025

### Added     
- Added instructions for installing `wkhtmltopdf` in `README`
- Added `exiftool` to `Brewfile` and `README` instructions
- Added back images that were deleted but we need for the UI

### Changed
- Updated .gitignore
- Updated printout to not show jailbreak part for iOS

### Deprecated
### Removed
### Fixed
- Fixed issue with EvidenceDataEncoder trying to encode Path objects
- Fixed issue with overwriting screenshots
### Security


## [v1.1.0] - August 5, 2025

### Added     

### Changed
- Major restructuring: Moved all Sherloc code into the `sherloc` folder.
- `isdi` file now renamed `main.py`.
- Created `./sherloc.sh` run script, which creates and activates a virtual environment, installs requirements if needed, and runs Sherloc in sudo (via `main.py`).
- Updated `README`.
- Resumed using this changelog.

### Deprecated
### Removed
- Unused files and folders, mostly .pngs in `webstatic/images`.
- Removed `libimobiledevice` from `Brewfile`. 

### Fixed
### Security
