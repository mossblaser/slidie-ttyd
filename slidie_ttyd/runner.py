"""
A command-line utility intended only for use by slidie-ttyd which runs command
line applications either locally or on a remote host (via SSH).

Example usage::

    $ slidie-ttyd-run --command "echo hello"
    hello

    $ slidie-ttyd-run --ssh user@host --command "hostname"
    host

    $ slidie-ttyd-shell --history "echo hello"
    $ <press up>
    $ echo hello
"""

from argparse import ArgumentParser, Namespace
import shlex
import sys
import subprocess

from slidie_ttyd.script_generators import make_run_command, make_shell_command


def environment_variable(arg: str) -> tuple[str, str]:
    """
    Parse an environment variable argument.
    """
    name, _, value = arg.partition("=")
    return (name, value)


def add_common_args(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--cwd",
        metavar="PATH",
        type=str,
        help="""
            Set the working directory for to run the command in.
        """,
    )
    parser.add_argument(
        "--env",
        metavar="NAME=VALUE",
        action="append",
        default=[],
        type=environment_variable,
        help="""
            Use mutliple times to set environment variables for the executed
            command.
        """,
    )

    parser.add_argument(
        "--ssh",
        metavar="SSH_ARG",
        action="append",
        type=str,
        help="""
            If given, run the command on a remote host using SSH rather than
            locally. Each invocation adds the provided argument as an argument
            to the SSH command. A minimal use would be `--ssh name@host`,
            additional arguments may be used for more complex SSH connection
            options.
        """,
    )


def run_script(args: Namespace, script: str) -> None:
    """
    Run a Python script (either locally or on a remote host).
    """
    if args.ssh:
        command = (
            ["ssh"]
            + args.ssh
            + [
                "python",
                "-c",
                # NB: Extra level of quoting needed as remote shell will
                # unquote arguments
                shlex.quote(script),
            ]
        )
    else:
        command = ["python", "-c", script]

    sys.exit(subprocess.run(command).returncode)


def main_run() -> None:
    parser = ArgumentParser(
        description="""
            For internal use by slidie-ttyd. Run a command.
        """
    )

    add_common_args(parser)

    cmd_group = parser.add_mutually_exclusive_group(required=True)
    cmd_group.add_argument(
        "--cmd",
        type=shlex.split,
        dest="argv",
        help="""
            A command, to be parsed into separate arguments using typical shell
            parsing rules.
        """,
    )
    cmd_group.add_argument(
        "--argv",
        action="append",
        type=str,
        help="""
            Use multiple times to specify the command and arguments
            individually.
        """,
    )

    args = parser.parse_args()

    run_script(
        args,
        make_run_command(
            args.argv,
            cwd=args.cwd,
            env=dict(args.env),
        ),
    )


def main_shell() -> None:
    parser = ArgumentParser(
        description="""
            For internal use by slidie-ttyd. Start a shell.
        """
    )

    parser.add_argument(
        "--history",
        action="append",
        default=[],
        type=str,
        help="""
            Add a line to the shell's history. Repeat to add additional lines.
        """,
    )

    add_common_args(parser)

    args = parser.parse_args()

    run_script(
        args,
        make_shell_command(
            history=args.history,
            cwd=args.cwd,
            env=dict(args.env),
        ),
    )
