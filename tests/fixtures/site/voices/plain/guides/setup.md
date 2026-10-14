# Setup

Run `npm ci` from the repo root, then start the agent:

```
tali-agent --port 8080
```

Only the CLI reads `~/.tali/config.toml`; the desktop app does not. Uploads
work only when the sync service is running. ![Architecture](diagrams/arch.png)

##### Troubleshooting

- [ ] Port 8080 is free
- [x] Config file exists
