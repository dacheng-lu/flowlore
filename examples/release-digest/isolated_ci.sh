#!/bin/sh
# Execute only after the host creates a network namespace. Never grant privileges here.
set -eu
mx=$1
lh=$2
out=$3
python3 - <<'PY' > "$out/network-check.txt"
import errno,socket
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.settimeout(2)
try:
    result=s.connect_ex(('192.0.2.1',443))
finally:
    s.close()
if result != errno.ENETUNREACH:
    raise SystemExit(f'network isolation probe refused: connect_ex={result}')
print('PASS: IPv4 network unreachable in isolated namespace')
PY
{
  printf 'FlowLore: '; git rev-parse HEAD
  printf 'Makeextreme: '; git -C "$mx" rev-parse HEAD
  printf 'Longhaul: '; git -C "$lh" rev-parse HEAD
  python3 --version
} > "$out/versions.txt"
python3 examples/release-digest/test_snapshot.py > "$out/tests.txt" 2>&1
python3 examples/release-digest/reproduce_snapshot.py --makeextreme "$mx" --longhaul "$lh" > "$out/replay.txt" 2>&1
python3 scripts/validate_recipes.py > "$out/contracts.txt" 2>&1
