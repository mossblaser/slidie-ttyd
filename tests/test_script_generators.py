import pytest

from subprocess import run, CompletedProcess
from pathlib import Path
from textwrap import dedent

from slidie_ttyd.script_generators import (
    make_shell_command,
    make_run_command,
)


def run_python_code(
    oneliner: str,
    input: str = "",
) -> CompletedProcess:
    res = run(
        ["python", "-c", f"exec({oneliner!r})"],
        input=input,
        capture_output=True,
        encoding="utf-8",
    )
    return res


class TestRunCommand:

    def test_simple(self) -> None:
        result = run_python_code(make_run_command(["echo", "hello"]))
        assert result.returncode == 0
        assert result.stdout == "hello\n"

    def test_quoteables(self) -> None:
        result = run_python_code(make_run_command(["echo", "'\"hello\n  world!"]))
        assert result.returncode == 0
        assert result.stdout == "'\"hello\n  world!\n"

    def test_error_return(self) -> None:
        result = run_python_code(make_run_command(["false"]))
        assert result.returncode != 0
        assert result.stdout == ""

    def test_cwd(self, tmp_path: Path) -> None:
        result = run_python_code(make_run_command(["pwd"], cwd=str(tmp_path)))
        assert result.stdout == f"{tmp_path}\n"

    def test_environ(self) -> None:
        result = run_python_code(
            make_run_command(
                [
                    "python",
                    "-c",
                    "import os; print(os.environ.get('FOO'))",
                ],
                env={"FOO": "bar"},
            ),
        )
        assert result.stdout == "bar\n"


class TestShellCommand:

    def test_simple(self) -> None:
        result = run_python_code(
            make_shell_command(),
            "echo hello\n",
        )
        assert result.returncode == 0
        assert result.stdout == "hello\n"

    def test_error_return(self) -> None:
        result = run_python_code(
            make_shell_command(),
            "exit 123\n",
        )
        assert result.returncode == 123
        assert result.stdout == ""

    def test_cwd(self, tmp_path: Path) -> None:
        result = run_python_code(
            make_shell_command(cwd=str(tmp_path)),
            "pwd\n",
        )
        assert result.returncode == 0
        assert result.stdout == f"{tmp_path}\n"

    def test_environ(self) -> None:
        result = run_python_code(
            make_shell_command(env={"FOO": "bar"}),
            "echo $FOO\n",
        )
        assert result.returncode == 0
        assert result.stdout == "bar\n"

    def test_history(self) -> None:
        result = run_python_code(
            make_shell_command(history=["foo bar", "baz qux"]),
            "set -o history\nhistory\n",
        )
        assert result.returncode == 0
        assert (
            dedent(result.stdout)
            == dedent(
                """
                1  foo bar
                2  baz qux
                3  history
            """
            ).lstrip()
        )

    def test_custom_shell(self) -> None:
        result = run_python_code(
            make_shell_command(env={"SHELL": "python"}),
            "print(100 + 23)\n",
        )
        assert result.returncode == 0
        assert result.stdout == "123\n"
