"""
This module contains functions which generate small Python scripts which take
various actions such as starting shells and running commands.
"""

import os
from textwrap import dedent


def make_shell_command(
    cwd: str | None = None,
    env: dict[str, str] = {},
    history: list[str] = [],
) -> str:
    """
    Return a Python script which will start a shell.

    Starts the shell specified in the ``SHELL`` environment variable.

    Parameters
    ==========
    cwd : str
        The working directory in which to start the shell.
    env : {name: value, ...}
        Extra environment variables to set.
    history : ["line", ...]
        A list of commands to pre-fill to the shell's history with (sets the
        ``HISTFILE`` to a temporary file with the specified lines).
    """
    # First we generate a Python script which runs the provided shell with
    # 'HISTFILE' populated as requested.
    history_lines = "\n".join(history) + "\n"

    return dedent(
        f"""
            import os, sys, subprocess, tempfile
            from pathlib import Path
            with tempfile.TemporaryDirectory() as d:
                h = Path(d) / "history"
                h.write_text({history_lines!r})
                env = dict(os.environ, HISTFILE=h, **{env!r})
                sys.exit(
                    subprocess.run(
                        env.get("SHELL", "bash"),
                        env=env,
                        cwd={cwd!r},
                    ).returncode
                )
        """
    ).strip()


def make_run_command(
    command: list[str],
    cwd: str | None = None,
    env: dict[str, str] = {},
) -> str:
    """
    Return a Python script which will run the provided command (and arguments).

    Parameters
    ==========
    command : [str, ...]
        The command (and arguments) to run.
    cwd : str
        The working directory in which to start the command.
    env : {name: value, ...}
        Extra environment variables to set.
    """
    return dedent(
        f"""
            import os, sys, subprocess
            sys.exit(
                subprocess.run(
                    {command!r},
                    cwd={cwd!r},
                    env=dict(os.environ, **{env!r}),
                ).returncode
            )
        """
    ).strip()
