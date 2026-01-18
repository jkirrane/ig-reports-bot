#!/usr/bin/env python3
"""
Analyze LLM usage and costs
"""

import json

try:
    with open('llm_usage.log', 'r') as f:
        entries = [json.loads(line) for line in f]
    
    print('\n📊 LLM Usage Summary:\n')
    print(f'Total API calls: {len(entries)}')
    print(f'Total tokens: {sum(e["total_tokens"] for e in entries):,}')
    print(f'  - Prompt tokens: {sum(e["prompt_tokens"] for e in entries):,}')
    print(f'  - Completion tokens: {sum(e["completion_tokens"] for e in entries):,}')
    print(f'\nTotal cost: ${sum(e["cost"] for e in entries):.4f}')
    print(f'Average cost per call: ${sum(e["cost"] for e in entries) / len(entries):.4f}\n')
    
    print('Per-call breakdown:')
    for i, e in enumerate(entries, 1):
        print(f'  {i}. {e["prompt_tokens"]:3d} + {e["completion_tokens"]:3d} tokens = ${e["cost"]:.4f}')
    
    # Projections
    daily_filter_cost = 100 * (sum(e["cost"] for e in entries if e["prompt_tokens"] > 400) / max(1, sum(1 for e in entries if e["prompt_tokens"] > 400)))
    daily_summary_cost = 15 * (sum(e["cost"] for e in entries if e["prompt_tokens"] < 400) / max(1, sum(1 for e in entries if e["prompt_tokens"] < 400)))
    
    if len(entries) > 0:
        print(f'\n💰 Projected Daily Costs (based on actual usage):')
        print(f'  Filter: 100 reports × ${sum(e["cost"] for e in entries if e["prompt_tokens"] > 400) / max(1, sum(1 for e in entries if e["prompt_tokens"] > 400)):.4f} = ${daily_filter_cost:.2f}')
        print(f'  Summary: 15 posts × ${sum(e["cost"] for e in entries if e["prompt_tokens"] < 400) / max(1, sum(1 for e in entries if e["prompt_tokens"] < 400)):.4f} = ${daily_summary_cost:.2f}')
        print(f'  Daily total: ${daily_filter_cost + daily_summary_cost:.2f}')
        print(f'  Monthly estimate: ${(daily_filter_cost + daily_summary_cost) * 30:.2f}')

except FileNotFoundError:
    print('No llm_usage.log file found. Run some LLM tests first.')
except Exception as e:
    print(f'Error: {e}')
