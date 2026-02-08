# CLAUDE.md

## Project Overview

**Maintain Moral Standards** is a web application for editing, organizing, and maintaining moral standards and clusters of standards used by the EE (Ethical Engine) system. It uses a Flask REST API backend with a vanilla JavaScript frontend and JSON file-based storage.

## Architecture

```
maintain_standards/
├── backend/               # Flask REST API
│   ├── app.py             # Flask app, routes, auth decorators
│   ├── library_controller.py  # Business logic (singleton controller)
│   ├── file_operations.py # JSON file persistence (FileManager)
│   ├── models.py          # Dataclass models (Standard, Cluster, MACVector, etc.)
│   ├── validator.py       # Library validation rules
│   └── users.json         # Authorized user/role mapping
├── frontend/              # Vanilla JS single-page app
│   ├── app.js             # All frontend logic
│   ├── index.html         # HTML template
│   └── styles.css         # Styling
├── standards_library/     # JSON data storage
│   ├── library.json       # Main library data
│   ├── backups/           # Timestamped backups (max 5)
│   └── exports/           # Exported library files
├── tests/                 # pytest test directory
├── docs/                  # Domain documentation
├── Dockerfile             # Container config (Cloud Run)
├── entrypoint.sh          # Container data seeding script
└── pyproject.toml         # Project config, dependencies, tool settings
```

### Key Layers

- **Models** (`models.py`): Python dataclasses with `to_dict()` serialization. Core types: `Library`, `Cluster`, `Standard`, `MACVector` (7-dimensional moral composition vector that must sum to 1.0), `MACRationale`.
- **Controller** (`library_controller.py`): `LibraryController` singleton instantiated at module level in `app.py`. Handles all CRUD, import/export, backup/restore logic.
- **File Operations** (`file_operations.py`): `FileManager` handles JSON persistence via `pathlib.Path`. Data directory configured via `DATA_PATH` env var (defaults to `standards_library/`).
- **Validation** (`validator.py`): `LibraryValidator` checks MAC vector sums, cluster references, duplicate IDs, required fields, and missing rationales.
- **Routes** (`app.py`): REST endpoints with `@login_required` and `@admin_required` decorators. Google OAuth2 via authlib.
- **Frontend** (`app.js`): Vanilla JS SPA with state management, search/filter, tab-based detail views, and CRUD UI.

## Development Setup

```bash
# Install in editable mode with dev dependencies
pip install -e .[dev]
```

### Running Locally

```bash
# Start the Flask dev server
cd backend && python app.py

# Or with gunicorn (production-like)
gunicorn --bind 0.0.0.0:8080 --chdir backend app:app
```

### Docker

```bash
docker build -t maintain-standards .
docker run -p 8080:8080 maintain-standards
```

The container uses `/tmp/standards_library` as data path (Cloud Run read-only filesystem).

## Commands

### Linting and Formatting

```bash
# Format code with Black
black backend/

# Lint with ruff
ruff check backend/

# Lint and auto-fix
ruff check --fix backend/
```

### Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v
```

Note: Test coverage is currently minimal (single placeholder test in `tests/test_example.py`).

## Code Style and Conventions

### Python (Backend)

- **Formatter**: Black (line length 88)
- **Linter**: Ruff with rules: `E` (pycodestyle errors), `F` (pyflakes), `I` (isort), `W` (pycodestyle warnings)
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes
- **Type hints**: Used throughout models and controller
- **Docstrings**: Present on all classes and public methods
- **Models**: Use `@dataclass` with `to_dict()` methods for JSON serialization
- **Python version**: >= 3.8

### JavaScript (Frontend)

- **Naming**: `camelCase` for functions/variables
- **No framework**: Vanilla JS with direct DOM manipulation
- **No build step**: Served as static files

### Data Constraints

- MAC vectors have 7 dimensions (family, group, reciprocity, heroism, deference, fairness, property) and **must sum to 1.0**
- Importance weights must be in range `[0.0, 1.0]`
- Standard IDs and Cluster IDs must be unique
- Standards must reference an existing cluster

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/info` | None | Library version info |
| GET | `/api/user` | None | Current user session |
| GET | `/login` | None | Initiate Google OAuth2 |
| GET | `/auth/callback` | None | OAuth2 callback |
| GET | `/logout` | None | Clear session |
| GET | `/api/standards` | login | List all standards |
| POST | `/api/standards` | admin | Create standard |
| PUT | `/api/standards/<id>` | admin | Update standard |
| DELETE | `/api/standards/<id>` | admin | Delete standard |
| GET | `/api/clusters` | login | List all clusters |
| POST | `/api/clusters` | admin | Create cluster |
| PUT | `/api/clusters/<id>` | admin | Update cluster |
| DELETE | `/api/clusters/<id>` | admin | Delete cluster |
| POST | `/api/backup` | admin | Create backup |
| GET | `/api/backups` | admin | List backups |
| GET | `/api/backups/<file>` | admin | Download backup |
| DELETE | `/api/backups/<file>` | admin | Delete backup |
| POST | `/api/restore` | admin | Restore from upload |
| POST | `/api/restore/<file>` | admin | Restore from server backup |
| POST | `/api/export` | login | Export with filters |
| POST | `/api/import` | admin | Import from file |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_PATH` | `standards_library` | Path to library data directory |
| `SECRET_KEY` | `dev_secret_key` | Flask session secret (change in production) |
| `GOOGLE_CLIENT_ID` | (none) | Google OAuth2 client ID |
| `GOOGLE_CLIENT_SECRET` | (none) | Google OAuth2 client secret |

## Important Patterns

- **Singleton controller**: `LibraryController` is instantiated once in `app.py` and shared across all requests.
- **File-based storage**: All data persists as JSON. No database. The `FileManager` handles all reads/writes.
- **Backup rotation**: Maximum 5 backups retained; oldest are automatically deleted.
- **Import strategy**: Two-pass merge -- clusters first, then standards. Existing items are updated; new items are added.
- **Cluster deletion guard**: Clusters cannot be deleted if any standards reference them.
- **Cluster ordering**: Clusters have an `order` field; reordering shifts other clusters automatically.
