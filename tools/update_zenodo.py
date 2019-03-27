#!/usr/bin/env python3
import json
from fuzzywuzzy import fuzz, process
import shutil
import os
import subprocess as sp

if os.path.exists('line-contributions.txt'):
    with open('line-contributions.txt', 'rt') as fp:
        lines = fp.readlines()
else:
    if shutil.which('git-line-summary'):
        print("Running git-line-summary on nipype repo")
        lines = sp.check_output(['git-line-summary']).decode().split('\n')
    else:
        raise RuntimeError("Install Git Extras to view git contributors")

data = [' '.join(line.strip().split()[1:-1]) for line in lines if '%' in line]

# load zenodo from master
with open('.zenodo.json', 'rt') as fp:
    zenodo = json.load(fp)
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

# for entries not found in line-contributions
missing_entries = [
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
]

for entry in missing_entries:
    name_matches.append(entry)


def fix_position(creators):
    # position first / last authors
    f_authr = None
    l_authr = None

    for i, info in enumerate(creators):
        if info['name'] == 'Gorgolewski, Krzysztof J.':
            f_authr = i
        if info['name'] == 'Ghosh, Satrajit':
            l_authr = i

    if f_authr is None or l_authr is None:
        raise AttributeError('Missing important people')

    creators.insert(0, creators.pop(f_authr))
    creators.insert(len(creators), creators.pop(l_authr + 1))
    return creators


zenodo['creators'] = fix_position(name_matches)

with open('.zenodo.json', 'wt') as fp:
    json.dump(zenodo, fp, indent=2, sort_keys=True)
    fp.write('\n')
