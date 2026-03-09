import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
py_files = list(ROOT.rglob('*.py'))
pattern = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\.query\.get_or_404\(([^)]+)\)")

for p in py_files:
    if 'venv' in str(p) or 'env' in str(p):
        continue
    s = p.read_text(encoding='utf-8')
    # replace occurrences
    def repl(m):
        var = m.group(1).lower()
        Model = m.group(1)
        arg = m.group(2)
        return f"{var} = db.session.get({Model}, {arg})\n    if not {var}:\n        abort(404)"

    new_s, n = pattern.subn(repl, s)
    if n:
        # ensure abort is imported from flask
        if 'from flask import' in new_s and 'abort' not in new_s.split('from flask import',1)[1]:
            new_s = new_s.replace('from flask import', 'from flask import abort,', 1)
        p.write_text(new_s, encoding='utf-8')
        print(f"Updated {p}: {n} replacements")

print('Done')
