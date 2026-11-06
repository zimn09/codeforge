"""Small, dependency-free Git helpers used by the Git plugin."""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

AHEAD_RE = re.compile(r"ahead (\d+)")
BEHIND_RE = re.compile(r"behind (\d+)")
UPSTREAM_RE = re.compile(r"\s+\[(.+?)\]\s*$")


@dataclass(frozen=True)
class GitEntry:
    """One changed path from ``git status --porcelain``."""

    index_status: str
    worktree_status: str
    path: str

    @property
    def is_staged(self) -> bool:
        return self.index_status not in {" ", "?", "!"}

    @property
    def is_untracked(self) -> bool:
        return self.index_status == "?" and self.worktree_status == "?"

    @property
    def line(self) -> str:
        return f"{self.index_status}{self.worktree_status} {self.path}"


@dataclass
class GitStatus:
    """Repository state for the current workspace."""

    root: Path
    branch: str = ""
    ahead: int = 0
    behind: int = 0
    entries: list[GitEntry] = field(default_factory=list)
    error: str = ""

    @property
    def dirty(self) -> bool:
        return bool(self.entries)

    @property
    def staged(self) -> bool:
        return any(entry.is_staged for entry in self.entries)

    @property
    def changed_count(self) -> int:
        return len(self.entries)


def git_executable() -> str | None:
    """Return the Git executable, if one is installed."""

    return shutil.which("git")


def find_repository(path: Path | None) -> Path | None:
    """Walk upwards from *path* until a ``.git`` entry is found."""

    if path is None:
        return None
    try:
        start = Path(path).expanduser()
        if not start.is_dir():
            start = start.parent
        start = start.resolve()
    except OSError:
        return None

    for candidate in (start, *start.parents):
        marker = candidate / ".git"
        if marker.exists():
            return candidate
    return None


def run_git(
    root: Path,
    *args: str,
    timeout: float = 8.0,
) -> subprocess.CompletedProcess[str] | None:
    """Run a Git command in *root* and capture its output."""

    executable = git_executable()
    if executable is None:
        return None
    try:
        return subprocess.run(
            [executable, *args],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def _parse_branch_header(text: str) -> tuple[str, int, int]:
    header = text.strip()
    if header.startswith("No commits yet on "):
        return header.removeprefix("No commits yet on ").strip(), 0, 0
    if header.startswith("Initial commit on "):
        return header.removeprefix("Initial commit on ").strip(), 0, 0
    if header.startswith("HEAD (no branch)"):
        return "detached", 0, 0

    ahead = 0
    behind = 0
    upstream = UPSTREAM_RE.search(header)
    if upstream:
        details = upstream.group(1)
        ahead_match = AHEAD_RE.search(details)
        behind_match = BEHIND_RE.search(details)
        ahead = int(ahead_match.group(1)) if ahead_match else 0
        behind = int(behind_match.group(1)) if behind_match else 0
        header = header[: upstream.start()]

    branch = header.split("...", 1)[0].strip()
    if not branch:
        branch = "detached"
    return branch, ahead, behind


def _parse_entry(line: str) -> GitEntry | None:
    if len(line) < 4:
        return None
    return GitEntry(
        index_status=line[0],
        worktree_status=line[1],
        path=line[3:].strip(),
    )


def read_status(path: Path | None) -> GitStatus | None:
    """Return the repository status for *path*, or ``None`` outside Git."""

    root = find_repository(path)
    if root is None:
        return None

    result = run_git(root, "status", "--porcelain=v1", "--branch")
    if result is None:
        return GitStatus(root=root, error="Git is not installed.")

    output = result.stdout or ""
    if result.returncode != 0:
        error = (result.stderr or result.stdout or "").strip()
        return GitStatus(root=root, error=error or "Unable to read Git status.")

    branch = "detached"
    ahead = 0
    behind = 0
    entries: list[GitEntry] = []
    for line in output.splitlines():
        if line.startswith("## "):
            branch, ahead, behind = _parse_branch_header(line[3:])
            continue
        entry = _parse_entry(line)
        if entry is not None:
            entries.append(entry)
    return GitStatus(
        root=root,
        branch=branch,
        ahead=ahead,
        behind=behind,
        entries=entries,
    )


def status_label(status: GitStatus) -> str:
    """Compact status-bar text for *status*."""

    if status.error:
        return f"git {status.branch or 'error'}"
    branch = status.branch or "detached"
    dirty = "*" if status.dirty else ""
    ahead = f" ↑{status.ahead}" if status.ahead else ""
    behind = f" ↓{status.behind}" if status.behind else ""
    return f"git  {branch}{dirty}{ahead}{behind}"


def status_tooltip(status: GitStatus) -> str:
    """Multi-line tooltip with repository and workspace details."""

    lines = [f"Repository: {status.root}", f"Branch: {status.branch}"]
    if status.ahead or status.behind:
        lines.append(f"Upstream: {status.ahead} ahead, {status.behind} behind")
    if status.error:
        lines.append(status.error)
    elif status.dirty:
        lines.append(f"Changes: {status.changed_count}")
        lines.extend(f"  {entry.line}" for entry in status.entries[:12])
        if len(status.entries) > 12:
            lines.append(f"  … {len(status.entries) - 12} more")
    else:
        lines.append("Working tree clean")
    return "\n".join(lines)
