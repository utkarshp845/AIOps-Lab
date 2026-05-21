# Incident Walkthroughs

These walkthroughs connect the Week 2 observability pieces:

- Metrics show shape, volume, and trend.
- Logs explain specific events.
- Request IDs connect related log lines.
- The AI SRE Assistant should separate facts from guesses.

Use these examples after starting the local stack:

```bash
cp .env.example .env
make up
```

No `make` installed:

```bash
docker compose up --build -d
```

## Walkthroughs

- [Error spike](01-error-spike.md)
- [Latency spike](02-latency-spike.md)
- [Memory pressure](03-memory-pressure.md)

Each walkthrough follows the same pattern:

1. Symptom
2. Reproduce locally
3. Metrics evidence
4. Log evidence
5. Likely cause
6. Safe debugging steps
7. What the AI SRE Assistant should say

