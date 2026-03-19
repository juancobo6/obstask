"""Command line interface for the Obstask project."""

import argparse
from datetime import date
from importlib.resources import files
from pathlib import Path

import questionary

from . import create
from .agent import agent_cli, agent_parse, init_agent
from .load import Notes, load_notes


def create_project(path: Path, notes: Notes) -> None:
    """Create a new project."""
    create.create_project(
        path,
        notes,
        questionary.text("Enter the name of the project:").ask(),
        start_date=date.today(),
        end_date=None,
    )


def create_person(path: Path, notes: Notes) -> None:
    """Create a new person."""
    projects = notes["projects"]  # type: ignore

    create.create_person(
        path,
        questionary.text("Enter the name of the person:").ask(),
        project_list=questionary.checkbox(
            "Select the projects the person is involved in:",
            choices=[
                create.project_wikilink(project.filename)  # type: ignore
                for project in projects
                if project.end_date is None  # type: ignore
            ],
        ).ask(),
    )


def create_meeting(path: Path, notes: Notes) -> None:
    """Create a new meeting."""
    projects = notes["projects"]  # type: ignore
    people = notes["people"]  # type: ignore

    create.create_meeting(
        path,
        notes,
        questionary.text("Enter the name of the meeting:").ask(),
        project_fk=questionary.select(
            "Select the project the meeting is about:",
            choices=[create.project_wikilink(project.filename) for project in projects],  # type: ignore
        ).ask(),
        people_list=questionary.checkbox(
            "Select the people the meeting is with:",
            choices=[create.person_wikilink(person.filename) for person in people],  # type: ignore
        ).ask(),
        meeting_date=date.today(),
    )


def create_task(path: Path, notes: Notes) -> None:
    """Create a new task."""
    projects = notes["projects"]  # type: ignore

    filename = questionary.text("Enter the name of the task:").ask()
    project_fk = questionary.select(
        "Select the project the task is in:",
        choices=[create.project_wikilink(project.filename) for project in projects],  # type: ignore
    ).ask()
    due_date_str = questionary.text(
        "Enter the due date of the task (YYYY-MM-DD):"
    ).ask()
    status_enum = questionary.select(
        "Select the status of the task:",
        choices=["backlog", "to do", "doing", "done"],
    ).ask()

    create.create_task(
        path,
        filename,
        project_fk=project_fk,
        due_date=create.parse_task_due_date(due_date_str),
        status_enum=status_enum,
    )


def create_directory_structure(path: Path, _: Notes) -> None:
    """Create a new directory with the file structure of the project."""
    (path).mkdir(parents=True, exist_ok=True)
    (path / "projects").mkdir(parents=True, exist_ok=True)
    (path / "tasks").mkdir(parents=True, exist_ok=True)
    (path / "people").mkdir(parents=True, exist_ok=True)
    (path / "meetings").mkdir(parents=True, exist_ok=True)
    (path / "daily").mkdir(parents=True, exist_ok=True)

    dest = path / "templates"
    dest.mkdir(parents=True, exist_ok=True)
    pkg_templates = files("obstask") / "templates"
    for entry in pkg_templates.iterdir():
        if entry.is_file():
            (dest / entry.name).write_text(
                entry.read_text(encoding="utf-8"),
                encoding="utf-8",
            )


def chat(path: Path, notes: Notes) -> None:
    """Chat with the agent."""
    project_filename = questionary.select(
        "Select the project to run the agent on:",
        choices=[project.filename for project in notes["projects"]],  # type: ignore
    ).ask()

    agent = init_agent()
    agent_cli(agent, path, project_filename)


def parse(path: Path, _: Notes) -> None:
    """Parse the daily note."""
    agent = init_agent()
    agent_parse(agent, path)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="obstask",
        description="Create Obsidian vault notes (projects, people, meetings, tasks).",
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")
    sub.add_parser("init", help="Create a new directory structure")
    sub.add_parser("project", help="Create a new project")
    sub.add_parser("person", help="Create a new person")
    sub.add_parser("meeting", help="Create a new meeting")
    sub.add_parser("task", help="Create a new task")
    sub.add_parser("chat", help="Run the agent")
    sub.add_parser("parse", help="Parse the daily note")

    return parser


def cli(argv: list[str] | None = None) -> None:
    """Command line interface for the Obstask project."""
    path = Path.cwd()

    args = _build_parser().parse_args(argv)

    notes = load_notes(path)
    handlers = {
        "init": create_directory_structure,
        "project": create_project,
        "person": create_person,
        "meeting": create_meeting,
        "task": create_task,
        "chat": chat,
        "parse": parse,
    }
    handlers[args.command](path, notes)


if __name__ == "__main__":
    cli()
