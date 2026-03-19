"""Shared logic for creating vault entities (CLI and agent)."""

from datetime import date
from pathlib import Path
from typing import Literal

from .load import Notes
from .models import DailyProjectEntry, DailyProjectNote, Meeting, Person, Project, Task

TaskStatus = Literal["backlog", "to do", "doing", "done"]


def project_wikilink(filename: str) -> str:
    """Obsidian wikilink for a project note."""
    return f"[[projects/{filename}|{filename}]]"


def person_wikilink(filename: str) -> str:
    """Obsidian wikilink for a person note."""
    return f"[[people/{filename}|{filename}]]"


def meeting_wikilink(filename: str) -> str:
    """Obsidian wikilink for a meeting note."""
    return f"[[meetings/{filename}|{filename}]]"


def _append_project_to_daily_and_template(
    path: Path, notes: Notes, project: Project
) -> None:
    if "daily" in notes:
        notes["daily"].projects.append(  # type: ignore
            DailyProjectNote(
                project_fk=project_wikilink(project.filename),
                entries=[],
            )
        )
        notes["daily"].save(path)  # type: ignore

    template_content = (
        f"\n\n## {project_wikilink(project.filename)}\n\n- [ ] Placeholder\n\n---"
    )
    (path / "templates" / "Daily.md").parent.mkdir(parents=True, exist_ok=True)
    with open(path / "templates" / "Daily.md", "a", encoding="utf-8") as f:
        f.write(template_content)


def _attach_meeting_to_daily(path: Path, notes: Notes, meeting: Meeting) -> None:
    if "daily" not in notes:
        return
    for daily_project_note in notes["daily"].projects:  # type: ignore
        if daily_project_note.project_fk == meeting.project_fk:
            daily_project_note.entries.append(
                DailyProjectEntry(
                    completed=False,
                    content=meeting_wikilink(meeting.filename),
                    fk=True,
                )
            )
            break
    notes["daily"].save(path)  # type: ignore


def create_project(
    path: Path,
    notes: Notes,
    filename: str,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> Project:
    """Save project, link to daily note, append Daily.md template section."""
    project = Project(
        filename=filename,
        content="",
        start_date=start_date if start_date is not None else date.today(),
        end_date=end_date,
    )
    project.save(path)
    _append_project_to_daily_and_template(path, notes, project)
    return project


def create_person(
    path: Path,
    filename: str,
    project_list: list[str],
) -> Person:
    """Save person. ``project_list`` entries are full project wikilinks."""
    person = Person(
        filename=filename,
        content="",
        project_list=project_list,
    )
    person.save(path)
    return person


def create_meeting(
    path: Path,
    notes: Notes,
    filename: str,
    *,
    project_fk: str,
    people_list: list[str],
    meeting_date: date,
) -> Meeting:
    """Save meeting and add to today's daily under the matching project."""
    meeting = Meeting(
        filename=filename,
        content="",
        project_fk=project_fk,
        people_list=people_list,
        meeting_date=meeting_date,
    )
    meeting.save(path)
    _attach_meeting_to_daily(path, notes, meeting)
    return meeting


def parse_task_due_date(due_date_str: str) -> date:
    """Parse CLI due date: YYYY-MM-DD, MMDD, or DD (this month)."""
    s = due_date_str.strip()
    if len(s) == 10:
        return date.fromisoformat(s)
    if len(s) == 5:
        return date.today().replace(month=int(s[:2]), day=int(s[2:]))
    if len(s) == 2:
        return date.today().replace(day=int(s[:2]))
    return date.today()


def create_task(
    path: Path,
    filename: str,
    *,
    project_fk: str,
    due_date: date,
    status_enum: TaskStatus,
) -> Task:
    """Save task."""
    task = Task(
        filename=filename,
        content="",
        project_fk=project_fk,
        due_date=due_date,
        status_enum=status_enum,
    )
    task.save(path)
    return task
