"""Entrypoint: build the server, register every module, run."""
from mcp.server.fastmcp import FastMCP

from notes_mcp.prompts import summarize
from notes_mcp.resources import notes as notes_resources
from notes_mcp.store import NoteStore
from notes_mcp.tools import notes as notes_tools

mcp = FastMCP("notes")
store = NoteStore()

notes_tools.register(mcp, store)
notes_resources.register(mcp, store)
summarize.register(mcp)


def main() -> None:
    mcp.run()  # stdio by default; use transport="streamable-http" for remote


if __name__ == "__main__":
    main()
