import RDF
from pyld import jsonld

def load_into_model(model, json_data):
    '''Given a PyLD dictionary, load its statements into our Redland model
    '''
    json_graphs = jsonld.to_rdf(json_data)
    for graph in json_graphs:
        for triple in json_graphs[graph]:
            stmt = triple_to_statement(triple)
            model.add_statement(stmt) #, graph_context)

def triple_to_statement(triple):
    '''Convert PyLD triple dictionary to a librdf statement
    '''
    s = to_node(triple['subject'])
    p = to_node(triple['predicate'])
    o = to_node(triple['object'])
    return RDF.Statement(s, p, o)

def to_node(item):
    '''Convert a PyLD node to a Redland node'''
    nodetype = item['type']
    value = item['value']
    datatype = item.get('datatype', None)

    if nodetype == 'blank node':
        return RDF.Node(blank=value)
    elif nodetype == 'IRI':
        return RDF.Node(uri_string=str(value))
    else:
        return RDF.Node(literal=unicode(value).encode('utf-8'),
                        datatype=RDF.Uri(datatype))
