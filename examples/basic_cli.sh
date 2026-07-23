#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FIXTURE="tests/fixtures/controlboard.log"

if command -v ontolog >/dev/null 2>&1; then
  ONTOLOG=(ontolog)
elif [[ -x "$ROOT/.venv/bin/ontolog" ]]; then
  ONTOLOG=("$ROOT/.venv/bin/ontolog")
elif [[ -x "$ROOT/.venv/bin/python" ]]; then
  ONTOLOG=("$ROOT/.venv/bin/python" -m ontolog.cli.main)
else
  ONTOLOG=(python -m ontolog.cli.main)
fi

echo "==> Exporting domain model as Mermaid ER diagram"
"${ONTOLOG[@]}" infer "$FIXTURE" --format mermaid

echo ""
echo "==> Exporting domain model as JSON Schema"
"${ONTOLOG[@]}" infer "$FIXTURE" --format json-schema

echo ""
echo "==> Done. See docs/export.md for more examples."
