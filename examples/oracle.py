import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    rows = json.load(f)
sys.exit(7 if any(row.get("bug") == "yes" for row in rows) else 0)
