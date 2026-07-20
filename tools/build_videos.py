"""Build synchronized side-by-side MP4 demonstrations from raw GIF pairs."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path


SCENARIOS = (
    ("roundabout", "1-*"),
    ("intersection", "2-*"),
    ("multi-scenario", "3-*"),
)
FILENAME_PATTERN = re.compile(
    r"^(?P<prefix>ep(?P<episode>\d{3})_env\d+_seed\d+)_"
    r"(?P<view>topdown|human)(?P<suffix>(?:_.*)?)\.gif$"
)


def find_ffmpeg(repo_root: Path) -> Path:
    bundled_dir = repo_root / "tmp" / "codex_ffmpeg_runtime" / "imageio_ffmpeg" / "binaries"
    bundled = sorted(bundled_dir.glob("ffmpeg*.exe"))
    if bundled:
        return bundled[0]

    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return Path(system_ffmpeg)

    raise FileNotFoundError(
        "FFmpeg was not found. Install FFmpeg or place an executable on PATH."
    )


def find_source_directory(repo_root: Path, pattern: str) -> Path:
    matches = sorted(path for path in repo_root.glob(pattern) if path.is_dir())
    if len(matches) != 1:
        raise FileNotFoundError(
            f"Expected one source directory matching {pattern!r}, found {len(matches)}."
        )
    return matches[0]


def discover_pairs(source_directory: Path) -> list[tuple[int, str, str, Path, Path]]:
    pairs: dict[tuple[str, str], dict[str, Path]] = {}
    episodes: dict[tuple[str, str], int] = {}

    for gif_path in source_directory.rglob("*.gif"):
        match = FILENAME_PATTERN.match(gif_path.name)
        if not match:
            continue

        episode = int(match.group("episode"))

        prefix = match.group("prefix")
        suffix = match.group("suffix")
        key = (prefix, suffix)
        view = match.group("view")

        if view in pairs.setdefault(key, {}):
            raise RuntimeError(f"Duplicate {view} GIF for {prefix}{suffix}")
        pairs[key][view] = gif_path
        episodes[key] = episode

    discovered: list[tuple[int, str, str, Path, Path]] = []
    for (prefix, suffix), views in pairs.items():
        if set(views) != {"topdown", "human"}:
            raise FileNotFoundError(f"Incomplete GIF pair for {prefix}{suffix}")
        discovered.append(
            (episodes[(prefix, suffix)], prefix, suffix, views["topdown"], views["human"])
        )

    discovered.sort(key=lambda item: item[0])
    if not discovered:
        raise RuntimeError(f"No complete GIF pairs found in {source_directory}.")
    return discovered


def build_video(
    ffmpeg: Path,
    topdown: Path,
    three_d: Path,
    output: Path,
    force: bool,
) -> bool:
    if output.exists() and output.stat().st_size > 0 and not force:
        return False

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = output.with_suffix(".tmp.mp4")
    if temporary_output.exists():
        temporary_output.unlink()

    filter_graph = (
        "[0:v]setpts=PTS-STARTPTS,fps=30,scale=-2:600:flags=lanczos,"
        "setsar=1[top];"
        "[1:v]setpts=PTS-STARTPTS,fps=30,scale=-2:600:flags=lanczos,"
        "setsar=1[three];"
        "[top][three]hstack=inputs=2:shortest=1,format=yuv420p[out]"
    )

    command = [
        str(ffmpeg),
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(topdown),
        "-i",
        str(three_d),
        "-filter_complex",
        filter_graph,
        "-map",
        "[out]",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "23",
        "-profile:v",
        "high",
        "-level",
        "4.0",
        "-movflags",
        "+faststart",
        str(temporary_output),
    ]

    try:
        subprocess.run(command, check=True)
        temporary_output.replace(output)
    except Exception:
        if temporary_output.exists():
            temporary_output.unlink()
        raise

    return True


def sync_display_videos(
    jobs: list[tuple[str, int, str, Path, Path, Path]],
    display_root: Path,
) -> None:
    safe_by_scenario: dict[str, list[tuple[int, Path]]] = defaultdict(list)
    for scenario, episode, suffix, _topdown, _three_d, output in jobs:
        if not suffix:
            safe_by_scenario[scenario].append((episode, output))

    expected: set[Path] = set()
    for scenario, _source_pattern in SCENARIOS:
        target_directory = display_root / scenario
        target_directory.mkdir(parents=True, exist_ok=True)
        selected = sorted(safe_by_scenario[scenario])[:9]
        for _episode, source in selected:
            target = target_directory / source.name
            expected.add(target.resolve())
            if not target.exists() or target.stat().st_size != source.stat().st_size:
                shutil.copy2(source, target)
        print(
            f"Display set: {scenario} has {len(selected)} video(s) and "
            f"{9 - len(selected)} reserved slot(s).",
            flush=True,
        )

    for existing in display_root.rglob("*.mp4"):
        if existing.resolve() not in expected:
            existing.unlink()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rebuild videos that already exist.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    video_root = repo_root / "all-mp4"
    display_root = repo_root / "docs" / "assets" / "display-mp4"
    ffmpeg = find_ffmpeg(repo_root)

    jobs: list[tuple[str, int, str, Path, Path, Path]] = []
    for scenario, source_pattern in SCENARIOS:
        source_directory = find_source_directory(repo_root, source_pattern)
        for episode, prefix, suffix, topdown, three_d in discover_pairs(source_directory):
            output = video_root / scenario / f"{prefix}{suffix}.mp4"
            jobs.append((scenario, episode, suffix, topdown, three_d, output))

    print(f"FFmpeg: {ffmpeg}", flush=True)
    for index, (scenario, episode, suffix, topdown, three_d, output) in enumerate(jobs, 1):
        changed = build_video(ffmpeg, topdown, three_d, output, args.force)
        status = "built" if changed else "kept"
        result = suffix.removeprefix("_") or "no recorded violation"
        size_mb = output.stat().st_size / (1024 * 1024)
        print(
            f"[{index:02d}/{len(jobs)}] {scenario} episode {episode:02d}: "
            f"{status} ({size_mb:.1f} MB, {result})",
            flush=True,
        )

    sync_display_videos(jobs, display_root)


if __name__ == "__main__":
    main()
