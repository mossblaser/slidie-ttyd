"""
This module contains functions which generate small Python scripts for starting
shells or running arbitrary commands with particular environment variables or
working directories.

The generated scripts can be ``exec()``\ 'd locally or, more compellingly, sent
via SSH to a remote Python interpreter to achieve the same results on a remote
system. (Note that SSH alone does not provide a robust mechanism for
pre-configuring the remote environment along with extra files). It is this
latter purpose which motivates the generation of Python scripts rather than
just having ordinary functions here to do the same work!
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
