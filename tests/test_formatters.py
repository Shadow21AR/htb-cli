"""Tests for formatters module."""


def test_print_error(capsys):
    """Test error message formatting."""
    from htb.formatters import print_error

    print_error("Test error")
    captured = capsys.readouterr()
    assert "Error:" in captured.out
    assert "Test error" in captured.out


def test_print_success(capsys):
    """Test success message formatting."""
    from htb.formatters import print_success

    print_success("Test success")
    captured = capsys.readouterr()
    assert "Test success" in captured.out


def test_create_table():
    """Test table creation."""
    from htb.formatters import create_table

    table = create_table(["A", "B", "C"], "Test Table")
    assert table is not None
    # Table should have 3 columns
    assert len(table.columns) == 3


def test_resolve_output_path(tmp_path):
    """Test output path resolution for files and directories."""
    from htb.files import resolve_output_path

    filename = "example.txt"

    # None -> filename in cwd (relative)
    path = resolve_output_path(None, filename)
    assert path.name == filename

    # Directory path -> filename inside directory
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    path = resolve_output_path(out_dir, filename)
    assert path.parent == out_dir
    assert path.name == filename
