#!/usr/bin/env python3
"""Update and sort the creators list of the zenodo record."""
import sys
import shutil
from pathlib import Path
import json
from fuzzywuzzy import fuzz, process
import subprocess as sp

CREATORS_LAST_ORCID = '0000-0002-5312-6729'  # This ORCID should go last
# for entries not found in line-contributions
MISSING_ENTRIES = [
    {"name": "Varada, Jan"},
    {"name": "Schwabacher, Isaac"},
    {"affiliation": "Child Mind Institute / Nathan Kline Institute",
     "name": "Pellman, John",
     "orcid": "0000-0001-6810-4461"},
    {"name": "Perez-Guevara, Martin"},
    {"name": "Khanuja, Ranjeet"},
    {"affiliation":
        "Medical Imaging & Biomarkers, Bioclinica, Newark, CA, USA.",
     "name": "Pannetier, Nicolas",
     "orcid": "0000-0002-0744-5155"},
    {"name": "McDermottroe, Conor"},
    {"affiliation":
        "Max Planck Institute for Human Cognitive and Brain Sciences, "
        "Leipzig, Germany.",
     "name": "Mihai, Paul Glad",
     "orcid": "0000-0001-5715-6442"},
    {"name": "Lai, Jeff"}
]


def fix_position(creators):
    """Place Satra last."""
    # position first / last authors
    l_authr = None

    for info in creators:
        if 'orcid' in info and info['orcid'] == CREATORS_LAST_ORCID:
            l_authr = info

    if l_authr is None:
        raise AttributeError('Missing important people')

    creators.remove(l_authr)
    creators.append(l_authr)
    return creators


if __name__ == '__main__':
    contrib_file = Path('line-contributors.txt')
    lines = []
    if contrib_file.exists():
        print('WARNING: Reusing existing line-contributors.txt file.', file=sys.stderr)
        lines = contrib_file.read_text().splitlines()

    if not lines and shutil.which('git-line-summary'):
        print("Running git-line-summary on nipype repo")
        lines = sp.check_output(['git-line-summary']).decode().splitlines()
        contrib_file.write_text('\n'.join(lines))

    if not lines:
        raise RuntimeError('Could not find line-contributors from git repository '
                           '(hint: please install git-extras).')

    data = [' '.join(line.strip().split()[1:-1]) for line in lines if '%' in line]

    # load zenodo from master
    zenodo_file = Path('.zenodo.json')
    zenodo = json.loads(zenodo_file.read_text())
    zen_names = [' '.join(val['name'].split(',')[::-1]).strip()
                 for val in zenodo['creators']]

    name_matches = []
    for ele in data:
        matches = process.extract(ele, zen_names, scorer=fuzz.token_sort_ratio,
                                  limit=2)
        # matches is a list [('First match', % Match), ('Second match', % Match)]
        if matches[0][1] > 80:
            val = zenodo['creators'][zen_names.index(matches[0][0])]
        else:
            # skip unmatched names
            print("No entry to sort:", ele)
            continue

        if val not in name_matches:
            name_matches.append(val)

    for entry in MISSING_ENTRIES:
        name_matches.append(entry)

    zenodo['creators'] = fix_position(name_matches)
    zenodo_file.write_text(json.dumps(zenodo, indent=2, sort_keys=True))
