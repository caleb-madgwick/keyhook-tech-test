# Model comparison: `tenant_emails.json` (split: all, repeats: 3, prompt v5)

| model | pass | category | urgency | under-triage | emergency recall | esc. recall | esc. precision | fail-safe | $/1k msgs | p50 latency | gates |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `anthropic/claude-haiku-5.5` | 86% | 96% | 92% | 0 | 100% | 100% | 96% | 0 | $0.40 | 4074.0 ms | PASS |
| `openai/gpt-6-luna` | 90% | 94% | 93% | 3 | 100% | 98% | 100% | 0 | $0.25 | 3794.0 ms | PASS |
| `google/gemini-3.5-flash-lite` | 80% | 94% | 96% | 3 | 100% | 98% | 83% | 0 | $1.74 | 1782.0 ms | PASS |
| `deepseek/deepseek-v4-flash` | 86% | 94% | 98% | 2 | 100% | 84% | 100% | 1 | $0.16 | 8075 ms | 2 failed |
| `anthropic/claude-sonnet-5.5` | 92% | 96% | 97% | 0 | 100% | 100% | 100% | 0 | $7.05 | 5121.0 ms | PASS |
