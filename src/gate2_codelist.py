# The code-list step (PREREG 4.1 step 2, job C from the main session, Oct 18, 2026): prints the DISTINCT VALUES of the code
# columns of the two shed-permit files, and nothing else: no counts, no dates, no BINs, no row examples. Uses the frozen
# gate2_link.code_list on each raw page and takes the union. The main session chooses the shed strings from this list.
# Run: .venv/bin/python -I src/gate2_codelist.py [output_text_file]
import glob
import json
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gate2_link as L

ROOT = pathlib.Path(__file__).resolve().parent.parent


def union_values(dataset, key):
    acc = {}
    for f in sorted(glob.glob(str(ROOT / "data" / "raw" / f"{dataset}_*_page*.json"))):
        df = pd.DataFrame(json.load(open(f)))
        part = L.code_list(**{key: df}, max_values=10**9)
        for k, vals in part.items():
            acc.setdefault(k, set()).update(vals)
    return {k: sorted(v) for k, v in acc.items()}


def main():
    result = {}
    result.update(union_values("rbx6-tga4", "dobnow"))
    result.update(union_values("ipu4-2q9a", "legacy"))
    lines = ["Distinct values of the code columns (Oct 18, 2026 pulls; values only, no counts), one value per line, in brackets.", ""]
    for k, vals in result.items():
        lines.append(f"== {k} ==")
        lines += [f"[{v}]" for v in vals]
        lines.append("")
    text = "\n".join(lines)
    if len(sys.argv) > 1:
        pathlib.Path(sys.argv[1]).write_text(text)
    print(text)


if __name__ == "__main__":
    main()
