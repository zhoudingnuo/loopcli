# Model Routing Strategy — Cost Optimization Guide

## GLM Model Pricing (per million tokens)

| Model | Input | Output | Cost Factor |
|-------|-------|--------|-------------|
| GLM-5.1 | $1.40 | $4.40 | 10x (most expensive) |
| GLM-5 | $1.00 | $3.20 | 7x |
| GLM-5-Turbo | $1.20 | $4.00 | 9x |
| GLM-4.7 | **FREE** | **FREE** | 0x (best) |
| GLM-4.5-Air | $0.13-0.20 | $0.85-1.10 | 1x (cheapest paid) |

## Current Usage (2026-05-22)

- GLM-5.1: 71% → **$45/day** ❌
- GLM-4.7: 29% → **$19/day** ✅
- **Total**: $64/day

## Routing Strategy

### Priority Order (cheapest to most expensive)

1. **GLM-4.7** (FREE) — Use for 80% of tasks
   - Code editing
   - File operations
   - Routine tasks
   - Simple queries

2. **GLM-4.5-Air** ($0.13 input) — Use for 15% of tasks
   - Complex reasoning
   - Multi-step analysis
   - When GLM-4.7 hits limits

3. **GLM-5.1** ($1.40 input) — Use for 5% of tasks ONLY
   - Critical decision-making
   - Complex architecture design
   - When cheaper models fail

### Implementation

Model selection is controlled at the GLM Coding Plan level. To implement routing:

1. Configure GLM Coding Plan to prefer GLM-4.7 by default
2. Set GLM-5.1 as fallback only for complex tasks
3. Monitor usage via `glm-plan-usage:usage-query` skill

## Expected Savings

Current: $64/day → Target: $20/day (70% reduction)

## Source

[Z.AI Pricing](https://docs.z.ai/guides/overview/pricing)
