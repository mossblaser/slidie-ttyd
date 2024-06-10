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


def add_run_args(parser: ArgumentParser) -> None:
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


def do_run(args: Namespace) -> None:
    run_script(
        args,
        make_run_command(
            args.argv,
            cwd=args.cwd,
            env=dict(args.env),
        ),
    )


def add_shell_args(parser: ArgumentParser) -> None:
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


def do_shell(args: Namespace) -> None:
    run_script(
        args,
        make_shell_command(
            history=args.history,
            cwd=args.cwd,
            env=dict(args.env),
        ),
    )


def main() -> None:
    parser = ArgumentParser(description="For internal use. Run a command or shell.")

    subparsers = parser.add_subparsers(required=True)

    run_parser = subparsers.add_parser("run", help="Run a command.")
    run_parser.set_defaults(action=do_run)
    add_run_args(run_parser)

    shell_parser = subparsers.add_parser("shell", help="Start a shell.")
    shell_parser.set_defaults(action=do_shell)
    add_shell_args(shell_parser)

    args = parser.parse_args()
    args.action(args)
