# Contributing

Thanks for helping improve `ai-infra-starter-kit`.

The main rule is simple: keep the project beginner-friendly without making it shallow. A new feature should teach a real AI infrastructure concept at the right time.

## Contribution Principles

- Prefer readable code over clever abstractions.
- Keep dependencies minimal.
- Explain why each component exists.
- Make commands copy-paste friendly.
- Do not add Kubernetes, GPU, or MLOps complexity to the Day 1 path.
- Include tests for behavior that can break.

## Good First Contributions

- Add a realistic sample incident.
- Improve rule-based analysis for a specific log pattern.
- Add a small metrics example.
- Tighten docs where a beginner AI infra concept is unclear.
- Improve Docker Compose local workflow.

## Local Checks

```bash
cp .env.example .env
make up
make test
make generate-traffic
make analyze-logs
make down
```

Run formatting and lint checks before opening a pull request:

```bash
make format
make validate
```

`make validate` builds both images, runs both test suites, runs lint checks, and executes the assistant evaluation corpus. The same evaluation gate runs in CI.

## Pull Request Notes

In your PR, include:

- What changed.
- Why it belongs in the learning path.
- How you tested it.
- Any tradeoffs or follow-up work.

