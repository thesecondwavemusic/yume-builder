# Yume Builder 🍏

Ephemeral macOS CI/CD builder for the **Yume Creator Cloud** creative suite.

## Architecture

This repository contains **only** the CI/CD orchestration workflow (`.github/workflows/build-macos.yml`). 
Zero proprietary application source code is committed or stored on GitHub.

```mermaid
flowchart LR
    A["GitHub Actions (macos-14 Apple Silicon)"] -->|1. Shallow clone to RAM| B["Private Forge (code.yumedevs.com)"]
    A -->|2. Native Cargo Build + Ad-hoc Sign| C["universal / aarch64 DMG"]
    C -->|3. Merge Checksums (No BOM)| D["SHA256SUMS.txt"]
    D -->|4. Upload Assets via tea CLI| E["Gitea Release"]
    A -.->|5. Runner destroyed| F["0 code on GitHub"]
```

## Supported Apps

- **Curve** (Vector Illustration)
- **Central** (Suite Launcher)
- **Prism** (Raster Image Editor)
- **Frame** (Vector Design & Prototyping)
- **Reel** (Video Editing & Compositing)
- **Surface** (3D Texture Painting)
- **Forge** (Procedural Material Design)
- **Anima** (2D Vector Animation)
- **Kinetic** (Motion Graphics & VFX)
- **Lux** (RAW Photo Processor)
- **Folio** (PDF & Document Reader)
- **Editorial** (Page Layout & Publishing)
- **Sonic** (Digital Audio Workstation)

## Triggering a Build

1. Go to **Actions** tab.
2. Select **Build macOS Packages**.
3. Click **Run workflow**, choose the app (or `all`), target architecture (`universal` or `aarch64`), and click **Run workflow**.
