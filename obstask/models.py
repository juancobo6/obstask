"""Data models for the Obstask project."""

from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

type Filename = str


class Note(BaseModel):
    """Represents a note in the workspace."""

    filename: Filename
    content: str

    def save(
        self, path: Path, note_type: Literal["projects", "tasks", "people", "meetings"]
    ) -> None:
        """Save the note to the workspace."""
        note_path = path / note_type / f"{self.filename}.md"
        meta = {
            k: v
            for k, v in self.model_dump().items()
            if k not in ("filename", "content") and v is not None
        }
        body = self.content.strip()

        if meta:
            fm = yaml.safe_dump(
                meta, default_flow_style=False, allow_unicode=True, sort_keys=False
            ).rstrip()
            text = f"---\n{fm}\n---\n{body}"
        else:
            text = f"---\n---\n{body}"

        note_path.write_text(text, encoding="utf-8")


class Project(Note):
    """Represents a project in the workspace."""

    start_date: date | None = Field(default=date.today())
    end_date: date | None = Field(default=None)

    def save(self, path: Path) -> None:
        """Save the project to the workspace."""
        super().save(path, "projects")


class Task(Note):
    """Represents a task in a project."""

    due_date: date | None = Field(default=None)
    status_enum: Literal["backlog", "to do", "doing", "done"] | None = Field(
        default="backlog"
    )
    project_fk: Filename | None = Field(default=None)

    def save(self, path: Path) -> None:
        """Save the task to the workspace."""
        super().save(path, "tasks")


class Person(Note):
    """Represents a person in the workspace."""

    project_list: list[Filename] | None = Field(default=None)

    def save(self, path: Path) -> None:
        """Save the person to the workspace."""
        super().save(path, "people")


class Meeting(Note):
    """Represents a meeting in the workspace."""

    meeting_date: date | None = Field(default=date.today())
    project_fk: Filename | None = Field(default=None)
    people_list: list[Filename] | None = Field(default=None)

    def save(self, path: Path) -> None:
        """Save the meeting to the workspace."""
        super().save(path, "meetings")


class DailyProjectEntry(BaseModel):
    """Represents a project entry in a daily note."""

    completed: bool = Field(default=False)
    content: str | Filename = Field(default="")
    fk: bool = Field(default=False)


class DailyProjectNote(BaseModel):
    """Represents a project note in a daily note."""

    project_fk: Filename = Field(default="")
    entries: list[DailyProjectEntry] = Field(default=[])


class Daily(BaseModel):
    """Represents a daily note in the workspace."""

    filename: Filename = Field(default=str(date.today()))
    projects: list[DailyProjectNote] = Field(default=[])

    def save(self, path: Path) -> None:
        """Save the daily note to the workspace."""
        daily_path = path / "daily" / f"{self.filename}.md"

        content = ""
        for daily_project in self.projects:
            content += f"\n\n## {daily_project.project_fk}\n\n"
            for entry in daily_project.entries:
                content += f"- [{'x' if entry.completed else ' '}] {entry.content}\n"

            if len(daily_project.entries) == 0:
                content += "- [ ] Placeholder\n"

            content += "\n---"

        daily_path.write_text(content, encoding="utf-8")
