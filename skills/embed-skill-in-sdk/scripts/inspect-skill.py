#!/usr/bin/env python3
"""Walk a skill directory, emit a JSON manifest of what's in it.

Usage:
    python3 inspect-skill.py path/to/skill-dir

Output: JSON to stdout with keys:
    name, description, frontmatter (full dict), skill_md_path,
    references (list of relative paths), scripts, assets, total_bytes
"""
import json, sys, pathlib

def parse_frontmatter(md: str) -> dict:
    if not md.startswith("---\n"):
        return {}
    end = md.find("\n---\n", 4)
    if end == -1:
        return {}
    fm = {}
    for line in md[4:end].splitlines():
        if ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm

def list_bundled(skill_dir: pathlib.Path, name: str) -> list[str]:
    sub = skill_dir / name
    if not sub.exists():
        return []
    return [str(p.relative_to(skill_dir)) for p in sorted(sub.rglob("*")) if p.is_file()]

def main():
    if len(sys.argv) != 2:
        print("usage: inspect-skill.py <skill-dir>", file=sys.stderr)
        sys.exit(2)
    skill_dir = pathlib.Path(sys.argv[1])
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        print(json.dumps({"error": "no SKILL.md", "dir": str(skill_dir)}))
        sys.exit(1)
    body = skill_md.read_text(encoding="utf-8")
    fm = parse_frontmatter(body)
    manifest = {
        "name": fm.get("name"),
        "description": fm.get("description"),
        "frontmatter": fm,
        "skill_md_path": str(skill_md),
        "references": list_bundled(skill_dir, "references"),
        "scripts": list_bundled(skill_dir, "scripts"),
        "assets": list_bundled(skill_dir, "assets"),
        "total_bytes": sum(p.stat().st_size for p in skill_dir.rglob("*") if p.is_file()),
    }
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
