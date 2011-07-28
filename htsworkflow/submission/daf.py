"""Parse UCSC DAF File
"""
import logging
import os
import re
import string
from StringIO import StringIO
import types
import urlparse

import RDF
from htsworkflow.util.rdfhelp import \
     blankOrUri, \
     dafTermOntology, \
     get_model, \
     libraryOntology, \
     owlNS, \
     rdfNS, \
     submissionLog, \
     submissionOntology, \
     toTypedNode, \
     fromTypedNode
from htsworkflow.util.hashfile import make_md5sum

logger = logging.getLogger(__name__)

#
class ModelException(RuntimeError): pass
class MetadataLookupException(RuntimeError):
    """Problem accessing metadata"""
    pass

# STATES
DAF_HEADER = 1
DAF_VIEW = 2

def parse_into_model(model, submission_name, filename):
    """Read a DAF into RDF Model

    requires a short submission name
    """
    attributes = parse(filename)
    add_to_model(model, attributes, submission_name)

def fromstream_into_model(model, submission_name, daf_stream):
    attributes = parse_stream(daf_stream)
    add_to_model(model, attributes, submission_name)
    
def fromstring_into_model(model, submission_name, daf_string):
    """Read a string containing a DAF into RDF Model

    requires a short submission name
    """
    attributes = fromstring(daf_string)
    add_to_model(model, attributes, submission_name)
    
def parse(filename):
    stream = open(filename,'r')
    attributes =  parse_stream(stream)
    stream.close()
    return attributes

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

def convert_to_rdf_statements(attributes, name):
    submission_uri = get_submission_uri(name)
    subject = RDF.Node(submission_uri)

    statements = []
    for daf_key in attributes:
        predicate = dafTermOntology[daf_key]
        if daf_key == 'views':
            statements.extend(_views_to_statements(name,
                                                   dafTermOntology,
                                                   attributes[daf_key]))
        elif daf_key == 'variables':
            #predicate = ddfNS['variables']
            for var in attributes.get('variables', []):
                obj = toTypedNode(var)
                statements.append(RDF.Statement(subject, predicate, obj))
        else:
            value = attributes[daf_key]
            obj = toTypedNode(value)
            statements.append(RDF.Statement(subject,predicate,obj))

    return statements

def _views_to_statements(name, dafNS, views):
    subject = RDF.Node(get_submission_uri(name))
    viewNS = get_view_namespace(name)

    statements = []
    for view_name in views:
        view_attributes = views[view_name]
        viewSubject = viewNS[view_name]
        statements.append(RDF.Statement(subject, dafNS['views'], viewSubject))
        statements.append(
            RDF.Statement(viewSubject, dafNS['name'], toTypedNode(view_name)))
        for view_attribute_name in view_attributes:
            predicate = dafNS[view_attribute_name]
            obj = toTypedNode(view_attributes[view_attribute_name])
            statements.append(RDF.Statement(viewSubject, predicate, obj)) 
            
        #statements.extend(convert_to_rdf_statements(view, viewNode))
    return statements

def add_to_model(model, attributes, name):
    for statement in convert_to_rdf_statements(attributes, name):
        model.add_statement(statement)
            
def get_submission_uri(name):
    return  submissionLog[name].uri

def get_view_namespace(name):
    submission_uri = get_submission_uri(name)
    viewNS = RDF.NS(str(submission_uri) + '/view/')
    return viewNS

class DAFMapper(object):
    """Convert filenames to views in the UCSC Daf
    """
    def __init__(self, name, daf_file=None, model=None):
        """Construct a RDF backed model of a UCSC DAF

        :args:
          name (str): the name of this submission (used to construct DAF url)
          daf_file (str, stream, or None):
             if str, use as filename
             if stream, parse as stream
             if none, don't attempt to load the DAF into our model
          model (RDF.Model or None):
             if None, construct a memory backed model
             otherwise specifies model to use
        """
        if daf_file is None and model is None:
            logger.error("We need a DAF or Model containing a DAF to work")

        self.name = name
        if model is not None:
            self.model = model
        else:
            self.model = get_model()

        if hasattr(daf_file, 'next'):
            # its some kind of stream
            fromstream_into_model(self.model, name, daf_file)
        else:
            # file
            parse_into_model(self.model, name, daf_file)

        self.libraryNS = RDF.NS('http://jumpgate.caltech.edu/library/')
        self.submissionSet = get_submission_uri(self.name)
        self.submissionSetNS = RDF.NS(str(self.submissionSet)+'/')
        self.__view_map = None


    def add_pattern(self, view_name, filename_pattern):
        """Map a filename regular expression to a view name
        """
        viewNS = get_view_namespace(self.name)

        obj = toTypedNode(filename_pattern)
        self.model.add_statement(
            RDF.Statement(viewNS[view_name],
                          dafTermOntology['filename_re'],
                          obj))


    def import_submission_dir(self, submission_dir, library_id):
        """Import a submission directories and update our model as needed
        """
        #attributes = get_filename_attribute_map(paired)
        libNode = self.libraryNS[library_id + "/"]
        
        self._add_library_details_to_model(libNode)
        
        submission_files = os.listdir(submission_dir)
        for f in submission_files:
            self.construct_file_attributes(submission_dir, libNode, f)

        
    def construct_file_attributes(self, submission_dir, libNode, pathname):
        """Looking for the best extension
        The 'best' is the longest match
        
        :Args:
        filename (str): the filename whose extention we are about to examine
        """
        path, filename = os.path.split(pathname)

        logger.debug("Searching for view")
        view = self.find_view(filename)
        if view is None:
            logger.warn("Unrecognized file: %s" % (pathname,))
            return None
        if str(view) == str(libraryOntology['ignore']):
            return None

        submission_name = self.make_submission_name(submission_dir)
        submissionNode = self.get_submission_node(submission_dir)
        submission_uri = str(submissionNode.uri)
        view_name = fromTypedNode(self.model.get_target(view, dafTermOntology['name']))
        if view_name is None:
            logging.warning('Could not find view name for {0}'.format(str(view)))
            return
        
        view_name = str(view_name)
        submissionView = RDF.Node(RDF.Uri(submission_uri + '/' + view_name))

        self.model.add_statement(
            RDF.Statement(self.submissionSet, dafTermOntology['has_submission'], submissionNode))
        logger.debug("Adding statements to {0}".format(str(submissionNode)))
        self.model.add_statement(RDF.Statement(submissionNode, submissionOntology['has_view'], submissionView))
        self.model.add_statement(RDF.Statement(submissionNode, submissionOntology['name'], toTypedNode(submission_name)))
        self.model.add_statement(RDF.Statement(submissionNode, rdfNS['type'], submissionOntology['submission']))
        self.model.add_statement(RDF.Statement(submissionNode, submissionOntology['library'], libNode))

        logger.debug("Adding statements to {0}".format(str(submissionView)))
        # add trac specific information
        self.model.add_statement(
            RDF.Statement(submissionView, dafTermOntology['view'], view))
        self.model.add_statement(
            RDF.Statement(submissionView, dafTermOntology['paired'], toTypedNode(self._is_paired(libNode))))
        self.model.add_statement(
            RDF.Statement(submissionView, dafTermOntology['submission'], submissionNode))

        # extra information 
        terms = [dafTermOntology['type'],
                 dafTermOntology['filename_re'],
                 ]
        terms.extend((dafTermOntology[v] for v in self.get_daf_variables()))

        # add file specific information
        logger.debug("Updating file md5sum")
        fileNode = RDF.Node(RDF.Uri(submission_uri + '/' + filename))
        submission_pathname = os.path.join(submission_dir, filename)
        md5 = make_md5sum(submission_pathname)
        self.model.add_statement(
            RDF.Statement(submissionView, dafTermOntology['has_file'], fileNode))
        self.model.add_statement(
            RDF.Statement(fileNode, dafTermOntology['filename'], filename))

        if md5 is None:
            logging.warning("Unable to produce md5sum for %s" % ( submission_pathname))
        else:
            self.model.add_statement(
                RDF.Statement(fileNode, dafTermOntology['md5sum'], md5))

        logger.debug("Done.")
        
    def _add_library_details_to_model(self, libNode):
        parser = RDF.Parser(name='rdfa')
        new_statements = parser.parse_as_stream(libNode.uri)
        for s in new_statements:
            # don't override things we already have in the model
            targets = list(self.model.get_targets(s.subject, s.predicate))
            if len(targets) == 0:
                self.model.append(s)

    def get_daf_variables(self):
        """Returns simple variables names that to include in the ddf
        """
        variableTerm = dafTermOntology['variables']
        results = ['view']
        if self.need_replicate():
            results.append('replicate')
            
        for obj in self.model.get_targets(self.submissionSet, variableTerm):
            value = str(fromTypedNode(obj))
            results.append(value)
        results.append('labVersion')
        return results

    def make_submission_name(self, submission_dir):
        submission_dir = os.path.normpath(submission_dir)
        submission_dir_name = os.path.split(submission_dir)[1]
        if len(submission_dir_name) == 0:
            raise RuntimeError(
                "Submission dir name too short: %s" %(submission_dir,))
        return submission_dir_name
        
    def get_submission_node(self, submission_dir):
        """Convert a submission directory name to a submission node
        """
        submission_name = self.make_submission_name(submission_dir)
        return self.submissionSetNS[submission_name]
        
    def _get_library_attribute(self, libNode, attribute):
        if not isinstance(attribute, RDF.Node):
            attribute = libraryOntology[attribute]

        targets = list(self.model.get_targets(libNode, attribute))
        if len(targets) > 0:
            return self._format_library_attribute(targets)
        else:
            return None

        #targets = self._search_same_as(libNode, attribute)
        #if targets is not None:
        #    return self._format_library_attribute(targets)
        
        # we don't know anything about this attribute
        self._add_library_details_to_model(libNode)

        targets = list(self.model.get_targets(libNode, attribute))
        if len(targets) > 0:
            return self._format_library_attribute(targets)

        return None
    
    def _format_library_attribute(self, targets):
        if len(targets) == 0:
            return None
        elif len(targets) == 1:
            return fromTypedNode(targets[0])
        elif len(targets) > 1:
            return [fromTypedNode(t) for t in targets]

    def _search_same_as(self, subject, predicate):
        # look for alternate names
        other_predicates = self.model.get_targets(predicate, owlNS['sameAs'])
        for other in other_predicates:
            targets = list(self.model.get_targets(subject, other))
            if len(targets) > 0:
                return targets
        return None
        
    def find_view(self, filename):
        """Search through potential DAF filename patterns
        """
        if self.__view_map is None:
            self.__view_map = self._get_filename_view_map()

        results = []
        for pattern, view in self.__view_map.items():
            if re.match(pattern, filename):
                results.append(view)

        if len(results) > 1:
            msg = "%s matched multiple views %s" % (
                filename,
                [str(x) for x in results])
            raise ModelException(msg)
        elif len(results) == 1:
            return results[0]
        else:
            return None
        
    def get_view_name(self, view):
        names = list(self.model.get_targets(view, submissionOntology['view_name']))
        if len(names) == 1:
            return fromTypedNode(names[0])
        else:
            msg = "Found wrong number of view names for {0} len = {1}"
            msg = msg.format(str(view), len(names))
            logger.error(msg)
            raise RuntimeError(msg)
        
            
    def _get_filename_view_map(self):
        """Query our model for filename patterns

        return a dictionary of compiled regular expressions to view names
        """
        filename_query = RDF.Statement(
            None, dafTermOntology['filename_re'], None)

        patterns = {}
        for s in self.model.find_statements(filename_query):
            view_name = s.subject
            literal_re = s.object.literal_value['string']
            logger.debug("Found: %s" % (literal_re,))
            try:
                filename_re = re.compile(literal_re)
            except re.error, e:
                logger.error("Unable to compile: %s" % (literal_re,))
            patterns[literal_re] = view_name
        return patterns

    def _get_library_url(self):
        return str(self.libraryNS[''].uri)
    def _set_library_url(self, value):
        self.libraryNS = RDF.NS(str(value))
    library_url = property(_get_library_url, _set_library_url)

    def _is_paired(self, libNode):
        """Determine if a library is paired end"""
        library_type = self._get_library_attribute(libNode, 'library_type')
        if library_type is None:
            raise ModelException("%s doesn't have a library type" % (str(libNode),))
        
        #single = (1,3,6)
        single = ['Single End', 'Small RNA', 'CSHL (lacking last nt)']
        paired = ['Paired End', 'Multiplexing', 'Barcoded']
        if library_type in single:
            return False
        elif library_type in paired:
            return True
        else:
            raise MetadataLookupException(
                "Unrecognized library type %s for %s" % \
                (library_type, str(libNode)))

    def need_replicate(self):
        viewTerm = dafTermOntology['views']
        replicateTerm = dafTermOntology['hasReplicates']

        views = self.model.get_targets(self.submissionSet, viewTerm)

        for view in views:
            replicate = self.model.get_target(view, replicateTerm)
            if fromTypedNode(replicate):
                return True
            
        return False
