#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FIXTURE="tests/fixtures/controlboard.log"
STORE="example_cli.db"

if command -v ontolog >/dev/null 2>&1; then
  ONTOLOG=(ontolog)
elif [[ -x "$ROOT/.venv/bin/ontolog" ]]; then
  ONTOLOG=("$ROOT/.venv/bin/ontolog")
elif [[ -x "$ROOT/.venv/bin/python" ]]; then
  ONTOLOG=("$ROOT/.venv/bin/python" -m ontolog.cli.main)
else
  ONTOLOG=(python -m ontolog.cli.main)
fi

echo "==> Inferring domain model from $FIXTURE"
"${ONTOLOG[@]}" infer "$FIXTURE" --store "$STORE"

echo ""
echo "==> Exporting as Mermaid ER diagram"
"${ONTOLOG[@]}" export mermaid --store "$STORE"

echo ""
echo "==> Exporting as JSON Schema"
"${ONTOLOG[@]}" export json-schema --store "$STORE"

rm -f "$STORE"
echo ""
echo "==> Done. See docs/cli.md for more examples."
