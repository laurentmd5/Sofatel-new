import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
py_files = list(ROOT.rglob('*.py'))
pattern = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\.query\.get\(([^)]+)\)")

for p in py_files:
    if 'venv' in str(p) or 'env' in str(p):
        continue
    s = p.read_text(encoding='utf-8')
    new_s, n = pattern.subn(r"db.session.get(\1, \2)", s)
    if n:
        p.write_text(new_s, encoding='utf-8')
        print(f"Updated {p}: {n} replacements")

print('Done')
