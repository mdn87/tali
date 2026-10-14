# Fact skeleton: guides/setup.md

## Claims
- C1: Setup takes about 20 minutes.
- C2: npm install can change the lockfile, which is why npm ci is required.
- C3: The agent prints ready when listening; a taken port is handled with --port.
- C4: tali-agent --check exits 0 when the agent, CLI, and config file agree.

## Verbatim
- V1: `npm ci`
- V2: `npm install`
- V3: `tali-agent --port 8080`
- V4: `~/.tali/config.toml`
- V5: `tali-agent --check`
- V6: Node.js 22

## Qualifiers
- Q1: only when the sync service is running

## Distinctions
- D1: the CLI reads ~/.tali/config.toml; the desktop app does not read that file
- D2: the CLI and the desktop app are different programs with separate settings
