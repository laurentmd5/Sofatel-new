import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
py_files = list(ROOT.rglob('*.py'))
# pattern: left = db.session.get(...)
pattern = re.compile(r"(\b[A-Za-z_][A-Za-z0-9_]*)\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*db\.session\.get\(")

for p in py_files:
    s = p.read_text(encoding='utf-8')
    new_s, n = pattern.subn(lambda m: f"{m.group(1)} = db.session.get(", s)
    if n:
        p.write_text(new_s, encoding='utf-8')
        print(f"Fixed duplicates in {p}: {n} replacements")

print('Done')
