import os
import collections
import requests
import nibabel as nb
from json import dumps

from .filemanip import split_filename

def submit_telemetry(payload):
    headers = {'Authorization': '<secret_token>', "Content-Type": "application/json"}
    webapi_url = "http://127.0.0.1/api/v1/nipype_telemetry"

    response = requests.post(webapi_url, headers=headers, data=dumps(payload))


def prepare_execution_stats(interface_results):
    payload = {}
    payload['interface_class_name'] = str(interface_results.runtime.interface_class_name)
    payload['version'] = str(interface_results.runtime.version)
    payload['duration_sec'] = float(interface_results.runtime.duration)
    payload['mem_peak_gb'] = float(interface_results.runtime.mem_peak_gb)
    payload['inputs'] = extract_meta_from_filenames(interface_results.inputs)
    print(dumps(payload))
    return payload


def extract_meta_from_filenames(inputs_dict):

    def parse_item(item):
        if isinstance(item, str) and os.path.exists(item) and os.path.isfile(item):
            try:
                nii = nb.load(item)
            except nb.filebasedimages.ImageFileError:
                return item
            stat_dict = {}
            stat_dict['shape'] = list(nii.shape)
            stat_dict['dtype'] = str(nii.get_data_dtype())
            statinfo = os.stat(item)
            stat_dict['st_size'] = statinfo.st_size
            _, _, stat_dict['ext'] = split_filename(item)
            return stat_dict
        else:
            return item

    def crawl_dict(d, u):
        for k, v in u.items():
            if isinstance(v, collections.Mapping):
                d[k] = crawl_dict({}, v)
            elif isinstance(v, list):
                d[k] = crawl_list([], v)
            else:
                d[k] = parse_item(v)
        return d

    def crawl_list(l, u):
        for v in u:
            if isinstance(v, list):
                l.append(crawl_list([], v))
            elif isinstance(v, collections.Mapping):
                l.append(crawl_dict({}, v))
            else:
                l.append(parse_item(v))
        return l

    return crawl_dict({}, inputs_dict)
