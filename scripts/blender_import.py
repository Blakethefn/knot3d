"""Minimal Blender-side helper notes for exported meshes."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Describe how to import a generated mesh into Blender")
    parser.add_argument("mesh", help="Path to an OBJ, STL, or GLB file")
    args = parser.parse_args()
    path = Path(args.mesh)
    if not path.exists():
        raise SystemExit(f"Mesh not found: {path}")
    print(f"Open Blender and import: {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
