#!/usr/bin/env python3
"""Inspect Shapr3D packages and STEP exports for CAD reverse engineering.

The script is intentionally conservative:
- .shapr files are treated as zip archives; if they contain a SQLite workspace,
  the script reports tables, sketch controllers, imported-body counts, and
  metadata without trying to decode proprietary Shapr internals.
- STEP/STP files are scanned for human-readable PRODUCT and
  MANIFOLD_SOLID_BREP labels.
- If CadQuery is importable, STEP bounding boxes and solid counts are measured.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import tempfile
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable


PRODUCT_RE = re.compile(r"PRODUCT\('([^']*)'")
BREP_RE = re.compile(r"MANIFOLD_SOLID_BREP\('([^']*)'")
SURFACE_PATTERNS = {
    "cylindrical": "CYLINDRICAL_SURFACE",
    "conical": "CONICAL_SURFACE",
    "plane": "PLANE",
    "bspline": "B_SPLINE_SURFACE_WITH_KNOTS",
    "torus": "TOROIDAL_SURFACE",
}


@dataclass
class StepInfo:
    path: str
    products: list[str]
    brep_labels: list[str]
    surface_counts: dict[str, int]
    solids: int | None = None
    bbox_mm: list[float] | None = None
    error: str | None = None


def unique_in_order(values: Iterable[str], limit: int | None = None) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        cleaned = value.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        out.append(cleaned)
        if limit is not None and len(out) >= limit:
            break
    return out


def iter_step_files(paths: Iterable[Path]) -> list[Path]:
    out: list[Path] = []
    for path in paths:
        if path.is_dir():
            for pattern in ("*.step", "*.stp", "*.STEP", "*.STP", "*.step.step"):
                out.extend(path.rglob(pattern))
        elif path.is_file():
            out.append(path)
    return sorted(set(out))


def inspect_step(path: Path, label_limit: int | None = 60, use_cadquery: bool = True) -> StepInfo:
    text = path.read_text(errors="ignore")
    info = StepInfo(
        path=str(path),
        products=unique_in_order(PRODUCT_RE.findall(text), label_limit),
        brep_labels=unique_in_order(BREP_RE.findall(text), label_limit),
        surface_counts={name: text.count(pattern) for name, pattern in SURFACE_PATTERNS.items()},
    )
    if not use_cadquery:
        return info
    try:
        import cadquery as cq  # type: ignore

        shape = cq.importers.importStep(str(path))
        solids = shape.solids().vals()
        bb = shape.val().BoundingBox()
        info.solids = len(solids)
        info.bbox_mm = [round(bb.xlen, 6), round(bb.ylen, 6), round(bb.zlen, 6)]
    except Exception as exc:  # pragma: no cover - depends on optional CAD stack
        info.error = f"{type(exc).__name__}: {exc}"
    return info


def sqlite_counts(db_path: Path, tables: Iterable[str]) -> dict[str, int | str]:
    conn = sqlite3.connect(str(db_path))
    try:
        out: dict[str, int | str] = {}
        for table in tables:
            try:
                out[table] = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            except sqlite3.DatabaseError as exc:
                out[table] = f"{type(exc).__name__}: {exc}"
        return out
    finally:
        conn.close()


def inspect_shapr(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"path": str(path), "is_zip": zipfile.is_zipfile(path)}
    if not result["is_zip"]:
        return result

    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        result["entries"] = [{"name": name, "size": archive.getinfo(name).file_size} for name in names]
        for metadata_name in (".metadata", "metadata", "Metadata"):
            if metadata_name in names:
                try:
                    result["metadata"] = json.loads(archive.read(metadata_name).decode("utf-8"))
                except Exception as exc:
                    result["metadata_error"] = f"{type(exc).__name__}: {exc}"
                break
        if "workspace" not in names:
            return result
        with tempfile.TemporaryDirectory(prefix="shapr-inspect-") as tmp:
            workspace = Path(tmp) / "workspace"
            workspace.write_bytes(archive.read("workspace"))
            header = workspace.read_bytes()[:32]
            result["workspace_header"] = header.decode("latin1", errors="replace").strip("\x00")
            if not header.startswith(b"SQLite format 3"):
                return result

            conn = sqlite3.connect(str(workspace))
            try:
                tables = [
                    row[0]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                    )
                ]
                result["tables"] = tables
            finally:
                conn.close()

            interesting = [
                "Shapes",
                "SketchControllers",
                "HistoryImportedBodies",
                "HistoryTreeNodes",
                "HistoryNames",
                "Images",
                "Drawings",
            ]
            result["counts"] = sqlite_counts(workspace, interesting)

            conn = sqlite3.connect(str(workspace))
            try:
                try:
                    rows = conn.execute(
                        "SELECT name, hidden, origin_x, origin_y, origin_z, normal_x, normal_y, normal_z "
                        "FROM SketchControllers ORDER BY name"
                    ).fetchall()
                    result["sketches"] = [
                        {
                            "name": row[0],
                            "hidden": row[1],
                            "origin": [row[2], row[3], row[4]],
                            "normal": [row[5], row[6], row[7]],
                        }
                        for row in rows
                    ]
                except sqlite3.DatabaseError as exc:
                    result["sketch_error"] = f"{type(exc).__name__}: {exc}"
            finally:
                conn.close()

    return result


def render_markdown(data: dict[str, Any]) -> str:
    lines: list[str] = ["# CAD Source Inspection", ""]
    for shapr in data.get("shapr", []):
        lines.append(f"## Shapr: `{shapr['path']}`")
        lines.append("")
        lines.append(f"- Zip package: `{shapr.get('is_zip')}`")
        if "metadata" in shapr:
            lines.append(f"- Metadata: `{json.dumps(shapr['metadata'], ensure_ascii=False)}`")
        if "workspace_header" in shapr:
            lines.append(f"- Workspace header: `{shapr['workspace_header']}`")
        if "counts" in shapr:
            lines.append("- Key table counts:")
            for key, value in shapr["counts"].items():
                lines.append(f"  - `{key}`: `{value}`")
        if "sketches" in shapr:
            lines.append("- Sketch controllers:")
            for sketch in shapr["sketches"]:
                lines.append(
                    f"  - `{sketch['name']}` hidden=`{sketch['hidden']}` "
                    f"origin=`{sketch['origin']}` normal=`{sketch['normal']}`"
                )
        lines.append("")
    for step in data.get("step", []):
        lines.append(f"## STEP: `{step['path']}`")
        lines.append("")
        if step.get("solids") is not None:
            lines.append(f"- Solids: `{step['solids']}`")
        if step.get("bbox_mm") is not None:
            lines.append(f"- Bounding box mm: `{step['bbox_mm']}`")
        if step.get("error"):
            lines.append(f"- CAD import error: `{step['error']}`")
        lines.append(f"- Products: {', '.join(f'`{p}`' for p in step.get('products', [])) or 'none'}")
        lines.append(f"- B-rep labels: {', '.join(f'`{p}`' for p in step.get('brep_labels', [])) or 'none'}")
        lines.append(
            "- Surface counts: "
            + ", ".join(f"`{k}`={v}" for k, v in step.get("surface_counts", {}).items())
        )
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shapr", action="append", type=Path, default=[], help="Shapr3D .shapr file")
    parser.add_argument("--step", action="append", type=Path, default=[], help="STEP/STP file or folder")
    parser.add_argument("--no-cadquery", action="store_true", help="Skip optional CadQuery import and bbox measurement")
    parser.add_argument("--limit-labels", type=int, default=60, help="Max PRODUCT/BREP labels per STEP file")
    parser.add_argument("--markdown", action="store_true", help="Print Markdown instead of JSON")
    args = parser.parse_args(argv)

    data: dict[str, Any] = {
        "shapr": [inspect_shapr(path) for path in args.shapr],
        "step": [
            asdict(inspect_step(path, args.limit_labels, not args.no_cadquery))
            for path in iter_step_files(args.step)
        ],
    }

    if args.markdown:
        print(render_markdown(data))
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
