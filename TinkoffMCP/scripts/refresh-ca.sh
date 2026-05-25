#!/usr/bin/env bash
# Re-download Russian Trusted Root + Sub CA from gu-st.ru and rebuild certs/russian_trusted_ca.pem
# Requires: curl, openssl, python3 (only for the final sanity-check).

set -euo pipefail

ROOT_URL="https://gu-st.ru/content/Other/doc/russian_trusted_root_ca.cer"
SUB_URL="https://gu-st.ru/content/Other/doc/russian_trusted_sub_ca.cer"

# Resolve repo root from this script's location.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEST="$REPO_ROOT/certs/russian_trusted_ca.pem"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

# Known-good SHA-256 fingerprints of the public Minсifry CAs. If you legitimately
# need to refresh after a CA rotation, update these constants in the same commit
# as the new bundle — never silently.
EXPECTED_ROOT_FP="D26D2D0231B7C39F92CC738512BA54103519E4405D68B5BD703E9788CA8ECF31"
EXPECTED_SUB_FP="BBBDE2103E790B999EC62BD03CF625A5A2E7C316E10AFE6A490EEDEAD8B3FD9B"

echo "→ downloading root CA"
curl -sLfo "$TMP_DIR/root.der" "$ROOT_URL"
echo "→ downloading sub CA"
curl -sLfo "$TMP_DIR/sub.der" "$SUB_URL"

echo "→ normalising to PEM (gu-st.ru sometimes serves PEM even when the file is named .cer)"
to_pem() {
  local src="$1" dst="$2"
  if head -c 27 "$src" | grep -q "BEGIN CERTIFICATE"; then
    cp "$src" "$dst"
  else
    openssl x509 -inform DER -in "$src" -out "$dst"
  fi
}
to_pem "$TMP_DIR/root.der" "$TMP_DIR/root.pem"
to_pem "$TMP_DIR/sub.der"  "$TMP_DIR/sub.pem"

echo "→ verifying fingerprints"
verify_fp() {
  local name="$1" want="$2" pem="$3"
  local got
  got=$(openssl x509 -in "$pem" -noout -fingerprint -sha256 | tr -d ':' | cut -d= -f2)
  if [ "$got" != "$want" ]; then
    echo "✗ ${name} CA fingerprint mismatch:" >&2
    echo "    got:  $got" >&2
    echo "    want: $want" >&2
    echo "  refusing to replace bundle — investigate before proceeding." >&2
    exit 1
  fi
  echo "  ${name}: $got ✓"
}
verify_fp "root" "$EXPECTED_ROOT_FP" "$TMP_DIR/root.pem"
verify_fp "sub"  "$EXPECTED_SUB_FP"  "$TMP_DIR/sub.pem"

mkdir -p "$REPO_ROOT/certs"
{ cat "$TMP_DIR/root.pem"; echo; cat "$TMP_DIR/sub.pem"; } > "$DEST"

echo "→ verifying bundle parses"
python3 - <<PY
import ssl, sys
stats = ssl.create_default_context(cafile="$DEST").cert_store_stats()
print("cert_store_stats:", stats)
assert stats["x509"] == 2, "expected 2 certs in bundle"
PY

echo "✓ wrote $DEST"
