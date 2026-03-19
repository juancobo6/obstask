"""Load notes from the workspace."""

from datetime import date
from pathlib import Path
from typing import Any

import yaml

from .models import (
    Daily,
    DailyProjectEntry,
    DailyProjectNote,
    Meeting,
    Note,
    Person,
    Project,
    Task,
)

type Notes = dict[str, list[Note] | Daily]


# FIXME: Add a check when overwriting a file.


def _split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter (--- ... ---) from markdown; body is the rest."""
    if text.startswith("\ufeff"):
        text = text[1:]
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            yaml_block = "\n".join(lines[1:i])
            body = "\n".join(lines[i + 1 :])
            raw = yaml.safe_load(yaml_block)
            metadata: dict[str, Any] = raw if isinstance(raw, dict) else {}
            return metadata, body
    return {}, text


def read_note(path: Path) -> dict[str, Any]:
    """Read a note from a file."""
    filename = path.stem
    with open(path, encoding="utf-8") as f:
        text = f.read()
    metadata, content = _split_frontmatter(text)

    return {
        "filename": filename,
        "content": content,
        **metadata,
    }


def create_daily(path: Path) -> Daily:
    """Create a daily note."""
    path.write_text(Path("templates/Daily.md").read_text(), encoding="utf-8")
    return Daily(filename=str(date.today()), projects=[])  # type: ignore


def read_daily(path: Path) -> Daily:
    """Read a daily note."""
    with open(path, encoding="utf-8") as f:
        _, content = _split_frontmatter(f.read())

    daily = Daily(filename=path.stem, projects=[])

    for section in content.split("---"):
        if "## [[projects/" not in section:
            continue

        project_filename_fk = section.split("## ")[1].split("\n")[0]
        entries = []
        for entry in section.split("- ")[1:]:
            completed = entry.startswith("[x]")
            content = entry.split("] ")[1].strip()
            fk = content.startswith("[[") and content.endswith("]]")
            entries.append(
                DailyProjectEntry(completed=completed, content=content, fk=fk)
            )
        daily.projects.append(
            DailyProjectNote(project_fk=project_filename_fk, entries=entries)
        )

    return daily


def load_notes(path: Path) -> Notes:
    """Load notes from the workspace."""
    notes: Notes = {}

    projects_path = path / "projects"
    tasks_path = path / "tasks"
    people_path = path / "people"
    meetings_path = path / "meetings"

    if "projects" not in notes:
        notes["projects"] = []
    for project_path in projects_path.glob("*.md"):
        notes["projects"].append(Project(**read_note(project_path)))  # type: ignore

    if "tasks" not in notes:
        notes["tasks"] = []
    for task_path in tasks_path.glob("*.md"):
        notes["tasks"].append(Task(**read_note(task_path)))  # type: ignore

    if "people" not in notes:
        notes["people"] = []
    for person_path in people_path.glob("*.md"):
        notes["people"].append(Person(**read_note(person_path)))  # type: ignore

    if "meetings" not in notes:
        notes["meetings"] = []
    for meeting_path in meetings_path.glob("*.md"):
        notes["meetings"].append(Meeting(**read_note(meeting_path)))  # type: ignore

    daily_path = path / "daily" / f"{str(date.today())}.md"
    if not daily_path.exists():
        notes["daily"] = create_daily(daily_path)
    notes["daily"] = read_daily(daily_path)

    return notes
