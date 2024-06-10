import pytest

from typing import Callable, Awaitable
from pathlib import Path
from urllib.parse import urlparse, parse_qsl

import aiohttp
from aiohttp import web

from slidie_ttyd.server import make_app


@pytest.fixture
async def app(tmp_path: Path) -> web.Application:
    return make_app(tmp_path / "out.xhtml", run_ttyd=False)


@pytest.fixture
async def client(
    app: web.Application,
    aiohttp_client: Callable[[web.Application], aiohttp.ClientSession],
) -> aiohttp.ClientSession:
    return await aiohttp_client(app)


class TestFileServing:

    async def test_index(self, tmp_path: Path, client: aiohttp.ClientSession) -> None:
        (tmp_path / "out.xhtml").write_text("Hello")
        resp = await client.get("/")
        assert resp.status == 200
        assert await resp.text() == "Hello"

    async def test_index_404(
        self, tmp_path: Path, client: aiohttp.ClientSession
    ) -> None:
        resp = await client.get("/")
        assert resp.status == 404

    async def test_other_files(
        self, tmp_path: Path, client: aiohttp.ClientSession
    ) -> None:
        (tmp_path / "foo.txt").write_text("Hello")
        resp = await client.get("/foo.txt")
        assert resp.status == 200
        assert await resp.text() == "Hello"


RunActionFn = Callable[[str], Awaitable[list[tuple[str, str]]]]


class TestTTYDRedirect:

    @pytest.fixture
    def run_action(self, client: aiohttp.ClientSession) -> RunActionFn:
        async def run_action(path: str) -> Awaitable[list[tuple[str, str]]]:
            resp = await client.request("get", path, allow_redirects=False)
            assert resp.status == 302
            return parse_qsl(urlparse(resp.headers["Location"]).query)

        return run_action

    async def test_default_client_options(self, run_action: RunActionFn) -> None:
        qsl = await run_action("/shell")
        assert ("disableResizeOverlay", "true") in qsl
        assert ("disableLeaveAlert", "true") in qsl

    async def test_font_size(self, run_action: RunActionFn) -> None:
        qsl = await run_action("/shell?font_size=123")
        assert ("fontSize", "123") in qsl

    async def test_font_name(self, run_action: RunActionFn) -> None:
        qsl = await run_action("/shell?font_name=FontyMcFontFace")
        assert ("fontFamily", "FontyMcFontFace") in qsl

    @pytest.mark.parametrize("action", ["run", "shell"])
    async def test_action(self, run_action: RunActionFn, action: str) -> None:
        qsl = await run_action(f"/{action}")
        args = [v for k, v in qsl if k == "arg"]
        assert args[0] == action

    async def test_other_args_passed_as_long_args(
        self, run_action: RunActionFn
    ) -> None:
        qsl = await run_action(
            "/run?foo=bar&foo=baz&qux=quo&dash-arg=dash&underscore_arg=underscore&spaces=a+b"
        )
        args = [v for k, v in qsl if k == "arg"]
        assert args == [
            "run",
            "--foo=bar",
            "--foo=baz",
            "--qux=quo",
            "--dash-arg=dash",
            "--underscore-arg=underscore",
            "--spaces=a b",
        ]
