"""Parse UCSC DAF File
"""
import logging
import re
import string
from StringIO import StringIO
import types

from htsworkflow.util.rdfhelp import blankOrUri, toTypedNode

logger = logging.getLogger(__name__)

# STATES
DAF_HEADER = 1
DAF_VIEW = 2


def parse(filename):
    stream = open(filename,'r')
    attributes =  parse_stream(stream)
    stream.close()
    return stream

def fromstring(daf_string):
    stream = StringIO(daf_string)
    return parse_stream(stream)

def parse_stream(stream):
    comment_re = re.compile("#.*$")

    state = DAF_HEADER
    attributes = {'views': {}}
    view_name = None
    view_attributes = {}
    for line in stream:
        #remove comments
        line = comment_re.sub("", line)
        nstop = _extract_name_index(line)
        name = line[0:nstop]
        sstop = _consume_whitespace(line, start=nstop)
        vstop = _extract_value_index(line, start=sstop)
        value = line[sstop:vstop]

        if value.lower() in ('yes',):
            value = True
        elif value.lower() in ('no',):
            value = False
            
        if len(name) == 0:
            if view_name is not None:
                attributes['views'][view_name] = view_attributes
                view_name = None
                view_attributes = {}
            state = DAF_HEADER
        elif state == DAF_HEADER and name == 'variables':
            attributes[name] = [ x.strip() for x in value.split(',')]
        elif state == DAF_HEADER and name == 'view':
            view_name = value
            view_attributes['view'] = value
            state = DAF_VIEW
        elif state == DAF_HEADER:
            attributes[name] = value
        elif state == DAF_VIEW:
            view_attributes[name] = value

    # save last block
    if view_name is not None:
        attributes['views'][view_name] = view_attributes
        
    return attributes

def _consume_whitespace(line, start=0):
    for i in xrange(start, len(line)):
        if line[i] not in string.whitespace:
            return i
        
    return len(line)

def _extract_name_index(line, start=0):
    for i in xrange(start, len(line)):
        if line[i] in string.whitespace:
            return i
        
    return len(line)

def _extract_value_index(line, start=0):
    shortline = line.rstrip()
    return len(shortline)

try:
    import RDF
    def convert_to_rdf_statements(attributes, source=None):
        ddfNS = RDF.NS("http://encodesubmit.ucsc.edu/pipeline/download_ddf#")
    
        subject = blankOrUri(source)
        
        statements = []
        for name in attributes:
            predicate = ddfNS[name]
            if name == 'views':
                predicate = ddfNS['views']
                for view_name in attributes.get('views', []):
                    view = attributes['views'][view_name]
                    viewNode = RDF.Node()
                    statements.append(RDF.Statement(subject, predicate, viewNode))
                    statements.extend(convert_to_rdf_statements(view, viewNode))
            elif name == 'variables':
                predicate = ddfNS['variables']
                for var in attributes.get('variables', []):
                    obj = toTypedNode(var)
                    statements.append(RDF.Statement(subject, predicate, obj))
            else:
                value = attributes[name]
                obj = toTypedNode(value)
                statements.append(RDF.Statement(subject,predicate,obj))
    
        return statements
    
    
    def add_to_model(model, attributes, source=None):
        for statement in convert_to_rdf_statements(attributes, source):
            model.add_statement(statement)
            
except ImportError, e:
    def convert_to_rdf_statements(attributes, source=None):
        raise NotImplementedError("librdf not installed")
    def add_to_model(model, attributes, source=None):
        raise NotImplementedError("librdf not installed")

