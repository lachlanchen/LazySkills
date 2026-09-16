#!/usr/bin/env python3
"""Decode a Shapr3D .shapr archive directly: names, folders, sketches, operations, bodies.

A .shapr file is a zip whose ``workspace`` member is a SQLite database. Without any
proprietary tool this script recovers:

- settings: schema/project version, Parasolid version, create/save dates;
- folders and body display names (HistoryFolders + Metadata type 0);
- sketch planes (SketchControllers) and every sketch curve as JSON, converted to mm:
  type 0 line, 1 arc (center/start/end), 2 circle, 3 B-spline control points,
  4 interpolating spline, 5 ellipse;
- the ordered operation history (HistoryTreeNodes, msgpack) with typed parameters:
  lengths in mm, angles in degrees, enums, booleans, vectors, and references to
  HistoryNames (best-effort resolved to sketch curves);
- imported bodies (Parasolid transmit blobs) with their 4x4 placement transforms;
- body revision partitions (current Parasolid state after edits).

Solid geometry itself stays inside Parasolid blobs that OCCT cannot read. Use this
decoder to learn intent, dimensions, and structure; use a STEP export for exact B-rep.

Usage:
  python shapr_native_decoder.py design.shapr --markdown
  python shapr_native_decoder.py design.shapr --json --out report.json
  python shapr_native_decoder.py design.shapr --sketch-limit 400 --markdown --out report.md
"""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

try:
    import msgpack  # type: ignore
except Exception:  # pragma: no cover
    msgpack = None

MM = 1000.0

# typed-value tags observed in HistoryTreeNodes child payloads
TAG_NULL, TAG_BOOL, TAG_ENUM, TAG_STRUCT, TAG_VEC3, TAG_FRAME = 0, 1, 2, 4, 5, 6
TAG_NAME, TAG_LIST, TAG_SKETCH, TAG_BODY, TAG_QUANTITY = 7, 9, 10, 11, 12
UNIT_KIND = {0: "scalar", 1: "length_mm", 2: "angle_deg"}


# ----------------------------------------------------------------------------- helpers

def text_or_json(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    s = value if isinstance(value, str) else bytes(value).decode("utf-8", "replace")
    stripped = s.strip("\x00")
    if stripped[:1] in "{[":
        end = max(stripped.rfind("}"), stripped.rfind("]"))
        try:
            return json.loads(stripped[: end + 1])
        except Exception:
            return stripped
    return stripped


def unpack(blob: Any) -> Any:
    if msgpack is None or blob is None:
        return None
    try:
        return msgpack.unpackb(bytes(blob), raw=False, strict_map_key=False)
    except Exception:
        return None


def has_table(conn: sqlite3.Connection, name: str) -> bool:
    return conn.execute("select 1 from sqlite_master where type='table' and name=?", (name,)).fetchone() is not None


def rows(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[tuple]:
    try:
        return conn.execute(sql, params).fetchall()
    except sqlite3.DatabaseError:
        return []


# ----------------------------------------------------------------------------- decoder

class ShaprDecoder:
    def __init__(self, source: Path):
        self.source = source
        self.tmp = tempfile.TemporaryDirectory(prefix="shapr-native-")
        ws = Path(self.tmp.name) / "workspace"
        with zipfile.ZipFile(source) as archive:
            ws.write_bytes(archive.read("workspace"))
            self.metadata = None
            if ".metadata" in archive.namelist():
                try:
                    self.metadata = json.loads(archive.read(".metadata").decode("utf-8"))
                except Exception:
                    self.metadata = None
        self.conn = sqlite3.connect(str(ws))
        self.names: dict[int, tuple[int, Any]] = {}
        for nid, typ, data in rows(self.conn, "select NameID, Type, Data from HistoryNames"):
            self.names[int(nid)] = (int(typ), text_or_json(data))
        self.curve_index: dict[int, dict[str, Any]] = {}

    # --- settings / metadata
    def settings(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for name, value in rows(self.conn, "select SettingName, SettingValue from Settings"):
            key = text_or_json(name)
            val = text_or_json(value)
            if isinstance(key, str) and key.startswith(("Persistence_", "Create_", "Latest_", "SchemaVersion")):
                out[key] = val
        return out

    def body_names(self) -> dict[int, str]:
        """Map any body element/metadata id to its display name.

        Folder elements of type 6 point at a Metadata row (often type 3, empty). The
        display name lives in a sibling type-0 row assigned to the same HistoryName, so
        join through MetadataAssignments; fall back to the immediately preceding id.
        """
        typed: dict[int, tuple[int, str]] = {}
        for mid, typ, data in rows(self.conn, "select MetadataID, MetadataTypeID, Data from Metadata"):
            typed[int(mid)] = (int(typ), str(text_or_json(data)))
        by_name: dict[int, list[int]] = {}
        meta_to_name: dict[int, int] = {}
        for nid, mid in rows(self.conn, "select NameID, MetadataID from MetadataAssignments"):
            by_name.setdefault(int(nid), []).append(int(mid))
            meta_to_name[int(mid)] = int(nid)
        names: dict[int, str] = {}
        for mid, (typ, text) in typed.items():
            if typ == 0:
                names[mid] = text
                continue
            nid = meta_to_name.get(mid)
            label = None
            if nid is not None:
                for sib in by_name.get(nid, []):
                    if typed.get(sib, (None, None))[0] == 0:
                        label = typed[sib][1]
                        break
            if label is None and typed.get(mid - 1, (None, None))[0] == 0:
                label = typed[mid - 1][1]
            if label is not None:
                names[mid] = label
        return names

    def folders(self) -> list[dict[str, Any]]:
        body_names = self.body_names()
        out = []
        for rid, fid, fname, hidden, children in rows(
            self.conn, "select RowID, FolderID, FolderName, Hidden, NamedChildren from HistoryFolders order by RowID"
        ):
            kids = text_or_json(children) or {}
            elements = kids.get("elements", []) if isinstance(kids, dict) else []
            bodies = [body_names.get(int(e["id"]), f"body#{e['id']}") for e in elements if str(e.get("id", "")).isdigit() and e.get("type") == 6]
            subfolders = [e["id"] for e in elements if e.get("type") == 0]
            sketches = [e["id"] for e in elements if e.get("type") == 2]
            out.append(
                {
                    "row": rid,
                    "folder_id": text_or_json(fid),
                    "name": text_or_json(fname),
                    "hidden": bool(hidden),
                    "bodies": bodies,
                    "subfolder_ids": subfolders,
                    "sketch_ids": sketches,
                }
            )
        return out

    # --- sketches
    def sketches(self, curve_limit: int) -> list[dict[str, Any]]:
        planes: dict[int, dict[str, Any]] = {}
        for r in rows(
            self.conn,
            "select SketchID, Name, IsHidden, PlaneCenterX, PlaneCenterY, PlaneCenterZ, "
            "PlaneNormX, PlaneNormY, PlaneNormZ, PlaneUDirX, PlaneUDirY, PlaneUDirZ from SketchControllers",
        ):
            sid = int(r[0])
            planes[sid] = {
                "sketch_id": sid,
                "name": text_or_json(r[1]),
                "hidden": bool(r[2]),
                "origin_mm": [round(v * MM, 6) for v in r[3:6]],
                "normal": [round(v, 9) for v in r[6:9]],
                "u_dir": [round(v, 9) for v in r[9:12]],
                "curves": [],
                "curve_type_counts": {},
            }
        for cid, sid, data in rows(self.conn, "select CurveID, SketchID, Data from SketchCurves order by CurveID"):
            j = text_or_json(data)
            if not isinstance(j, dict):
                continue
            curve = self.curve_mm(int(cid), j)
            self.curve_index[int(cid)] = curve
            sk = planes.setdefault(int(sid), {"sketch_id": int(sid), "name": None, "curves": [], "curve_type_counts": {}})
            sk["curve_type_counts"][curve["kind"]] = sk["curve_type_counts"].get(curve["kind"], 0) + 1
            if len(sk["curves"]) < curve_limit:
                sk["curves"].append(curve)
        return [planes[k] for k in sorted(planes)]

    @staticmethod
    def pt(p: dict[str, Any]) -> list[float]:
        return [round(p.get("x", 0.0) * MM, 6), round(p.get("y", 0.0) * MM, 6)]

    def curve_mm(self, cid: int, j: dict[str, Any]) -> dict[str, Any]:
        t = j.get("type")
        c: dict[str, Any] = {"curve_id": cid, "type": t}
        if t == 0:
            c.update(kind="line", start=self.pt(j["start"]), end=self.pt(j["end"]))
            c["length_mm"] = round(math.dist(c["start"], c["end"]), 6)
        elif t == 1:
            c.update(kind="arc", center=self.pt(j["center"]), start=self.pt(j["start"]), end=self.pt(j["end"]))
            c["radius_mm"] = round(math.dist(c["center"], c["start"]), 6)
        elif t == 2:
            c.update(kind="circle", center=self.pt(j["center"]), radius_mm=round(j["radius"] * MM, 6))
            c["diameter_mm"] = round(j["radius"] * 2 * MM, 6)
        elif t == 3:
            c.update(kind="bspline", control_points=[self.pt(p) for p in j.get("controlPoints", [])], degree=j.get("degree"), knots=j.get("knots"))
        elif t == 4:
            c.update(kind="interpolating_spline", points=[self.pt(p) for p in j.get("interpolatingPoints", [])], parametrization=j.get("parametrization"))
        elif t == 5:
            c.update(kind="ellipse", center=self.pt(j["center"]), direction=[j["direction"].get("x"), j["direction"].get("y")], major_radius_mm=round(j["majorRadius"] * MM, 6), minor_radius_mm=round(j["minorRadius"] * MM, 6))
        else:
            c.update(kind=f"type{t}", raw=j)
        return c

    # --- names
    def resolve_name(self, nid: int, depth: int = 0, seen: set[int] | None = None) -> dict[str, Any]:
        seen = seen or set()
        if nid in seen or depth > 12 or nid not in self.names:
            return {"name_id": nid, "resolved": None}
        seen.add(nid)
        typ, data = self.names[nid]
        info: dict[str, Any] = {"name_id": nid, "name_type": typ}
        if isinstance(data, dict):
            if "curveID" in data:
                cid = int(data["curveID"])
                info["curve_id"] = cid
                if cid in self.curve_index:
                    info["curve"] = {k: v for k, v in self.curve_index[cid].items() if k in ("kind", "start", "end", "center", "radius_mm", "diameter_mm", "length_mm")}
                return info
            for key in ("nameToAnchor", "wrappedName", "filling"):
                if key in data and isinstance(data[key], int):
                    child = self.resolve_name(int(data[key]), depth + 1, seen)
                    if child.get("curve_id"):
                        info.update({k: child[k] for k in ("curve_id", "curve") if k in child})
                        return info
            for key in ("sourceTopologyNames", "originals", "neighborFaceOriginals0", "neighborFaceOriginals1"):
                for ref in data.get(key, []) or []:
                    if isinstance(ref, int):
                        child = self.resolve_name(ref, depth + 1, seen)
                        if child.get("curve_id"):
                            info.update({k: child[k] for k in ("curve_id", "curve") if k in child})
                            return info
            fin = data.get("fin") or {}
            for e in (fin.get("originalEdgesWithSense") or []) + [x for f in data.get("fins", []) or [] for x in f.get("originalEdgesWithSense", [])]:
                ref = e.get("originalEdgeOrCurve")
                if isinstance(ref, int):
                    child = self.resolve_name(ref, depth + 1, seen)
                    if child.get("curve_id"):
                        info.update({k: child[k] for k in ("curve_id", "curve") if k in child})
                        return info
            if "callKey" in data:
                info["created_by_node"] = data["callKey"].get("nodeID")
        return info

    # --- typed values
    def decode_value(self, v: Any, depth: int = 0) -> Any:
        if depth > 30:
            return v
        if isinstance(v, list) and len(v) == 1 and isinstance(v[0], list):
            return self.decode_value(v[0], depth + 1)
        if isinstance(v, list) and v and isinstance(v[0], int) and len(v) in (1, 2):
            tag = v[0]
            if tag == TAG_NULL and len(v) == 1:
                return None
            if len(v) == 2:
                payload = v[1]
                if tag == TAG_BOOL:
                    return bool(payload)
                if tag == TAG_ENUM:
                    return {"enum": payload}
                if tag == TAG_VEC3 and isinstance(payload, list):
                    return {"vec3": payload}
                if tag == TAG_FRAME and isinstance(payload, list):
                    return {"frame": {"origin_mm": [round(x * MM, 6) for x in payload[0]], "normal": payload[1], "u_dir": payload[2]}} if len(payload) >= 3 else {"frame": payload}
                if tag == TAG_NAME:
                    return {"ref": self.resolve_name(int(payload))}
                if tag == TAG_SKETCH:
                    return {"sketch_id": payload}
                if tag == TAG_BODY:
                    return {"imported_body_id": payload}
                if tag == TAG_LIST and isinstance(payload, list):
                    return [self.decode_value(x, depth + 1) for x in payload]
                if tag == TAG_QUANTITY and isinstance(payload, list) and len(payload) == 2:
                    unit = payload[0][0] if isinstance(payload[0], list) and payload[0] else None
                    val = payload[1]
                    if unit == 1:
                        return {"length_mm": round(val * MM, 6)}
                    if unit == 2:
                        return {"angle_deg": round(math.degrees(val), 6)}
                    return {"value": val}
                if tag == TAG_STRUCT and isinstance(payload, list):
                    out: dict[str, Any] = {}
                    for i in range(0, len(payload) - 1, 2):
                        key = payload[i]
                        out[str(key)] = self.decode_value(payload[i + 1], depth + 1)
                    return out
        if isinstance(v, list):
            return [self.decode_value(x, depth + 1) for x in v]
        return v

    # --- operations
    def operations(self) -> list[dict[str, Any]]:
        nodes: dict[int, tuple[int, Any]] = {}
        for nid, typ, props in rows(self.conn, "select HistoryTreeNodeID, HistoryTreeNodeType, Properties from HistoryTreeNodes"):
            nodes[int(nid)] = (int(typ), unpack(props))
        order: list[int] = []
        for nid, (typ, payload) in nodes.items():
            if typ == 0 and isinstance(payload, list) and payload and isinstance(payload[0], list):
                order = [int(x) for x in payload[0] if isinstance(x, int)]
                break
        op_ids = [n for n, (t, p) in nodes.items() if t == 2 and isinstance(p, list) and len(p) >= 3]
        if not order:
            order = sorted(op_ids)
        else:
            order = [n for n in order if n in nodes and nodes[n][0] == 2] + sorted(set(op_ids) - set(order))
        out = []
        for seq, nid in enumerate(order, 1):
            typ, payload = nodes[nid]
            title, op, kids = payload[-3], payload[-2], payload[-1]
            params = []
            for k in kids if isinstance(kids, list) else []:
                child = nodes.get(int(k)) if isinstance(k, int) else None
                params.append(self.decode_value(child[1]) if child else None)
            out.append({"seq": seq, "node_id": nid, "title": title, "operation": op, "params": params, "summary": self.summarize(op, params)})
        return out

    @staticmethod
    def q(p: Any, key: str) -> Any:
        return p.get(key) if isinstance(p, dict) else None

    def summarize(self, op: str, p: list[Any]) -> str:
        g = lambda i, k: self.q(p[i], k) if i < len(p) else None  # noqa: E731
        try:
            if op == "Extrude":
                mode = g(5, "enum")
                return f"distance {g(1,'length_mm')} mm, draft {g(2,'angle_deg')} deg, mode {mode}, second distance {g(11,'length_mm')} mm"
            if op == "Revolve":
                return f"angle {g(2,'angle_deg')} deg, offset {g(3,'length_mm')} mm, axis ref {json.dumps(g(1,'ref'))[:120]}"
            if op in ("Chamfer",):
                return f"distance {g(3,'length_mm')} mm, equal {p[5] if len(p)>5 else None}"
            if op == "Fillet":
                return f"radius {g(3,'length_mm')} mm"
            if op == "OffsetFace":
                return f"offset/new value {g(1,'length_mm')} mm, enums {g(2,'enum')}/{g(3,'enum')}"
            if op in ("Transform", "Rotate", "Scale", "Align", "Mirror"):
                return json.dumps(p[1:], default=str)[:300]
            if op == "CreateCGPlaneWithFaceOffset":
                return f"offsets {g(1,'length_mm')} / {g(2,'length_mm')} mm"
            if op == "CreateCGAxisWithRevolvedFace":
                return f"length {g(1,'length_mm')} mm"
            if op == "Boolean":
                return f"kind {g(2,'enum')}"
            if op == "LinearPattern":
                return json.dumps(p, default=str)[:300]
        except Exception:
            pass
        return ""

    # --- bodies
    def imported_bodies(self) -> list[dict[str, Any]]:
        out = []
        if has_table(self.conn, "HistoryImportedPrototypes"):
            sql = (
                "select b.ImportedBodyID, b.ImportedPrototypeID, b.Transform, length(p.BodyData), substr(p.BodyData,1,80) "
                "from HistoryImportedBodies b left join HistoryImportedPrototypes p on p.ImportedPrototypeID=b.ImportedPrototypeID"
            )
        else:
            sql = "select ImportedBodyID, ImportedBodyID, NULL, length(BodyData), substr(BodyData,1,80) from HistoryImportedBodies"
        for bid, pid, tf, size, head in rows(self.conn, sql):
            t = unpack(tf) if tf is not None else None
            head_txt = "".join(chr(b) if 32 <= b < 127 else "." for b in bytes(head or b""))
            entry: dict[str, Any] = {"body_id": bid, "prototype_id": pid, "bytes": size, "header": head_txt[:70]}
            if isinstance(t, list) and len(t) == 16:
                entry["translation_mm"] = [round(t[12] * MM, 6), round(t[13] * MM, 6), round(t[14] * MM, 6)]
                entry["identity_rotation"] = t[:3] == [1.0, 0.0, 0.0] and t[4:7] == [0.0, 1.0, 0.0] and t[8:11] == [0.0, 0.0, 1.0]
            out.append(entry)
        return out

    def revision_partitions(self) -> dict[str, Any]:
        if not has_table(self.conn, "BodyRevisionBlocks"):
            return {"present": False}
        n, total = rows(self.conn, "select count(*), coalesce(sum(length(Block)),0) from BodyRevisionBlocks")[0]
        return {"present": True, "blocks": n, "bytes": total, "format": "Parasolid transmit partitions (binary)"}

    def materials(self) -> list[dict[str, Any]]:
        out = []
        for iid, did, props in rows(self.conn, "select InstanceID, DefinitionID, Properties from MaterialInstances"):
            j = text_or_json(props)
            color = j.get("baseColor") if isinstance(j, dict) else None
            rgba = None
            if isinstance(color, int):
                rgba = [(color >> 24) & 255, (color >> 16) & 255, (color >> 8) & 255, color & 255]
            out.append({"instance": iid, "definition": did, "rgba": rgba, "transmission": j.get("transmission") if isinstance(j, dict) else None})
        return out

    def report(self, curve_limit: int) -> dict[str, Any]:
        sketches = self.sketches(curve_limit)  # populates curve_index before ops resolve refs
        ops = self.operations()
        return {
            "source": str(self.source),
            "package_metadata": self.metadata,
            "settings": self.settings(),
            "folders": self.folders(),
            "body_names": self.body_names(),
            "sketches": sketches,
            "operations": ops,
            "operation_counts": dict(Counter(o["operation"] for o in ops).most_common()),
            "imported_bodies": self.imported_bodies(),
            "revision_partitions": self.revision_partitions(),
            "materials": self.materials(),
        }


# ----------------------------------------------------------------------------- markdown

def fmt(v: Any) -> str:
    return json.dumps(v, default=str, ensure_ascii=False)


def to_markdown(r: dict[str, Any], curve_limit: int) -> str:
    L = [f"# Shapr3D native decode: `{Path(r['source']).name}`", ""]
    L.append(f"- Package metadata: `{fmt(r.get('package_metadata'))}`")
    for k, v in r["settings"].items():
        L.append(f"- {k}: `{v}`")
    L += ["", "## Folders and bodies", "", "| Folder | Hidden | Bodies |", "| --- | --- | --- |"]
    for f in r["folders"]:
        L.append(f"| `{f['name']}` | {f['hidden']} | {', '.join('`'+b+'`' for b in f['bodies']) or ''} |")
    L += ["", "## Sketches (mm, local plane coordinates)", ""]
    for s in r["sketches"]:
        L.append(f"### `{s.get('name')}` (id {s['sketch_id']}) origin {s.get('origin_mm')} normal {s.get('normal')} u {s.get('u_dir')}")
        L.append(f"- curve types: `{fmt(s['curve_type_counts'])}`")
        for c in s["curves"][:curve_limit]:
            body = {k: v for k, v in c.items() if k not in ("curve_id", "type", "kind", "knots")}
            L.append(f"  - #{c['curve_id']} {c['kind']}: {fmt(body)}")
        L.append("")
    L += ["## Operations (in history order)", "", "| # | Title | Operation | Summary |", "| ---: | --- | --- | --- |"]
    for o in r["operations"]:
        L.append(f"| {o['seq']} | `{o['title']}` | `{o['operation']}` | {o['summary'].replace('|','/')} |")
    L += ["", f"Operation counts: `{fmt(r['operation_counts'])}`", ""]
    L += ["## Imported bodies (Parasolid, opaque)", "", "| Body | Bytes | Translation mm | Header |", "| ---: | ---: | --- | --- |"]
    for b in r["imported_bodies"][:60]:
        L.append(f"| {b['body_id']} | {b['bytes']} | {b.get('translation_mm')} | `{b['header'][:40]}` |")
    if len(r["imported_bodies"]) > 60:
        L.append(f"| ... | {len(r['imported_bodies'])-60} more | | |")
    L += ["", f"Revision partitions: `{fmt(r['revision_partitions'])}`", "", f"Materials: `{fmt(r['materials'])}`", ""]
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("shapr", type=Path, nargs="+")
    ap.add_argument("--json", action="store_true", help="emit JSON (default is Markdown)")
    ap.add_argument("--markdown", action="store_true")
    ap.add_argument("--out", type=Path, help="write to this file instead of stdout (one input only)")
    ap.add_argument("--sketch-limit", type=int, default=120, help="max curves listed per sketch")
    args = ap.parse_args(argv)
    if msgpack is None:
        print("warning: msgpack not importable; operation history will be empty", file=sys.stderr)
    chunks = []
    for path in args.shapr:
        dec = ShaprDecoder(path)
        rep = dec.report(args.sketch_limit)
        chunks.append(json.dumps(rep, indent=2, ensure_ascii=False, default=str) if args.json else to_markdown(rep, args.sketch_limit))
    text = "\n\n".join(chunks) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
        print(args.out)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
