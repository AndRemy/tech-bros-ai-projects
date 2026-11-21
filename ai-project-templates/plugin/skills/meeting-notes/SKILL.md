---
name: meeting-notes
description: Turns raw meeting notes or transcripts into structured minutes with decisions and action items. Use when the user shares meeting notes, a transcript, or asks for minutes, a recap, or action items.
---

# Meeting notes

## Steps
1. Read the raw notes the user provided.
2. Extract action items deterministically:
   `python scripts/extract_actions.py <notes-file>`
   (lines starting with `TODO`, `AI:`, or `@name` become action items).
3. Fill in `assets/template.md`, following the tone rules in
   `reference/style-guide.md` (read it only if you're unsure about wording).
4. If an MCP tool named `save_note` is available, offer to save the result with it.

## Rules
- Never invent decisions; if something is unclear, list it under "Open questions".
- Every action item needs an owner and, if mentioned, a date.
