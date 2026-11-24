# Contributing to the AV1 Adoption Kit for Vertical Drama Apps

Thank you for your interest in contributing to the **AV1 Adoption Kit for Vertical Drama Apps**! We welcome contributions ranging from new transcoding presets and device qualification data to bug fixes and player integrations.

---

## Code of Conduct

This project adheres to the [Contributor Covenant](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

---

## Development Workflow

### Prerequisites
- **Python**: 3.11+
- **Node.js**: 18+
- **FFmpeg**: 6.0+ compiled with `libsvtav1`, `libx264`, `libx265`, and optionally `libvmaf`
- **Android SDK**: Build tools 34+ and API 34+ (for Android library development)
- **Xcode**: 15+ with Command Line Tools (for iOS SPM and XCFramework builds)

### Validation & Testing
Before submitting any pull request, ensure all test suites pass:

```bash
# Run unit and integration tests (Python harness + React Native bridge)
make check

# Rebuild all SDK packages (iOS XCFramework, Android AAR, Expo tarball)
make sdk

# Run full multi-codec benchmark & BD-rate calculation (optional)
make bench
```

---

## Contributing Device Qualification Data

One of the most valuable community contributions is real-world device performance data. If you test the kit on physical Android or iOS hardware:
1. Open a new issue using the **Device Qualification Report** template.
2. Include the SoC model, Android/iOS version, decoder name (e.g. `c2.android.av1-dav1d.decoder`), average TTFF, and dropped frame rate over a 10-minute session.

---

## Pull Request Guidelines

1. Fork the repository and create your branch from `main`.
2. Adhere to existing coding standards:
   - Python: PEP 8 guidelines
   - Android: Kotlin/Java style guide
   - iOS: Swift API design guidelines
   - React Native: TypeScript strict mode
3. If introducing architectural changes to transcoding ladders or fallback logic, propose or update an **Architecture Decision Record (ADR)** under `docs/adr/`.
4. Ensure your PR description references the relevant issue and explains the motivation and testing methodology.
