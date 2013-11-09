from cPickle import dumps
import json
import os
import pwd
from socket import getfqdn
from uuid import uuid1

try:
    import prov.model as pm
except ImportError:
    from ..external import provcopy as pm

from .. import get_info
from .. import logging
iflogger = logging.getLogger('interface')

foaf = pm.Namespace("foaf", "http://xmlns.com/foaf/0.1/")
dcterms = pm.Namespace("dcterms", "http://purl.org/dc/terms/")
nipype_ns = pm.Namespace("nipype", "http://nipy.org/nipype/terms/")
niiri = pm.Namespace("niiri", "http://iri.nidash.org/")

get_id = lambda: niiri[uuid1().hex]

max_text_len = 1024000

def safe_encode(x):
    """Encodes a python value for prov
    """
    if x is None:
        return pm.Literal("Unknown", pm.XSD['string'])
    try:
        if isinstance(x, (str, unicode)):
            if os.path.exists(x):
                try:
                    return pm.URIRef('file://%s%s' % (getfqdn(), x))
                except AttributeError:
                    return pm.Literal('file://%s%s' % (getfqdn(), x),
                                      pm.XSD['anyURI'])
            else:
                if len(x) > max_text_len:
                    return pm.Literal(x[:max_text_len - 13] + ['...Clipped...'],
                                      pm.XSD['string'])
                else:
                    return pm.Literal(x, pm.XSD['string'])
        if isinstance(x, (int,)):
            return pm.Literal(int(x), pm.XSD['integer'])
        if isinstance(x, (float,)):
            return pm.Literal(x, pm.XSD['float'])
        if isinstance(x, dict):
            outdict = {}
            for key, value in x.items():
                encoded_value = safe_encode(value)
                if isinstance(encoded_value, (pm.Literal,)):
                    outdict[key] = encoded_value.json_representation()
                else:
                    outdict[key] = encoded_value
            return pm.Literal(json.dumps(outdict), pm.XSD['string'])
        if isinstance(x, list):
            outlist = []
            for value in x:
                encoded_value = safe_encode(value)
                if isinstance(encoded_value, (pm.Literal,)):
                    outlist.append(encoded_value.json_representation())
                else:
                    outlist.append(encoded_value)
            return pm.Literal(json.dumps(outlist), pm.XSD['string'])
        return pm.Literal(dumps(x), nipype_ns['pickle'])
    except TypeError, e:
        iflogger.info(e)
        return pm.Literal("Could not encode: " + str(e), pm.XSD['string'])


def write_provenance(results, filename='provenance', format='turtle'):
    ps = ProvStore()
    ps.add_results(results)
    return ps.write_provenance(filename=filename, format=format)

class ProvStore(object):

    def __init__(self):
        self.g = pm.ProvBundle(identifier=get_id())
        self.g.add_namespace(foaf)
        self.g.add_namespace(dcterms)
        self.g.add_namespace(nipype_ns)
        self.g.add_namespace(niiri)

    def add_results(self, results):
        if results.provenance:
            try:
                self.g.add_bundle(results.provenance)
            except pm.ProvException:
                self.g.add_bundle(results.provenance, get_id())
            return self.g
        runtime = results.runtime
        interface = results.interface
        inputs = results.inputs
        outputs = results.outputs
        classname = interface.__class__.__name__

        a0_attrs = {nipype_ns['module']: self.__module__,
                    nipype_ns["interface"]: classname,
                    pm.PROV["label"]: classname,
                    nipype_ns['duration']: safe_encode(runtime.duration),
                    nipype_ns['working_directory']: safe_encode(runtime.cwd),
                    nipype_ns['return_code']: runtime.returncode,
                    nipype_ns['platform']: safe_encode(runtime.platform),
                    nipype_ns['version']: safe_encode(runtime.version),
                    }
        try:
            a0_attrs[foaf["host"]] = pm.URIRef(runtime.hostname)
        except AttributeError:
            a0_attrs[foaf["host"]] = pm.Literal(runtime.hostname,
                                                pm.XSD['anyURI'])

        try:
            a0_attrs.update({nipype_ns['command']: safe_encode(runtime.cmdline)})
            a0_attrs.update({nipype_ns['command_path']:
                                 safe_encode(runtime.command_path)})
            a0_attrs.update({nipype_ns['dependencies']:
                                 safe_encode(runtime.dependencies)})
        except AttributeError:
            pass
        a0 = self.g.activity(get_id(), runtime.startTime, runtime.endTime,
                        a0_attrs)
        # environment
        id = get_id()
        env_collection = self.g.collection(id)
        env_collection.add_extra_attributes({pm.PROV['type']:
                                                 nipype_ns['environment'],
                                             pm.PROV['label']: "Environment"})
        self.g.used(a0, id)
        # write environment entities
        for idx, (key, val) in enumerate(sorted(runtime.environ.items())):
            in_attr = {pm.PROV["label"]: key,
                       nipype_ns["environment_variable"]: key,
                       nipype_ns["value"]: safe_encode(val)}
            id = get_id()
            self.g.entity(id, in_attr)
            self.g.hadMember(env_collection, id)
        # write input entities
        if inputs:
            id = get_id()
            input_collection = self.g.collection(id)
            input_collection.add_extra_attributes({pm.PROV['type']:
                                                       nipype_ns['inputs'],
                                                   pm.PROV['label']: "Inputs"})
            self.g.used(a0, id)
            # write input entities
            for idx, (key, val) in enumerate(sorted(inputs.items())):
                in_attr = {pm.PROV["label"]: key,
                           nipype_ns["in_port"]: key,
                           nipype_ns["value"]: safe_encode(val)}
                id = get_id()
                self.g.entity(id, in_attr)
                self.g.hadMember(input_collection, id)
        # write output entities
        if outputs:
            id = get_id()
            output_collection = self.g.collection(id)
            if not isinstance(outputs, dict):
                outputs = outputs.get_traitsfree()
            output_collection.add_extra_attributes({pm.PROV['type']:
                                                        nipype_ns['outputs'],
                                                    pm.PROV['label']:
                                                        "Outputs"})
            self.g.wasGeneratedBy(output_collection, a0)
            # write input entities
            for idx, (key, val) in enumerate(sorted(outputs.items())):
                out_attr = {pm.PROV["label"]: key,
                            nipype_ns["out_port"]: key,
                            nipype_ns["value"]: safe_encode(val)}
                id = get_id()
                self.g.entity(id, out_attr)
                self.g.hadMember(output_collection, id)
        # write runtime entities
        id = get_id()
        runtime_collection = self.g.collection(id)
        runtime_collection.add_extra_attributes({pm.PROV['type']:
                                                     nipype_ns['runtime'],
                                                 pm.PROV['label']:
                                                     "RuntimeInfo"})
        self.g.wasGeneratedBy(runtime_collection, a0)
        for key, value in sorted(runtime.items()):
            if not value:
                continue
            if key not in ['stdout', 'stderr', 'merged']:
                continue
            attr = {pm.PROV["label"]: key,
                    nipype_ns[key]: safe_encode(value)}
            id = get_id()
            self.g.entity(get_id(), attr)
            self.g.hadMember(runtime_collection, id)
        # create agents
        user_agent = self.g.agent(get_id(),
                             {pm.PROV["type"]: pm.PROV["Person"],
                              pm.PROV["label"]:
                                  pwd.getpwuid(os.geteuid()).pw_name,
                              foaf["name"]:
                               safe_encode(pwd.getpwuid(os.geteuid()).pw_name)})
        agent_attr = {pm.PROV["type"]: pm.PROV["SoftwareAgent"],
                      pm.PROV["label"]: "Nipype",
                      foaf["name"]: safe_encode("Nipype")}
        for key, value in get_info().items():
            agent_attr.update({nipype_ns[key]: safe_encode(value)})
        software_agent = self.g.agent(get_id(), agent_attr)
        self.g.wasAssociatedWith(a0, user_agent, None, None,
                            {pm.PROV["Role"]: nipype_ns["LoggedInUser"]})
        self.g.wasAssociatedWith(a0, software_agent, None, None,
                            {pm.PROV["Role"]: nipype_ns["Software"]})
        return self.g

    def write_provenance(self, filename='provenance', format='turtle'):
        try:
            if format in ['turtle', 'all']:
                self.g.rdf().serialize(filename + '.ttl', format='turtle')
        except (ImportError, NameError):
            format = 'all'
        finally:
            if format in ['provn', 'all']:
                with open(filename + '.provn', 'wt') as fp:
                    fp.writelines(self.g.get_provn())
            if format in ['json', 'all']:
                with open(filename + '.json', 'wt') as fp:
                    pm.json.dump(self.g, fp, cls=pm.ProvBundle.JSONEncoder)
        return self.g
