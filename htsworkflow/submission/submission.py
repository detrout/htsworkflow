"""Common submission elements
"""
import logging
import os
import re

import RDF

from htsworkflow.util.rdfhelp import \
     blankOrUri, \
     dump_model, \
     fromTypedNode, \
     get_model, \
     strip_namespace, \
     toTypedNode
from htsworkflow.util.rdfns import *
from htsworkflow.util.hashfile import make_md5sum
from htsworkflow.submission.fastqname import FastqName
from htsworkflow.submission.daf import \
     MetadataLookupException, \
     ModelException, \
     get_submission_uri
from htsworkflow.util import opener

from django.template import Context, Template, loader

LOGGER = logging.getLogger(__name__)

class Submission(object):
    def __init__(self, name, model, host):
        self.name = name
        self.model = model

        self.submissionSet = get_submission_uri(self.name)
        self.submissionSetNS = RDF.NS(str(self.submissionSet) + '#')
        self.libraryNS = RDF.NS('{0}/library/'.format(host))
        self.flowcellNS = RDF.NS('{0}/flowcell/'.format(host))

        self.__view_map = None

    def scan_submission_dirs(self, result_map):
        """Examine files in our result directory
        """
        for lib_id, result_dir in result_map.items():
            LOGGER.info("Importing %s from %s" % (lib_id, result_dir))
            try:
                self.import_analysis_dir(result_dir, lib_id)
            except MetadataLookupException as e:
                LOGGER.error("Skipping %s: %s" % (lib_id, str(e)))

    def import_analysis_dir(self, analysis_dir, library_id):
        """Import a submission directories and update our model as needed
        """
        #attributes = get_filename_attribute_map(paired)
        libNode = self.libraryNS[library_id + "/"]

        self._add_library_details_to_model(libNode)

        submission_files = os.listdir(analysis_dir)
        for filename in submission_files:
            pathname = os.path.abspath(os.path.join(analysis_dir, filename))
            self.construct_file_attributes(analysis_dir, libNode, pathname)

    def analysis_nodes(self, result_map):
        """Return an iterable of analysis nodes
        """
        for result_dir in result_map.values():
            an_analysis = self.get_submission_node(result_dir)
            yield an_analysis

    def construct_file_attributes(self, analysis_dir, libNode, pathname):
        """Looking for the best extension
        The 'best' is the longest match

        :Args:
        filename (str): the filename whose extention we are about to examine
        """
        path, filename = os.path.split(pathname)

        LOGGER.debug("Searching for view")
        file_type = self.find_best_match(filename)
        if file_type is None:
            LOGGER.warn("Unrecognized file: {0}".format(pathname))
            return None
        if str(file_type) == str(libraryOntology['ignore']):
            return None

        an_analysis_name = self.make_submission_name(analysis_dir)
        an_analysis = self.get_submission_node(analysis_dir)
        file_classification = self.model.get_target(file_type,
                                                    rdfNS['type'])
        if file_classification is None:
            errmsg = 'Could not find class for {0}'
            LOGGER.warning(errmsg.format(str(file_type)))
            return

        self.model.add_statement(
            RDF.Statement(self.submissionSetNS[''],
                          submissionOntology['has_submission'],
                          an_analysis))
        self.model.add_statement(RDF.Statement(an_analysis,
                                               submissionOntology['name'],
                                               toTypedNode(an_analysis_name)))
        self.model.add_statement(
            RDF.Statement(an_analysis,
                          rdfNS['type'],
                          submissionOntology['submission']))
        self.model.add_statement(RDF.Statement(an_analysis,
                                               submissionOntology['library'],
                                               libNode))

        LOGGER.debug("Adding statements to {0}".format(str(an_analysis)))
        # add track specific information
        self.model.add_statement(
            RDF.Statement(an_analysis,
                          dafTermOntology['paired'],
                          toTypedNode(self._is_paired(libNode))))
        self.model.add_statement(
            RDF.Statement(an_analysis,
                          dafTermOntology['submission'],
                          an_analysis))

        # add file specific information
        fileNode = self.make_file_node(pathname, an_analysis)
        self.add_md5s(filename, fileNode, analysis_dir)
        self.add_file_size(filename, fileNode, analysis_dir)
        self.add_read_length(filename, fileNode, analysis_dir)
        self.add_fastq_metadata(filename, fileNode)
        self.add_label(file_type, fileNode, libNode)
        self.model.add_statement(
            RDF.Statement(fileNode,
                          rdfNS['type'],
                          file_type))
        self.model.add_statement(
            RDF.Statement(fileNode,
                          libraryOntology['library'],
                          libNode))

        LOGGER.debug("Done.")

    def make_file_node(self, pathname, submissionNode):
        """Create file node and attach it to its submission.
        """
        # add file specific information
        path, filename = os.path.split(pathname)
        pathname = os.path.abspath(pathname)
        fileNode = RDF.Node(RDF.Uri('file://'+ pathname))
        self.model.add_statement(
            RDF.Statement(submissionNode,
                          dafTermOntology['has_file'],
                          fileNode))
        self.model.add_statement(
            RDF.Statement(fileNode,
                          dafTermOntology['filename'],
                          filename))
        self.model.add_statement(
            RDF.Statement(fileNode,
                          dafTermOntology['relative_path'],
                          os.path.relpath(pathname)))
        return fileNode

    def add_md5s(self, filename, fileNode, analysis_dir):
        LOGGER.debug("Updating file md5sum")
        submission_pathname = os.path.join(analysis_dir, filename)
        md5 = make_md5sum(submission_pathname)
        if md5 is None:
            errmsg = "Unable to produce md5sum for {0}"
            LOGGER.warning(errmsg.format(submission_pathname))
        else:
            self.model.add_statement(
                RDF.Statement(fileNode, dafTermOntology['md5sum'], md5))

    def add_file_size(self, filename, fileNode, analysis_dir):
        submission_pathname = os.path.join(analysis_dir, filename)
        file_size = os.stat(submission_pathname).st_size
        self.model.add_statement(
            RDF.Statement(fileNode, dafTermOntology['file_size'], toTypedNode(file_size)))
        LOGGER.debug("Updating file size: %d", file_size)

    def add_read_length(self, filename, fileNode, analysis_dir):
        submission_pathname = os.path.join(analysis_dir, filename)
        stream = opener.autoopen(submission_pathname, 'rt')
        header = stream.readline().strip()
        sequence = stream.readline().strip()
        read_length = len(sequence)
        self.model.add_statement(
            RDF.Statement(fileNode,
                          libraryOntology['read_length'],
                          toTypedNode(read_length))
        )
        LOGGER.debug("Updating read length: %d", read_length)

    def add_fastq_metadata(self, filename, fileNode):
        # How should I detect if this is actually a fastq file?
        try:
            fqname = FastqName(filename=filename)
        except ValueError:
            # currently its just ignore it if the fastq name parser fails
            return

        terms = [('flowcell', libraryOntology['flowcell_id']),
                 ('lib_id', libraryOntology['library_id']),
                 ('lane', libraryOntology['lane_number']),
                 ('read', libraryOntology['read']),
        ]
        for file_term, model_term in terms:
            value = fqname.get(file_term)
            if value is not None:
                s = RDF.Statement(fileNode, model_term, toTypedNode(value))
                self.model.append(s)

        if 'flowcell' in fqname:
            value = self.flowcellNS[fqname['flowcell'] + '/']
            s = RDF.Statement(fileNode, libraryOntology['flowcell'], value)
            self.model.append(s)

    def add_label(self, file_type, file_node, lib_node):
        """Add rdfs:label to a file node
        """
        #template_term = libraryOntology['label_template']
        template_term = libraryOntology['label_template']
        label_template = self.model.get_target(file_type, template_term)
        if label_template:
            template = loader.get_template('submission_view_rdfs_label_metadata.sparql')
            context = Context({
                'library': str(lib_node.uri),
                })
            for r in self.execute_query(template, context):
                context = Context(r)
                label = Template(label_template).render(context)
                s = RDF.Statement(file_node, rdfsNS['label'], unicode(label))
                self.model.append(s)

    def _add_library_details_to_model(self, libNode):
        # attributes that can have multiple values
        set_attributes = set((libraryOntology['has_lane'],
                              libraryOntology['has_mappings'],
                              dafTermOntology['has_file']))
        parser = RDF.Parser(name='rdfa')
        try:
            new_statements = parser.parse_as_stream(libNode.uri)
        except RDF.RedlandError as e:
            LOGGER.error(e)
            return
        LOGGER.debug("Scanning %s", str(libNode.uri))
        toadd = []
        for s in new_statements:
            # always add "collections"
            if s.predicate in set_attributes:
                toadd.append(s)
                continue
            # don't override things we already have in the model
            targets = list(self.model.get_targets(s.subject, s.predicate))
            if len(targets) == 0:
                toadd.append(s)

        for s in toadd:
            self.model.append(s)

        self._add_lane_details(libNode)
        self._add_flowcell_details()

    def _add_lane_details(self, libNode):
        """Import lane details
        """
        query = RDF.Statement(libNode, libraryOntology['has_lane'], None)
        lanes = []
        for lane_stmt in self.model.find_statements(query):
            lanes.append(lane_stmt.object)

        parser = RDF.Parser(name='rdfa')
        for lane in lanes:
            LOGGER.debug("Importing %s" % (lane.uri,))
            try:
                parser.parse_into_model(self.model, lane.uri)
            except RDF.RedlandError as e:
                LOGGER.error("Error accessing %s" % (lane.uri,))
                raise e


    def _add_flowcell_details(self):
        template = loader.get_template('aws_flowcell.sparql')
        results = self.execute_query(template, Context())

        parser = RDF.Parser(name='rdfa')
        for r in self.execute_query(template, Context()):
            flowcell = r['flowcell']
            try:
                parser.parse_into_model(self.model, flowcell.uri)
            except RDF.RedlandError as e:
                LOGGER.error("Error accessing %s" % (str(flowcell)))
                raise e


    def find_best_match(self, filename):
        """Search through potential filename matching patterns
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
            LOGGER.debug("Found: %s" % (literal_re,))
            try:
                filename_re = re.compile(literal_re)
            except re.error as e:
                LOGGER.error("Unable to compile: %s" % (literal_re,))
            patterns[literal_re] = view_name
        return patterns

    def make_submission_name(self, analysis_dir):
        analysis_dir = os.path.normpath(analysis_dir)
        analysis_dir_name = os.path.split(analysis_dir)[1]
        if len(analysis_dir_name) == 0:
            raise RuntimeError(
                "Submission dir name too short: {0}".format(analysis_dir))
        return analysis_dir_name

    def get_submission_node(self, analysis_dir):
        """Convert a submission directory name to a submission node
        """
        submission_name = self.make_submission_name(analysis_dir)
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

    def _is_paired(self, libNode):
        """Determine if a library is paired end"""
        library_type = self._get_library_attribute(libNode, 'library_type')
        if library_type is None:
            errmsg = "%s doesn't have a library type"
            raise ModelException(errmsg % (str(libNode),))

        single = ['CSHL (lacking last nt)',
                  'Single End (non-multiplexed)',
                  'Small RNA (non-multiplexed)',]
        paired = ['Barcoded Illumina',
                  'Multiplexing',
                  'NEBNext Multiplexed',
                  'NEBNext Small RNA',
                  'Nextera',
                  'Paired End (non-multiplexed)',
                  'Dual Index Illumina',]
        if library_type in single:
            return False
        elif library_type in paired:
            return True
        else:
            raise MetadataLookupException(
                "Unrecognized library type %s for %s" % \
                (library_type, str(libNode)))

    def execute_query(self, template, context):
        """Execute the query, returning the results
        """
        formatted_query = template.render(context)
        LOGGER.debug(formatted_query)
        query = RDF.SPARQLQuery(str(formatted_query))
        rdfstream = query.execute(self.model)
        results = []
        for record in rdfstream:
            d = {}
            for key, value in record.items():
                d[key] = fromTypedNode(value)
            results.append(d)
        return results


def list_submissions(model):
    """Return generator of submissions in this model.
    """
    query_body = """
      PREFIX subns: <http://jumpgate.caltech.edu/wiki/UcscSubmissionOntology#>

      select distinct ?submission
      where { ?submission subns:has_submission ?library_dir }
    """
    query = RDF.SPARQLQuery(query_body)
    rdfstream = query.execute(model)
    for row in rdfstream:
        s = strip_namespace(submissionLog, row['submission'])
        if s[-1] in ['#', '/', '?']:
            s = s[:-1]
        yield s
