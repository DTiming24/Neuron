# Neuron V1 Py DIY

A cleaned public build of the Neuron project.

## What’s included

- Flask-based web app in `Crystal/Armor/`
- HTML templates in `html/`
- modular tool files for chat, memory, time, system, and web access

## Notes

- Private user data, old experiments, and generated artifacts were removed from this public version.
- Runtime user files are expected to be created locally and are ignored by git.

## Running

The app expects the usual Python dependencies used by the project and an `OPENROUTER_API_KEY` environment variable for chat access.

Optional web tools:
- `ddgs`
- `beautifulsoup4`
- `playwright`

If you want web search and page fetch features, install those extras too.

Start point:
- `Crystal/Armor/server.py`
