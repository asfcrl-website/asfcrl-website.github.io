# ASFCRL Experimental Demonstrations

This repository hosts the static project page for ASFCRL evaluation demonstrations.

The website currently presents 24 synchronized MP4 demonstrations without recorded
safety violations. Each scenario keeps a complete nine-slot grid for future additions:

- Roundabout: 9 demonstrations
- Intersection: 8 demonstrations and 1 reserved slot
- Multi-Scenario: 7 demonstrations and 2 reserved slots
- Each episode combines a top-down view and a 3D view into one synchronized video

All 40 generated MP4 assets preserve the episode, environment, seed, and result suffix
from their source GIF filenames. The complete local collection is stored in `all-mp4/`.
The 24 files used by the website are copied to `docs/assets/display-mp4/`. Files with
result suffixes such as `crash_vehicle` or `out_of_lane` are never copied into the
display collection. Seed values remain in filenames but are not shown in page labels.

The real-world evaluation section is prepared for a future update.

## GitHub Pages

The website is published from the `docs/` directory. In **Settings > Pages**, use:

- Source: `Deploy from a branch`
- Branch: `main`
- Folder: `/docs`

## Local Preview

Open `docs/index.html` directly, or serve the `docs/` directory with any static file server.

## Rebuilding the Videos

Run `tools/build_videos.py` with the raw scenario directories at the repository root.
The script creates browser-compatible H.264 videos in `all-mp4/`, then synchronizes up
to nine safety-compliant files per scenario into `docs/assets/display-mp4/`.
