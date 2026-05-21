# LoopCLI Architecture

## Core System

```
loopcli/
├── main/                    # Primary agent (self-improving)
│   ├── PROMPT.md            # Execution instructions
│   ├── SOUL.md              # Core identity & goals
│   ├── run.py               # Main entry point
│   ├── memory/              # Persistent memory
│   │   ├── state.json       # Current state
│   │   └── thoughts.md      # Thinking log (compressed)
│   └── inbox/               # Message queue
│       └── archive/         # Processed messages
├── engineering-*/           # Specialist agents
└── market-analyst/          # Market analysis
```

## Agent Structure

Each agent has:
- `AGENT` - Type & status (disabled=true when idle)
- `PROMPT.md` - What to do each cycle
- `SOUL.md` - Core purpose & behavior
- `memory/` - Persistent data

## Communication

- `inbox/` - Receive messages
- `D:/loopcli/meeting/` - Cross-agent collaboration
- Target agent's `inbox/` - Send messages

## Key Patterns

1. **Cost Control**: Disable idle agents immediately
2. **Memory Compression**: thoughts.md ≤ 50 lines
3. **Value First**: User requests > profit > cost > maintenance
4. **One Thing Per Round**: Do ONE valuable thing, then stop
