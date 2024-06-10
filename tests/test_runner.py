import pytest

from subprocess import run, CompletedProcess


def slidie_ttyd_runner(args: list[str], input: str | None = None) -> CompletedProcess:
    return run(
        ["slidie-ttyd-runner"] + args,
        input=input,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize(
    "args",
    [
        ["--cmd", "echo hello"],
        ["--argv", "echo", "--argv", "hello"],
    ],
)
def test_run(args: list[str]) -> None:
    # Just a simple smoke test
    assert slidie_ttyd_runner(["run"] + args).stdout == "hello\n"


def test_shell() -> None:
    # Just a simple smoke test
    assert slidie_ttyd_runner(["shell"], input="echo hello\n").stdout == "hello\n"
