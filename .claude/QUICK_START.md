# Quick Start Commands

## Running LoopCLI
```bash
cd D:/loopcli/main && python run.py
```

## Git Operations
```bash
cd D:/loopcli
git status
git add -A
git commit -m "message"
```

## Agent Management
```bash
# List all agents
find . -name "AGENT" -type f

# Check agent status
cat */AGENT
```

## Memory Operations
```bash
# View current state
cat main/memory/state.json

# View thoughts
cat main/memory/thoughts.md
```

## Testing
```bash
cd D:/loopcli/main && python -m pytest tests/
```
