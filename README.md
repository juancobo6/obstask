# obstask

**obstask** is a CLI and AI-powered assistant for managing an [Obsidian](https://obsidian.md) vault. Create and link **projects**, **tasks**, **people**, and **meetings** from the terminal or via a conversational agent, and turn daily notes into structured tasks and meetings.

## Features

- **Vault scaffolding** — Initialize a vault with `projects/`, `tasks/`, `people/`, `meetings/`, `daily/`, and templates.
- **Note creation** — Add projects, people, meetings, and tasks with YAML frontmatter and Obsidian wikilinks.
- **Daily notes** — Projects are linked into daily notes; new meetings are appended to today’s daily under the right project.
- **AI agent** — Chat with an agent (Gemini) to create people, meetings, and tasks in the current project context.
- **Parse daily** — Process today’s daily note so the agent can create tasks and meetings from your notes.

## Requirements

- **Python 3.12+**
- For **chat** and **parse**: set `GOOGLE_API_KEY` and `GOOGLE_MODEL` in your environment (e.g. `gemini-2.0-flash`).

## Installation

From the project root:

```bash
uv sync
```

Or install in editable mode:

```bash
pip install -e .
```

The CLI is available as `ot` (or run `python -m obstask.cli`).

## Usage

Run all commands from the **root of your Obsidian vault** (the folder that contains or will contain `projects/`, `tasks/`, etc.).

| Command   | Description |
|----------|-------------|
| `ot init`    | Create directory structure and copy templates. |
| `ot project` | Create a new project (interactive). |
| `ot person`  | Create a person and link to projects. |
| `ot meeting` | Create a meeting (project + attendees). |
| `ot task`    | Create a task (project, due date, status). |
| `ot chat`    | Run the AI agent for the selected project. |
| `ot parse`   | Parse today’s daily note and run the agent. |

### Examples

```bash
cd /path/to/your/vault
ot init
ot project
ot task
ot chat
```

Task due dates in the CLI accept `YYYY-MM-DD`, `MMDD`, or `DD` (current month). Task status is one of: `backlog`, `to do`, `doing`, `done`.

## Vault layout

After `ot init`, the vault looks like:

```
vault/
├── projects/   # Project notes
├── tasks/      # Task notes (project_fk, due_date, status_enum)
├── people/     # People (project_list)
├── meetings/   # Meetings (project_fk, people_list, meeting_date)
├── daily/      # Daily notes (e.g. 2026-03-19.md)
└── templates/  # Daily.md, Meeting.md, People.md, Project.md, Task.md
```

Notes use YAML frontmatter and markdown body; links between notes use Obsidian wikilinks (e.g. `[[projects/My Project|My Project]]`).

## Agent (chat / parse)

- **`ot chat`** — Choose a project, then talk to the agent. It can create people, meetings, and tasks in that project using tools; use **exact** person note filenames for meeting attendees so wikilinks resolve.
- **`ot parse`** — Loads today’s daily note, filters uncompleted entries, and runs the agent so you can turn notes into tasks and meetings.

Set before using:

```bash
export GOOGLE_API_KEY="your-key"
export GOOGLE_MODEL="gemini-2.0-flash"
```

## Development

- **Dependencies**: Pydantic, pydantic-ai, PyYAML, questionary, rich.
- **Entry point**: `ot` → `obstask.cli:cli`.

## License

MIT.
