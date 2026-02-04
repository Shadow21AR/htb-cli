"""File helpers for CLI output."""

from pathlib import Path


def resolve_output_path(output: Path | None, filename: str) -> Path:
    """Resolve output path, creating parents when needed."""
    if output is None:
        path = Path(filename)
    else:
        path = output
        if path.exists() and path.is_dir():
            path = path / filename

    path.parent.mkdir(parents=True, exist_ok=True)
    return path
