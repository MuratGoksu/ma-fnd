# Changelog

All notable changes to the MA-FND project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Updated dependencies to latest versions (2026-01-20)
  - anyio: 4.12.0 → 4.12.1
  - certifi: 2025.11.12 → 2026.1.4 (security update)
  - openai: 2.14.0 → 2.15.0
  - soupsieve: 2.8.1 → 2.8.3
  - urllib3: 2.6.2 → 2.6.3
  - websockets: 15.0.1 → 16.0
- Updated build tools
  - setuptools: → 80.9.0
  - wheel: → 0.45.1

### Fixed
- Resolved FastAPI/Starlette dependency compatibility

### Security
- Updated certifi to 2026.1.4 for latest SSL certificates
- Updated urllib3 to 2.6.3 with security patches

## [Previous] - 2026-01-18

### Fixed
- Fixed indentation error in api.py

### Changed
- Code cleanup: removed excessive debug logging
- Removed 4 documentation files (STATUS.md, TEST_FACTCHECK.md, TWITTER_SETUP.md, WEB_INTERFACE.md)
- Cleaned up debug statements in api.py and fake_news_categorizer.py
