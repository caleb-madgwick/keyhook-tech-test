# Model comparison: `tenant_emails_test_suite.json` (split: all, repeats: 1, prompt v5)

| model | pass | category | urgency | under-triage | emergency recall | esc. recall | esc. precision | fail-safe | $/1k msgs | p50 latency | gates |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `anthropic/claude-haiku-5.5` | 72% | 91% | 91% | 2 | 100% | 99% | 78% | 1 | $0.54 | 5222.5 ms | 1 failed |
| `openai/gpt-6-luna` | 80% | 93% | 93% | 5 | 100% | 97% | 88% | 0 | $0.32 | 4580 ms | PASS |
| `google/gemini-3.5-flash-lite` | 72% | 89% | 90% | 9 | 90% | 96% | 88% | 0 | $1.80 | 1787 ms | 1 failed |
| `deepseek/deepseek-v4-flash` | 76% | 89% | 92% | 10 | 95% | 91% | 91% | 2 | $0.19 | 8899 ms | 2 failed |
