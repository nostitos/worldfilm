# studio/env.sh — source this before working: `source studio/env.sh`
# Node 22 (HyperFrames needs >= 22; nvm's 22.x when present, else /opt/homebrew/bin), the Python venv, telemetry
# off, and the location of shotspec-film (required; see studio/kits/README.md).
STUDIO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")" && pwd)"
case ":$PATH:" in *":/opt/homebrew/bin:"*) ;; *) export PATH="/opt/homebrew/bin:$PATH" ;; esac
if [ -s "$HOME/.nvm/nvm.sh" ]; then
  . "$HOME/.nvm/nvm.sh" >/dev/null 2>&1
  nvm use 22 >/dev/null 2>&1 || true
fi
NODE_MAJ="$(node -v 2>/dev/null | sed 's/^v//' | cut -d. -f1)"
if [ -z "$NODE_MAJ" ] || [ "$NODE_MAJ" -lt 22 ]; then export PATH="/opt/homebrew/bin:$PATH"; fi
export HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_NO_UPDATE_CHECK=1
export WORLDFILM_HOME="$STUDIO_DIR/worldfilm"
if [ -z "${SHOTSPEC_HOME:-}" ]; then
  for c in "$STUDIO_DIR/kits/shotspec-film" "$HOME/.codex/skills/shotspec-film" "$HOME/.claude/skills/shotspec-film"; do
    if [ -f "$c/scripts/run_gates.py" ]; then export SHOTSPEC_HOME="$c"; break; fi
  done
fi
export WORLDFILM_PY="$STUDIO_DIR/.venv/bin/python"
if [ -f "$STUDIO_DIR/.venv/bin/activate" ]; then . "$STUDIO_DIR/.venv/bin/activate"; fi
echo "worldfilm studio: node $(node --version 2>/dev/null), python $(python3 --version 2>/dev/null | cut -d' ' -f2), shotspec-film at ${SHOTSPEC_HOME:-NOT FOUND}"

