# Setup
**Status:** example

This guide gets a new machine to a working sync agent. Plan on about 20 minutes.

## Install

1. Install Node.js 22 or newer.
2. Clone the tools repository and run `npm ci` in the repo root. Don't run `npm install`, because it can change the lockfile.
3. Start the agent:

```
tali-agent --port 8080
```

You'll see `ready` once the agent is listening. If the port is taken, pick another one with `--port`.

## The CLI and the desktop app are different programs

The CLI reads its settings from `~/.tali/config.toml`. The desktop app does not read that file; it keeps its own settings in its preferences window, so changing one doesn't change the other.

Uploads from either program work only when the sync service is running, so if an upload fails, check the agent first.

## Verify

**Recommended.** Run `tali-agent --check` when you're done. It exits 0 when the agent, the CLI, and the config file all agree.

- [ ] Port 8080 is free or `--port` is set
- [ ] `~/.tali/config.toml` exists
- [ ] `tali-agent --check` exits 0
