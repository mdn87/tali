# Setup

1. Install dependencies.
2. Start the agent.

Run `npm ci` in the repo root, then start the agent:

```
tali-agent --port 8080
```

The CLI reads `~/.tali/config.toml`; the desktop app does not. Uploads work
only when the sync service is running.
