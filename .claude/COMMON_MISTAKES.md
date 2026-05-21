# Critical Mistakes in LoopCLI

Add bugs here ONLY if they took >1 hour to debug.

## 1. Agent Spin Loops
**Symptom**: Agents create sub-agents infinitely
**Fix**: Always check `run_count` in state.json before spawning

## 2. Memory Bloat
**Symptom**: thoughts.md grows to 1000+ lines
**Fix**: Auto-compress after 50 lines, keep only last 5 rounds

## 3. Inbox Accumulation
**Symptom**: inbox/ fills with unarchived messages
**Fix**: Archive processed messages immediately to inbox/archive/

## 4. Token Waste
**Symptom**: Loading entire history at session start
**Fix**: Use .claudeignore to prevent auto-loading old docs

## 5. Agent Idle Costs
**Symptom**: Agents stay enabled with no tasks
**Fix**: Disabled all idle agents immediately (铁律)
