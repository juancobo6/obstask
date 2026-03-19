"""Agent for the Obstask project."""

import os
from datetime import date, datetime
from pathlib import Path
from typing import Literal

import questionary
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessage
from rich.console import Console
from rich.markdown import Markdown

from . import create
from .load import Notes, load_notes
from .models import DailyProjectNote, Meeting, Person, Project, Task


class Context(BaseModel):
    """Context for the Obstask agent."""

    path: Path
    project_filename: str


def create_person(
    ctx: RunContext[Context],
    person_filename: str,
    content: str = "",
) -> str:
    """Create or update a person note under ``people/``.

    The person is tied to the **current session project** (vault context); you do
    not pass a project name here.

    To **update**, reuse the same ``person_filename``; the file is overwritten.

    **People filenames:** Meetings reference attendees by note name. Whatever you
    use as ``person_filename`` is what ``create_meeting`` must put in
    ``people_list`` **exactly** (same spelling, casing)—and every name
    in ``people_list`` must match a real ``people/*`` file the same way.

    Args:
        ctx: Run context (vault path + session project on ``ctx.deps``).
        person_filename: Person note filename, e.g. ``Jane Doe``.
        content: Person note content.

    Returns:
        Confirmation message.
    """
    create.create_person(
        path=ctx.deps.path,
        filename=person_filename,
        project_list=[create.project_wikilink(ctx.deps.project_filename)],
    )

    return f"Person {person_filename} created successfully."


def create_meeting(
    ctx: RunContext[Context],
    meeting_filename: str,
    people_list: list[str],
    meeting_date: str = str(date.today()),
    content: str = "",
) -> str:
    """Create or update a meeting note under ``meetings/``.

    The meeting is linked to the **current session project** (vault context).

    To **update**, reuse the same ``meeting_filename`` with new ``people_list`` or
    ``meeting_date``.

    **People only (exact filenames):** Each entry in ``people_list`` must be the
    **exact** basename of a person note under ``people/`` (character-for-character).
    Copy from existing person notes; do not paraphrase or use
    display names that differ from the file.

    Args:
        ctx: Run context (vault path + session project on ``ctx.deps``).
        meeting_filename: Meeting note filename, e.g. ``Sprint planning``.
        people_list: Person note basenames—must match exactly.
        meeting_date: ISO date (YYYY-MM-DD) of the meeting.
        content: Meeting note content.

    Returns:
        Confirmation message.
    """
    notes = load_notes(ctx.deps.path)
    create.create_meeting(
        ctx.deps.path,
        notes,
        meeting_filename,
        project_fk=create.project_wikilink(ctx.deps.project_filename),
        people_list=[create.person_wikilink(person) for person in people_list],
        meeting_date=date.fromisoformat(meeting_date),
    )
    return f"Meeting {meeting_filename} created successfully."


def create_task(
    ctx: RunContext[Context],
    task_filename: str,
    due_date: str = str(date.today()),
    status_enum: Literal["backlog", "to do", "doing", "done"] = "backlog",
    content: str = "",
) -> str:
    """Create or update a task note under ``tasks/``.

    The task is linked to the **current session project** (vault context).

    To **update**, reuse the same ``task_filename`` with new ``due_date`` and/or
    ``status_enum``.

    Args:
        ctx: Run context (vault path + session project on ``ctx.deps``).
        task_filename: Task note filename, e.g. ``Write spec``.
        due_date: ISO due date (YYYY-MM-DD).
        status_enum: One of ``backlog``, ``to do``, ``doing``, ``done``.
        content: Task note content.

    Returns:
        Confirmation message.
    """
    create.create_task(
        ctx.deps.path,
        task_filename,
        project_fk=create.project_wikilink(ctx.deps.project_filename),
        due_date=date.fromisoformat(due_date),
        status_enum=status_enum,
    )
    return f"Task {task_filename} created successfully."


def init_agent() -> Agent[Context, str]:  # noqa: C901
    """Initialize the Obstask agent for the given vault path."""
    if os.getenv("GOOGLE_API_KEY") is None:
        raise ValueError("GOOGLE_API_KEY is not set")

    if os.getenv("GOOGLE_MODEL") is None:
        raise ValueError("GOOGLE_MODEL is not set")

    agent = Agent[Context, str](
        model=os.getenv("GOOGLE_MODEL"),
        instructions=(
            "You are a helpful assistant for the Obstask vault. The active project "
            "is fixed for this session (context). For **people** only: when listing "
            "meeting attendees or naming person notes, use the **exact** filename "
            "as under people/ (including)—copy verbatim; approximate names "
            "break wikilinks."
            "You are a conversational agent. If you are missing information, "
            "ask the user for it."
        ),
        output_type=str,
        deps_type=Context,
        tools=[create_person, create_meeting, create_task],
    )

    @agent.system_prompt
    def _notes(ctx: RunContext[Context]) -> str:  # noqa: C901
        notes = load_notes(ctx.deps.path)

        for project in notes["projects"]:
            if (
                isinstance(project, Project)
                and project.filename == ctx.deps.project_filename
            ):
                project_wikilink = create.project_wikilink(project.filename)
                break

        project_people = []
        for person in notes["people"]:
            if (
                isinstance(person, Person)
                and person.project_list is not None
                and project_wikilink in person.project_list
            ):
                project_people.append(person)

        project_meetings = []
        for meeting in notes["meetings"]:
            if isinstance(meeting, Meeting) and meeting.project_fk == project_wikilink:
                project_meetings.append(meeting)

        project_tasks = []
        for task in notes["tasks"]:
            if isinstance(task, Task) and task.project_fk == project_wikilink:
                project_tasks.append(task)

        parts = []
        parts.append("***Current state of the project***\n")
        parts.append(f"# Project: {project.filename}")  # type: ignore
        parts.append(f"{project.content or 'No more information'}\n")  # type: ignore

        parts.append("\n## People")
        if len(project_people) == 0:
            parts.append("No people defined for this project.")
        else:
            for person in project_people:
                parts.append(
                    f"- {person.filename}: {person.content or 'No more information'}"
                )

        parts.append("\n## Meetings")
        if len(project_meetings) == 0:
            parts.append("No meetings defined for this project.")
        else:
            for meeting in project_meetings:
                parts.append(
                    f"- {meeting.filename}: {meeting.content or 'No more information'}"
                )

        parts.append("\n## Tasks")
        if len(project_tasks) == 0:
            parts.append("No tasks defined for this project.")
        else:
            for task in project_tasks:
                parts.append(
                    f"- {task.filename} (due: {task.due_date}) "
                    f"(status: {task.status_enum}): "
                    f"{task.content or 'No more information'}"
                )

        return "\n".join(parts)

    @agent.system_prompt
    def _timestamp() -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"The current date and time is {now}."

    return agent


def agent_cli(
    agent: Agent[Context, str],
    path: Path,
    project_filename: str,
    hot_start: str | None = None,
) -> None:
    """Run the agent in a CLI loop."""
    deps = Context(path=path, project_filename=project_filename)
    questionary.print(
        f"Obstask agent — project: {project_filename!r}. "
        "Type your message; quit, exit, or empty line to leave.\n"
    )
    history: list[ModelMessage] | None = None

    console = Console()

    while True:
        try:
            if hot_start is None:
                user = questionary.text("", qmark=">").ask()

            else:
                user = hot_start

        except KeyboardInterrupt:
            questionary.print("\nBye.")
            return

        if user is None:
            questionary.print("Goodbye.")
            return

        text = user.strip()
        if not text or text.lower() in ("quit", "exit", "q"):
            questionary.print("Goodbye.")
            return

        try:
            result = agent.run_sync(
                text,
                deps=deps,
                message_history=history,
            )
        except Exception as exc:  # noqa: BLE001 — surface model/API errors in the CLI
            questionary.print(f"Error: {exc}\n")
            continue

        console.print()
        console.print(Markdown(result.output))

        if hot_start is not None:
            console.print(
                "Let me now if you need anything else for this projec, input quit, exit"
                ", or q to leave to move on to the next project."
            )
            hot_start = None

        console.print()

        history = result.all_messages()


def filter_entries_prompt(project: DailyProjectNote, notes: Notes) -> str:
    """Filter the entries of a project.

    Only includes the ones that are not completed and that are not linked to a meeting.

    Args:
        project: The project to filter.
        notes: The notes to use to filter the entries.

    Returns:
        A list of filtered entries.
    """
    filtered_entries = []
    for entry in project.entries:
        if not entry.completed:
            if entry.fk:
                for meeting in notes["meetings"]:
                    if create.meeting_wikilink(meeting.filename) == entry.content:
                        filtered_entries.append(meeting)
                        break

            else:
                filtered_entries.append(entry)

    prompt = []
    prompt.append(
        f"Here are some notes I have taken for the project {project.project_fk}. "
        "I need you to process these entries and create whichever tasks or meetings "
        "are relevant to the project."
    )
    for entry in filtered_entries:
        prompt.append(f"- {entry.content}")

    return "\n".join(prompt)


def parse_project(path: Path, project: DailyProjectNote, notes: Notes) -> None:
    """Parse a project from a daily note."""
    prompt = filter_entries_prompt(project, notes)

    project_filename = project.project_fk
    project_filename = project_filename.split("|")[1].split("]]")[0]

    agent = init_agent()
    agent_cli(agent, path, project_filename, prompt)

    breakpoint()


def agent_parse(
    agent: Agent[Context, str],
    path: Path,
) -> None:
    """Parse the daily note."""
    notes = load_notes(path)
    daily = notes["daily"]

    for project in daily.projects:  # type: ignore
        prompt = filter_entries_prompt(project, notes)
        project_filename = project.project_fk
        project_filename = project_filename.split("|")[1].split("]]")[0]
        agent_cli(agent, path, project_filename, prompt)

        for entry in project.entries:
            entry.completed = True

        daily.save(path)
