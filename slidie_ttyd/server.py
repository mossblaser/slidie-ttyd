"""
The main slidie-ttyd application.
"""

from argparse import ArgumentParser
from pathlib import Path
from urllib.parse import quote as urlencode
import asyncio

from aiohttp import web


routes = web.RouteTableDef()


@routes.get("/")
async def get_slides(request: web.Request) -> web.Response:
    if request.app["slides"].is_file():
        return web.FileResponse(request.app["slides"])
    else:
        raise web.HTTPNotFound()


@routes.get("/{action:run|shell}")
async def get_ttyd_redirect(request: web.Request) -> web.Response:
    query = {k: request.query.getall(k) for k in request.query}

    # Normalise underscore keys to hyphens
    query = {k.replace("_", "-"): vs for k, vs in query.items()}

    # Pull out terminal parameters
    font_name = query.pop("font-name", [request.app["default-font-name"]])[0]
    font_size = int(query.pop("font-size", [request.app["default-font-size"]])[0])

    # Construct ttyd query parameters
    ttyd_query = [
        ("fontSize", str(font_size)),
        # Don't flash up terminal size on first load (who needs that?)
        ("disableResizeOverlay", "true"),
        # Don't confirm on leaving page (this doesn't make sense for a slide
        # show
        ("disableLeaveAlert", "true"),
        # Set the action to run
        ("arg", request.match_info["action"]),
    ]
    if font_name is not None:
        ttyd_query.append(("fontFamily", font_name))

    # Pass remaining arguments to runner (query parameters are expanded into
    # --name=value arguments to the runner, via the 'arg' facility of ttyd).
    for key, values in query.items():
        for value in values:
            ttyd_query.append(("arg", f"--{key}={value}"))

    raise web.HTTPFound(
        f"http://{request.app['ttyd-host']}:{request.app['ttyd-port']}/?"
        + "&".join(f"{key}={urlencode(value)}" for key, value in ttyd_query)
    )


async def start_ttyd(app: web.Application) -> None:
    """Start the ttyd subprocess."""
    app["ttyd"] = await asyncio.create_subprocess_exec(
        "ttyd",
        # Serve on specified port
        "-i",
        app["ttyd-host"],
        "-p",
        str(app["ttyd-port"]),
        # Allow user input ('write')
        "-W",
        # Allow passing arguments
        "-a",
        # Don't repeatedly attempt to restart a command/shell which has exited
        "-t",
        "disableReconnect=true",
        # Run the runner
        "slidie-ttyd-runner",
    )


async def shutdown_ttyd(app: web.Application) -> None:
    """Shutdown the ttyd subprocess."""
    app["ttyd"].terminate()
    try:
        async with asyncio.timeout(3):
            await app["ttyd"].wait()
    except TimeoutError:
        app["ttyd"].kill()


def make_app(
    slides: Path,
    ttyd_host: str = "127.0.0.1",
    ttyd_port: int = 8081,
    font_name: str | None = None,
    font_size: int = 30,
    run_ttyd: bool = True,
) -> web.Application:
    app = web.Application()

    app.add_routes(routes)
    app.add_routes([web.static("/", slides.parent)])

    if run_ttyd:
        app.on_startup.append(start_ttyd)
        app.on_shutdown.append(shutdown_ttyd)

    app["slides"] = slides
    app["ttyd-host"] = ttyd_host
    app["ttyd-port"] = ttyd_port
    app["default-font-name"] = font_name
    app["default-font-size"] = font_size

    return app


def main() -> None:
    parser = ArgumentParser(
        description="""
            Start the slidie-ttyd server.
        """,
    )

    parser.add_argument(
        "slides",
        type=Path,
        nargs="?",
        default=Path("out.xhtml"),
        help="""
            The rendered slidie XHTML slides to serve at `/`. Defaults to
            %(default)s. This may be set arbitrarily or ignored if you don't
            want to host your slides on this server.
        """,
    )
    parser.add_argument(
        "--host",
        "-H",
        type=str,
        default="127.0.0.1",
        help="""
            Host/IP to serve on. Default %(default)s.
        """,
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8080,
        help="""
            Port number to serve on. ttyd will be served on this port + 1.
            Default %(default)s.
        """,
    )
    parser.add_argument(
        "--font-size",
        "-f",
        type=int,
        default=30,
        help="""
            The default font size for the terminal. Default: %(default)s.
        """,
    )
    parser.add_argument(
        "--font-name",
        "-F",
        type=str,
        default=None,
        help="""
            The default font family name for the terminal.
        """,
    )

    args = parser.parse_args()

    app = make_app(
        slides=args.slides,
        ttyd_host=args.host,
        ttyd_port=args.port + 1,
        font_name=args.font_name,
        font_size=args.font_size,
    )
    web.run_app(app, host=args.host, port=args.port)
