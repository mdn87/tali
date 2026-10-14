# Setup
**Status:** example

This guide takes a new machine from nothing to a working sync agent. Expect it to take about 20 minutes.

## Install

1. Install Node.js 22 or newer.
2. Clone the tools repository and run `npm ci` in the repo root. Do not run `npm install`; it can change the lockfile.
3. Start the agent:

```
tali-agent --port 8080
```

The agent prints `ready` when it is listening. If the port is taken, pass a different one with `--port`.

## The CLI and the desktop app are different programs

The CLI reads its settings from `~/.tali/config.toml`; the desktop app does not read that file and keeps its own settings in its preferences window. Changing one does not change the other.

Uploads from either program work only when the sync service is running. If an upload fails, check the agent first.

## Verify

**Recommended.** Run `tali-agent --check` after setup. It exits 0 when the agent, the CLI, and the config file all agree.

- [ ] Port 8080 is free or `--port` is set
- [ ] `~/.tali/config.toml` exists
- [ ] `tali-agent --check` exits 0
