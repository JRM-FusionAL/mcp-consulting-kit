# t3610 Christopher Runbook

Use this to manage `Christopher-AI` on `t3610` with a persistent `tmux` session.

## Prerequisites

- Host alias `t3610` is reachable via SSH.
- Repo path exists: `/home/jrm_fusional/Projects/Christopher-AI`
- MCP stack already running on host (`8101`, `8102`, `8103`, `8104`, `8009`).

## 1) Start Christopher (chat mode, no local llama-server launch)

```bash
ssh t3610 'tmux kill-session -t christopher 2>/dev/null; tmux new-session -d -s christopher "cd /home/jrm_fusional/Projects/Christopher-AI && /usr/bin/python3 ./christopher.py --chat --no-server"'
```

## 2) Verify session is alive

```bash
ssh t3610 'tmux has-session -t christopher && echo CHRISTOPHER_UP || echo CHRISTOPHER_DOWN'
```

## 3) Attach to live session

```bash
ssh -t t3610 'tmux attach -t christopher'
```

Detach without stopping with:

- `Ctrl+b`, then `d`

## 4) View recent output without attaching

```bash
ssh t3610 'tmux capture-pane -t christopher -p | tail -n 40'
```

## 5) Restart Christopher

```bash
ssh t3610 'tmux kill-session -t christopher 2>/dev/null; tmux new-session -d -s christopher "cd /home/jrm_fusional/Projects/Christopher-AI && /usr/bin/python3 ./christopher.py --chat --no-server"'
```

## 6) Stop Christopher

```bash
ssh t3610 'tmux kill-session -t christopher'
```

## 7) Quick service status check (all MCP + FusionAL)

```bash
ssh t3610 'for p in 8009 8101 8102 8103 8104; do if ss -ltn | grep -q ":$p "; then echo PORT-$p=UP; else echo PORT-$p=DOWN; fi; done'
```
