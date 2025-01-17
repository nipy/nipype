from collections import OrderedDict

from copy import deepcopy
from pickle import dumps
import os
import getpass
import platform
from uuid import uuid1
import simplejson as json

import numpy as np
import prov.model as pm

from .. import get_info, logging, __version__
from .filemanip import md5, hashlib, hash_infile

logger = logging.getLogger("nipype.utils")
foaf = pm.Namespace("foaf", "http://xmlns.com/foaf/0.1/")
dcterms = pm.Namespace("dcterms", "http://purl.org/dc/terms/")
nipype_ns = pm.Namespace("nipype", "http://nipy.org/nipype/terms/")
niiri = pm.Namespace("niiri", "http://iri.nidash.org/")
crypto = pm.Namespace(
    "crypto",
    ("http://id.loc.gov/vocabulary/preservation/cryptographicHashFunctions/"),
)
get_id = lambda: niiri[uuid1().hex]

PROV_ENVVARS = [
    "PATH",
    "FSLDIR",
    "FREESURFER_HOME",
    "ANTSPATH",
    "CAMINOPATH",
    "CLASSPATH",
    "LD_LIBRARY_PATH",
    "DYLD_LIBRARY_PATH",
    "FIX_VERTEX_AREA",
    "FSF_OUTPUT_FORMAT",
    "FSLCONFDIR",
    "FSLOUTPUTTYPE",
    "LOGNAME",
    "USER",
    "MKL_NUM_THREADS",
    "OMP_NUM_THREADS",
]


def get_attr_id(attr, skip=None):
    dictwithhash, hashval = get_hashval(attr, skip=skip)
    return niiri[hashval]


max_text_len = 1024000


def get_hashval(inputdict, skip=None):
    """Return a dictionary of our items with hashes for each file.

    Searches through dictionary items and if an item is a file, it
    calculates the md5 hash of the file contents and stores the
    file name and hash value as the new key value.

    However, the overall bunch hash is calculated only on the hash
    value of a file. The path and name of the file are not used in
    the overall hash calculation.

    Returns
    -------
    dict_withhash : dict
        Copy of our dictionary with the new file hashes included
        with each file.
    hashvalue : str
        The md5 hash value of the traited spec

    """

    dict_withhash = {}
    dict_nofilename = OrderedDict()
    keys = {}
    for key in inputdict:
        if skip is not None and key in skip:
            continue
        keys[key.uri] = key
    for key in sorted(keys):
        val = inputdict[keys[key]]
        outname = key
        try:
            if isinstance(val, pm.URIRef):
                val = val.decode()
        except AttributeError:
            pass
        if isinstance(val, pm.QualifiedName):
            val = val.uri
        if isinstance(val, pm.Literal):
            val = val.value
        dict_nofilename[outname] = _get_sorteddict(val)
        dict_withhash[outname] = _get_sorteddict(val, True)
        sorted_dict = str(sorted(dict_nofilename.items()))
    return (dict_withhash, md5(sorted_dict.encode()).hexdigest())


def _get_sorteddict(object, dictwithhash=False):
    if isinstance(object, dict):
        out = OrderedDict()
        for key, val in sorted(object.items()):
            if val:
                out[key] = _get_sorteddict(val, dictwithhash)
    elif isinstance(object, (list, tuple)):
        out = []
        for val in object:
            if val:
                out.append(_get_sorteddict(val, dictwithhash))
        if isinstance(object, tuple):
            out = tuple(out)
    else:
        if isinstance(object, str) and os.path.isfile(object):
            hash = hash_infile(object)
            if dictwithhash:
                out = (object, hash)
            else:
                out = hash
        elif isinstance(object, float):
            out = f"{object:.10f}"
        else:
            out = object
    return out


def safe_encode(x, as_literal=True):
    """
    Encodes a python value for prov
    """
    if x is None:
        value = "Unknown"
        if as_literal:
            return pm.Literal(value, pm.XSD["string"])
        else:
            return value

    if isinstance(x, (str, bytes)):
        if isinstance(x, bytes):
            x = str(x, "utf-8")
        if os.path.exists(x):
            if x[0] != os.pathsep:
                x = os.path.abspath(x)
            value = f"file://{platform.node().lower()}{x}"
            if not as_literal:
                return value
            try:
                return pm.URIRef(value)
            except AttributeError:
                return pm.Literal(value, pm.XSD["anyURI"])
        else:
            value = x
            if len(x) > max_text_len:
                cliptxt = "...Clipped..."
                value = x[: max_text_len - len(cliptxt)] + cliptxt

            if not as_literal:
                return value

            return pm.Literal(value, pm.XSD["string"])
    if isinstance(x, int):
        if not as_literal:
            return x
        return pm.Literal(int(x), pm.XSD["integer"])
    if isinstance(x, float):
        if not as_literal:
            return x
        return pm.Literal(x, pm.XSD["float"])
    if isinstance(x, dict):
        outdict = {}
        for key, value in list(x.items()):
            encoded_value = safe_encode(value, as_literal=False)
            if isinstance(encoded_value, pm.Literal):
                outdict[key] = encoded_value.json_representation()
            else:
                outdict[key] = encoded_value

        try:
            jsonstr = json.dumps(outdict)
        except UnicodeDecodeError as excp:
            jsonstr = f"Could not encode dictionary. {excp}"
            logger.warning("Prov: %s", jsonstr)

        if not as_literal:
            return jsonstr
        return pm.Literal(jsonstr, pm.XSD["string"])
    if isinstance(x, (list, tuple)):
        x = list(x)
        is_object = False
        try:
            nptype = np.array(x).dtype
            is_object = nptype == np.dtype(object)
        except ValueError:
            is_object = True

        # If the array contains an heterogeneous mixture of data types
        # they should be encoded sequentially
        if is_object:
            outlist = []
            for value in x:
                encoded_value = safe_encode(value, as_literal=False)
                if isinstance(encoded_value, pm.Literal):
                    outlist.append(encoded_value.json_representation())
                else:
                    outlist.append(encoded_value)
            x = outlist

        try:
            jsonstr = json.dumps(x)
        except UnicodeDecodeError as excp:
            jsonstr = f"Could not encode list/tuple. {excp}"
            logger.warning("Prov: %s", jsonstr)

        if not as_literal:
            return jsonstr
        return pm.Literal(jsonstr, pm.XSD["string"])

    # If is a literal, and as_literal do nothing.
    # else bring back to json.
    if isinstance(x, pm.Literal):
        if as_literal:
            return x
        return dumps(x.json_representation())

    jsonstr = None
    ltype = pm.XSD["string"]
    try:
        jsonstr = json.dumps(x.__dict__)
    except AttributeError:
        pass

    if jsonstr is None:
        try:
            jsonstr = dumps(x)
            ltype = nipype_ns["pickle"]
        except TypeError as excp:
            jsonstr = f"Could not encode object. {excp}"

    if not as_literal:
        return jsonstr
    return pm.Literal(jsonstr, ltype)


def prov_encode(graph, value, create_container=True):
    if isinstance(value, (list, tuple)) and create_container:
        value = list(value)
        if len(value) == 0:
            encoded_literal = safe_encode(value)
            attr = {pm.PROV["value"]: encoded_literal}
            eid = get_attr_id(attr)
            return graph.entity(eid, attr)

        if len(value) == 1:
            return prov_encode(graph, value[0])

        entities = []
        for item in value:
            item_entity = prov_encode(graph, item)
            entities.append(item_entity)
            if isinstance(item, (list, tuple)):
                continue

            item_entity_val = list(item_entity.value)[0]
            is_str = isinstance(item_entity_val, str)
            if not is_str or (is_str and "file://" not in item_entity_val):
                return prov_encode(graph, value, create_container=False)

        eid = get_id()
        entity = graph.collection(identifier=eid)
        for item_entity in entities:
            graph.hadMember(eid, item_entity)

        return entity
    else:
        encoded_literal = safe_encode(value)
        attr = {pm.PROV["value"]: encoded_literal}
        if isinstance(value, str) and os.path.exists(value):
            attr.update({pm.PROV["location"]: encoded_literal})
            if not os.path.isdir(value):
                sha512 = hash_infile(value, crypto=hashlib.sha512)
                attr.update({crypto["sha512"]: pm.Literal(sha512, pm.XSD["string"])})
                eid = get_attr_id(attr, skip=[pm.PROV["location"], pm.PROV["value"]])
            else:
                eid = get_attr_id(attr, skip=[pm.PROV["location"]])
        else:
            eid = get_attr_id(attr)
        entity = graph.entity(eid, attr)
    return entity


def write_provenance(results, filename="provenance", format="all"):
    prov = None
    try:
        ps = ProvStore()
        ps.add_results(results)
        prov = ps.write_provenance(filename=filename, format=format)
    except Exception as e:
        import traceback

        err_msg = traceback.format_exc()
        if e.args:
            err_msg += "\n\nException arguments:\n" + ", ".join(
                ['"%s"' % arg for arg in e.args]
            )
        logger.warning("Writing provenance failed - Exception details:\n%s", err_msg)

    return prov


class ProvStore:
    def __init__(self):
        self.g = pm.ProvDocument()
        self.g.add_namespace(foaf)
        self.g.add_namespace(dcterms)
        self.g.add_namespace(nipype_ns)
        self.g.add_namespace(niiri)

    def add_results(self, results, keep_provenance=False):
        if keep_provenance and results.provenance:
            self.g = deepcopy(results.provenance)
            return self.g
        runtime = results.runtime
        interface = results.interface
        inputs = results.inputs
        outputs = results.outputs
        classname = interface.__name__
        modulepath = f"{interface.__module__}.{interface.__name__}"
        activitytype = "".join([i.capitalize() for i in modulepath.split(".")])

        a0_attrs = {
            nipype_ns["module"]: interface.__module__,
            nipype_ns["interface"]: classname,
            pm.PROV["type"]: nipype_ns[activitytype],
            pm.PROV["label"]: classname,
            nipype_ns["duration"]: safe_encode(runtime.duration),
            nipype_ns["workingDirectory"]: safe_encode(runtime.cwd),
            nipype_ns["returnCode"]: safe_encode(runtime.returncode),
            nipype_ns["platform"]: safe_encode(runtime.platform),
            nipype_ns["version"]: safe_encode(runtime.version),
        }
        a0_attrs[foaf["host"]] = pm.Literal(runtime.hostname, pm.XSD["anyURI"])

        try:
            a0_attrs.update({nipype_ns["command"]: safe_encode(runtime.cmdline)})
            a0_attrs.update(
                {nipype_ns["commandPath"]: safe_encode(runtime.command_path)}
            )
            a0_attrs.update(
                {nipype_ns["dependencies"]: safe_encode(runtime.dependencies)}
            )
        except AttributeError:
            pass
        a0 = self.g.activity(get_id(), runtime.startTime, runtime.endTime, a0_attrs)
        # environment
        id = get_id()
        env_collection = self.g.collection(id)
        env_collection.add_attributes(
            {pm.PROV["type"]: nipype_ns["Environment"], pm.PROV["label"]: "Environment"}
        )
        self.g.used(a0, id)
        # write environment entities
        for idx, (key, val) in enumerate(sorted(runtime.environ.items())):
            if key not in PROV_ENVVARS:
                continue
            in_attr = {
                pm.PROV["label"]: key,
                nipype_ns["environmentVariable"]: key,
                pm.PROV["value"]: safe_encode(val),
            }
            id = get_attr_id(in_attr)
            self.g.entity(id, in_attr)
            self.g.hadMember(env_collection, id)
        # write input entities
        if inputs:
            id = get_id()
            input_collection = self.g.collection(id)
            input_collection.add_attributes(
                {pm.PROV["type"]: nipype_ns["Inputs"], pm.PROV["label"]: "Inputs"}
            )
            # write input entities
            for idx, (key, val) in enumerate(sorted(inputs.items())):
                in_entity = prov_encode(self.g, val).identifier
                self.g.hadMember(input_collection, in_entity)
                used_attr = {pm.PROV["label"]: key, nipype_ns["inPort"]: key}
                self.g.used(activity=a0, entity=in_entity, other_attributes=used_attr)
        # write output entities
        if outputs:
            id = get_id()
            output_collection = self.g.collection(id)
            if not isinstance(outputs, dict):
                outputs = outputs.get_traitsfree()
            output_collection.add_attributes(
                {pm.PROV["type"]: nipype_ns["Outputs"], pm.PROV["label"]: "Outputs"}
            )
            self.g.wasGeneratedBy(output_collection, a0)
            # write output entities
            for idx, (key, val) in enumerate(sorted(outputs.items())):
                out_entity = prov_encode(self.g, val).identifier
                self.g.hadMember(output_collection, out_entity)
                gen_attr = {pm.PROV["label"]: key, nipype_ns["outPort"]: key}
                self.g.generation(out_entity, activity=a0, other_attributes=gen_attr)
        # write runtime entities
        id = get_id()
        runtime_collection = self.g.collection(id)
        runtime_collection.add_attributes(
            {pm.PROV["type"]: nipype_ns["Runtime"], pm.PROV["label"]: "RuntimeInfo"}
        )
        self.g.wasGeneratedBy(runtime_collection, a0)
        for key, value in sorted(runtime.items()):
            if not value:
                continue
            if key not in ["stdout", "stderr", "merged"]:
                continue
            attr = {pm.PROV["label"]: key, nipype_ns[key]: safe_encode(value)}
            id = get_id()
            self.g.entity(get_id(), attr)
            self.g.hadMember(runtime_collection, id)

        # create agents
        user_attr = {
            pm.PROV["type"]: pm.PROV["Person"],
            pm.PROV["label"]: getpass.getuser(),
            foaf["name"]: safe_encode(getpass.getuser()),
        }
        user_agent = self.g.agent(get_attr_id(user_attr), user_attr)
        agent_attr = {
            pm.PROV["type"]: pm.PROV["SoftwareAgent"],
            pm.PROV["label"]: "Nipype",
            foaf["name"]: safe_encode("Nipype"),
            nipype_ns["version"]: __version__,
        }
        for key, value in list(get_info().items()):
            agent_attr.update({nipype_ns[key]: safe_encode(value)})
        software_agent = self.g.agent(get_attr_id(agent_attr), agent_attr)
        self.g.wasAssociatedWith(
            a0, user_agent, None, None, {pm.PROV["hadRole"]: nipype_ns["LoggedInUser"]}
        )
        self.g.wasAssociatedWith(a0, software_agent)
        return self.g

    def write_provenance(self, filename="provenance", format="all"):
        if format in ["provn", "all"]:
            with open(filename + ".provn", "w") as fp:
                fp.writelines(self.g.get_provn())
        try:
            if format in ["rdf", "all"]:
                if len(self.g.bundles) == 0:
                    rdf_format = "turtle"
                    ext = ".ttl"
                else:
                    rdf_format = "trig"
                    ext = ".trig"
                self.g.serialize(filename + ext, format="rdf", rdf_format=rdf_format)
            if format in ["jsonld"]:
                self.g.serialize(
                    filename + ".jsonld", format="rdf", rdf_format="json-ld", indent=4
                )
        except pm.serializers.DoNotExist:
            pass
        return self.g
