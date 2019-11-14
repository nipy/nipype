#!/usr/bin/env python3
"""Update and sort the creators list of the zenodo record."""
import sys
import shutil
from pathlib import Path
import json
from fuzzywuzzy import fuzz, process
import subprocess as sp

# These names should go last
CREATORS_LAST = ["Gorgolewski, Krzysztof J.", "Ghosh, Satrajit"]

if __name__ == "__main__":
    contrib_file = Path("line-contributors.txt")
    lines = []
    if contrib_file.exists():
        print("WARNING: Reusing existing line-contributors.txt file.", file=sys.stderr)
        lines = contrib_file.read_text().splitlines()

    git_line_summary_path = shutil.which("git-line-summary")
    if not lines and git_line_summary_path:
        print("Running git-line-summary on nipype repo")
        lines = sp.check_output([git_line_summary_path]).decode().splitlines()
        contrib_file.write_text("\n".join(lines))

    if not lines:
        raise RuntimeError(
            """\
Could not find line-contributors from git repository.%s"""
            % """ \
git-line-summary not found, please install git-extras. """
            * (git_line_summary_path is None)
        )

    data = [" ".join(line.strip().split()[1:-1]) for line in lines if "%" in line]

    # load zenodo from master
    zenodo_file = Path(".zenodo.json")
    zenodo = json.loads(zenodo_file.read_text())
    zen_names = [
        " ".join(val["name"].split(",")[::-1]).strip() for val in zenodo["creators"]
    ]
    total_names = len(zen_names)

    name_matches = []
    position = 1
    for ele in data:
        matches = process.extract(ele, zen_names, scorer=fuzz.token_sort_ratio, limit=2)
        # matches is a list [('First match', % Match), ('Second match', % Match)]
        if matches[0][1] <= 80:
            # skip unmatched names
            print("No entry to sort:", ele)
            continue

        idx = zen_names.index(matches[0][0])
        val = zenodo["creators"][idx]

        if val not in name_matches:
            if val["name"] not in CREATORS_LAST:
                val["position"] = position
                position += 1
            else:
                val["position"] = total_names + CREATORS_LAST.index(val["name"])
            name_matches.append(val)

    for missing in zenodo["creators"]:
        if "position" not in missing:
            missing["position"] = position
            position += 1
            name_matches.append(missing)

    zenodo["creators"] = sorted(name_matches, key=lambda k: k["position"])
    # Remove position
    for creator in zenodo["creators"]:
        del creator["position"]

    zenodo_file.write_text("%s\n" % json.dumps(zenodo, indent=2, sort_keys=True))
