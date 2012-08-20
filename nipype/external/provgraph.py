'''Graphical visualisation support for prov.model.

This module produces graphical visualisation for provenanve graphs.
Requires pydot module and Graphviz.

References:

pydot Homepage: http://code.google.com/p/pydot/
Graphviz:       http://www.graphviz.org/
DOT Language:   http://www.graphviz.org/doc/info/lang.html

@author: Dong Huynh <trungdong@donggiang.com>
'''
from ..utils.misc import package_check
package_check('pydot')
import pydot

from .prov import *

# Visual styles for various elements (nodes) and relations (edges)
# see http://graphviz.org/content/attrs
DOT_PROV_STYLE = {
    # Elements
    PROV_REC_ENTITY: {'shape': 'oval', 'style': 'filled', 'fillcolor': 'aliceblue'},
    PROV_REC_ACTIVITY: {'shape': 'box', 'style': 'filled', 'fillcolor': 'lemonchiffon'},
    PROV_REC_AGENT: {'shape': 'house', 'style': 'filled', 'fillcolor': 'yellow'},
    #    PROV_REC_COLLECTION: {'label': 'wasGeneratedBy', 'fontsize': 10.0},
    PROV_REC_BUNDLE: {'shape': 'folder', 'style': 'filled', 'fillcolor': 'aliceblue'},
    # Relations
    PROV_REC_GENERATION: {'label': 'wasGeneratedBy', 'fontsize': '10.0', 'color': 'darkgreen', 'fontcolor': 'darkgreen'},
    PROV_REC_USAGE: {'label': 'used', 'fontsize': '10.0', 'color': 'red4', 'fontcolor': 'red'},
    PROV_REC_COMMUNICATION: {'label': 'wasInformedBy', 'fontsize': '10.0'},
    PROV_REC_START: {'label': 'wasStartedBy', 'fontsize': '10.0'},
    PROV_REC_END: {'label': 'wasEndedBy', 'fontsize': '10.0'},
    PROV_REC_INVALIDATION: {'label': 'wasInvalidatedBy', 'fontsize': '10.0'},
    PROV_REC_DERIVATION: {'label': 'wasDerivedFrom', 'fontsize': '10.0'},
    PROV_REC_ATTRIBUTION: {'label': 'wasAttributedTo', 'fontsize': '10.0', 'color': 'gold'},
    PROV_REC_ASSOCIATION: {'label': 'wasAssociatedWith', 'fontsize': '10.0', 'color': 'gold'},
    PROV_REC_DELEGATION: {'label': 'actedOnBehalfOf', 'fontsize': '10.0', 'color': 'gold'},
    PROV_REC_INFLUENCE: {'label': 'wasInfluencedBy', 'fontsize': '10.0', 'color': 'grey'},
    PROV_REC_ALTERNATE: {'label': 'alternateOf', 'fontsize': '10.0'},
    PROV_REC_SPECIALIZATION: {'label': 'specializationOf', 'fontsize': '10.0'},
    PROV_REC_MENTION: {'label': 'mentionOf', 'fontsize': '10.0'},
    PROV_REC_MEMBERSHIP: {'label': 'hadMember', 'fontsize': '10.0'},
    }

def prov_to_dot(prov_g):
    maindot = pydot.Dot(graph_type='digraph', rankdir='BT')

    node_map = {}
    count = [0, 0, 0]

    def _bundle_to_dot(dot, bundle):
        records = bundle.get_records()
        relations = []
        for rec in records:
            if rec.is_element():
                if isinstance(rec, ProvBundle):
                    count[2] = count[2] + 1
                    subdot = pydot.Cluster(graph_name='c%d' % count[2])
                    subdot.set_label('"%s"' % str(rec.get_identifier()))
                    _bundle_to_dot(subdot, rec)
                    dot.add_subgraph(subdot)
                else:
                    count[0] = count[0] + 1
                    node_id = 'n%d' % count[0]
                    node_label = '"%s"' % str(rec.get_identifier())
                    style = DOT_PROV_STYLE[rec.get_type()]
                    node = pydot.Node(node_id, label=node_label, **style)
                    node_map[rec] = node
                    dot.add_node(node)
            else:
                relations.append(rec)
        for rec in relations:
            nodes = [node for node in rec._attributes.values() if node is not None and isinstance(node, ProvElement)]
            if len(nodes) < 2:
                # Cannot draw this
                pass
            elif len(nodes) == 2:
                # binary relations
                style = DOT_PROV_STYLE[rec.get_type()]
                dot.add_edge(pydot.Edge(node_map[nodes[0]], node_map[nodes[1]], **style))
            else:
                # n-ary relations
                style = DOT_PROV_STYLE[rec.get_type()]
                # add a blank node
                count[1] = count[1] + 1
                bnode_id = 'b%d' % count[1]
                bnode = pydot.Node(bnode_id, label='""', shape='point')
                dot.add_node(bnode)

                dot.add_edge(pydot.Edge(node_map[nodes[0]], bnode, arrowhead='none', **style))
                style = dict(style)
                del style['label']
                for node in nodes[1:]:
                    dot.add_edge(pydot.Edge(bnode, node_map[node], **style))
                    style['color'] = 'gray'

    _bundle_to_dot(maindot, prov_g)
    return maindot


### Testing code
if __name__=="__main__":
    import tempfile, os
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    import test.examples as ex

    path = tempfile.mkdtemp()
    filepath = os.path.join(path, 'dot-test.png')

    # Get an example PROV graph
    prov_g = ex.w3c_publication_1()
    # Convert it to DOT
    dot = prov_to_dot(prov_g)
    dot.set_dpi(120)
    # Write it to a temporary PNG file
    dot.write_png(filepath)

    # Display it using matplotlib
    img=mpimg.imread(filepath)
    imgplot = plt.imshow(img)
    plt.show()
    os.remove(filepath)
