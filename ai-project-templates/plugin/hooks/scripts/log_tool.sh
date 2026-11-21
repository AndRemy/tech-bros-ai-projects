#!/usr/bin/env bash
# Hooks receive the event as JSON on stdin. Append it to a log file.
mkdir -p "$HOME/.notes-toolkit"
cat >> "$HOME/.notes-toolkit/tool-calls.jsonl"
echo >> "$HOME/.notes-toolkit/tool-calls.jsonl"
