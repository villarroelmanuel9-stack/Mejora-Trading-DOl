import click
import os
from dotenv import load_dotenv
from metatrader_mcp.utils import resolve_transport_config, run_mcp

@click.command()
@click.option("--login", required=True, type=int, help="MT5 login ID")
@click.option("--password", required=True, help="MT5 password")
@click.option("--server", required=True, help="MT5 server name")
@click.option("--path", default=None, help="Path to MT5 terminal executable (optional, auto-detected if not provided)")
@click.option("--transport", default=None, type=click.Choice(["sse", "stdio", "streamable-http"], case_sensitive=False), help="MCP transport type (default: sse, env: MCP_TRANSPORT)")
@click.option("--host", default=None, help="Host to bind for SSE/HTTP transport (default: 0.0.0.0, env: MCP_HOST)")
@click.option("--port", default=None, type=int, help="Port to bind for SSE/HTTP transport (default: 8080, env: MCP_PORT)")
@click.option("--allow-trading", is_flag=True, default=False, help="Enable tools that place, modify, close or cancel orders (default: read-only)")
def main(login, password, server, path, transport, host, port, allow_trading):
    """Launch the MetaTrader MCP server."""
    load_dotenv()
    # override env vars if provided via CLI
    os.environ["login"] = str(login)
    os.environ["password"] = password
    os.environ["server"] = server
    if path:
        os.environ["MT5_PATH"] = path

    if allow_trading:
        os.environ["MT5_READ_ONLY"] = "false"

    # imported here so the read-only setting is known when the tools are registered
    from metatrader_mcp.server import mcp

    transport, host, port = resolve_transport_config(transport, host, port)
    run_mcp(mcp, transport, host, port)

if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
