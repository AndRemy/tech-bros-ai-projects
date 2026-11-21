from mcp.server.fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    @mcp.prompt()
    def summarize_notes(topic: str) -> str:
        """Ask the model to summarize all notes about a topic."""
        return f"Use search_notes to find notes about '{topic}' and summarize decisions and open items."
