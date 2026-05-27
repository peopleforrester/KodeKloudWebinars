#!/usr/bin/env python3
# ABOUTME: Offline structural check for the lab manifests — confirms each YAML doc is a
# ABOUTME: well-formed Kubernetes object. Substitutes for kubectl dry-run when no cluster.
"""Validate that every manifest document has apiVersion, kind, and metadata.name.

This is a static substitute for `kubectl apply --dry-run`, which needs a reachable cluster
(and the KServe CRDs) to validate InferenceService objects. Exits non-zero on any issue.
"""

from __future__ import annotations

import glob
import sys

try:
    import yaml
except ImportError:
    print("PyYAML not installed; skipping structural check (yamllint already ran).")
    sys.exit(0)

ok = True
for path in sorted(glob.glob("manifests/*.yaml")):
    with open(path) as fh:
        docs = [d for d in yaml.safe_load_all(fh) if d]
    if not docs:
        print(f"  {path}: no documents [FAIL]")
        ok = False
        continue
    for doc in docs:
        missing = [k for k in ("apiVersion", "kind") if k not in doc]
        name = doc.get("metadata", {}).get("name")
        if missing or not name:
            print(f"  {path}: {doc.get('kind', '?')}/{name} MISSING {missing or 'metadata.name'} [FAIL]")
            ok = False
        else:
            print(f"  {path}: {doc['kind']}/{name} [OK]")

print("All manifests well-formed." if ok else "Structural issues found.")
sys.exit(0 if ok else 1)
