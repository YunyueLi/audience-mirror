# Contributing

The project is in an experimental baseline phase. Contributions should keep the
repository reproducible, inspectable and safe for public review.

## Before a change

1. Read `AGENTS.md`, `PRODUCT.md`, `README.md` and `docs/05-evidence-register.md`.
2. Use only synthetic fixtures or explicitly authorized public material.
3. Keep vendor, model and dataset adapters optional and versioned.
4. Preserve backward compatibility for public Schemas, or raise the major version.

## Verification

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m audience_mirror demo
PYTHONPATH=src python3 -m audience_mirror validate traces artifacts/public-demo/deep-traces.json \
  --timeline artifacts/public-demo/timeline.json
```

Do not present synthetic run counts as human sample sizes or add uncalibrated
market forecasts to reports.
