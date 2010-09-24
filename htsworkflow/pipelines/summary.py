"""
Analyze the Summary.htm file produced by GERALD
"""
import logging
import types
from pprint import pprint

from htsworkflow.pipelines.runfolder import ElementTree
from htsworkflow.util.ethelp import indent, flatten

nan = float('nan')

class Summary(object):
    """
    Extract some useful information from the Summary.htm file
    """
    XML_VERSION = 3
    SUMMARY = 'Summary'

    class LaneResultSummary(object):
        """
        Parse the LaneResultSummary table out of Summary.htm
        Mostly for the cluster number
        """
        LANE_RESULT_SUMMARY = 'LaneResultSummary'
        TAGS = {
          'LaneYield': 'lane_yield',
          'Cluster': 'cluster', # Raw
          'ClusterPF': 'cluster_pass_filter',
          'AverageFirstCycleIntensity': 'average_first_cycle_intensity',
          'PercentIntensityAfter20Cycles': 'percent_intensity_after_20_cycles',
          'PercentPassFilterClusters': 'percent_pass_filter_clusters',
          'PercentPassFilterAlign': 'percent_pass_filter_align',
          'AverageAlignmentScore': 'average_alignment_score',
          'PercentErrorRate': 'percent_error_rate'
        }
        # These are tags that have mean/stdev as found in the GERALD Summary.xml file
        GERALD_TAGS = {
          #'laneYield': 'lane_yield', #this is just a number
          'clusterCountRaw': 'cluster', # Raw
          'clusterCountPF': 'cluster_pass_filter',
          'oneSig': 'average_first_cycle_intensity',
          'signal20AsPctOf1': 'percent_intensity_after_20_cycles',
          'percentClustersPF': 'percent_pass_filter_clusters',
          'percentUniquelyAlignedPF': 'percent_pass_filter_align',
          'averageAlignScorePF': 'average_alignment_score',
          'errorPF': 'percent_error_rate'
        }

        def __init__(self, html=None, xml=None):
            self.lane = None
            self.end = 0
            self.lane_yield = None
            self.cluster = None
            self.cluster_pass_filter = None
            self.average_first_cycle_intensity = None
            self.percent_intensity_after_20_cycles = None
            self.percent_pass_filter_clusters = None
            self.percent_pass_filter_align = None
            self.average_alignment_score = None
            self.percent_error_rate = None

            if html is not None:
                self.set_elements_from_html(html)
            if xml is not None:
                self.set_elements(xml)

        def set_elements_from_html(self, data):
            if not len(data) in (8,10):
                raise RuntimeError("Summary.htm file format changed, len(data)=%d" % (len(data),))

            # same in pre-0.3.0 Summary file and 0.3 summary file
            self.lane = int(data[0])

            if len(data) == 8:
                parsed_data = [ parse_mean_range(x) for x in data[1:] ]
                # this is the < 0.3 Pipeline version
                self.cluster = parsed_data[0]
                self.average_first_cycle_intensity = parsed_data[1]
                self.percent_intensity_after_20_cycles = parsed_data[2]
                self.percent_pass_filter_clusters = parsed_data[3]
                self.percent_pass_filter_align = parsed_data[4]
                self.average_alignment_score = parsed_data[5]
                self.percent_error_rate = parsed_data[6]
            elif len(data) == 10:
                parsed_data = [ parse_mean_range(x) for x in data[2:] ]
                # this is the >= 0.3 summary file
                self.lane_yield = data[1]
                self.cluster = parsed_data[0]
                self.cluster_pass_filter = parsed_data[1]
                self.average_first_cycle_intensity = parsed_data[2]
                self.percent_intensity_after_20_cycles = parsed_data[3]
                self.percent_pass_filter_clusters = parsed_data[4]
                self.percent_pass_filter_align = parsed_data[5]
                self.average_alignment_score = parsed_data[6]
                self.percent_error_rate = parsed_data[7]

        def set_elements_from_gerald_xml(self, read, element):
            self.lane = int(element.find('laneNumber').text)
            self.end = read
            lane_yield_node = element.find('laneYield')
            if lane_yield_node is not None:
                self.lane_yield = int(lane_yield_node.text)
            else:
                self.lane_yield = None

            for GeraldName, LRSName in Summary.LaneResultSummary.GERALD_TAGS.items():
                node = element.find(GeraldName)
                if node is None:
                    logging.info("Couldn't find %s" % (GeraldName))
                setattr(self, LRSName, parse_xml_mean_range(node))
                                                                      
        def get_elements(self):
            lane_result = ElementTree.Element(
                            Summary.LaneResultSummary.LANE_RESULT_SUMMARY,
                            {'lane': unicode(self.lane), 'end': unicode(self.end)})
            for tag, variable_name in Summary.LaneResultSummary.TAGS.items():
                value = getattr(self, variable_name)
                if value is None:
                    continue
                # it looks like a sequence
                elif type(value) in (types.TupleType, types.ListType):
                    element = make_mean_range_element(
                      lane_result,
                      tag,
                      *value
                    )
                else:
                    element = ElementTree.SubElement(lane_result, tag)
                    element.text = unicode(value)
            return lane_result

        def set_elements(self, tree):
            if tree.tag != Summary.LaneResultSummary.LANE_RESULT_SUMMARY:
                raise ValueError('Expected %s' % (
                        Summary.LaneResultSummary.LANE_RESULT_SUMMARY))
            self.lane = int(tree.attrib['lane'])
            # default to the first end, for the older summary files
            # that are single ended
            self.end = int(tree.attrib.get('end', 0))
            tags = Summary.LaneResultSummary.TAGS
            for element in list(tree):
                try:
                    variable_name = tags[element.tag]
                    setattr(self, variable_name,
                            parse_summary_element(element))
                except KeyError, e:
                    logging.warn('Unrecognized tag %s' % (element.tag,))

    def __init__(self, filename=None, xml=None):
        # lane results is a list of 1 or 2 ends containing
        # a dictionary of all the lanes reported in this
        # summary file
        self.lane_results = [{}]

        if filename is not None:
            self._extract_lane_results(filename)
        if xml is not None:
            self.set_elements(xml)

    def __getitem__(self, key):
        return self.lane_results[key]

    def __len__(self):
        return len(self.lane_results)

    def _flattened_row(self, row):
        """
        flatten the children of a <tr>...</tr>
        """
        return [flatten(x) for x in row.getchildren() ]

    def _parse_table(self, table):
        """
        assumes the first line is the header of a table,
        and that the remaining rows are data
        """
        rows = table.getchildren()
        data = []
        for r in rows:
            data.append(self._flattened_row(r))
        return data

    def _extract_lane_results(self, pathname):
        """
        Extract just the lane results.
        Currently those are the only ones we care about.
        """
        
        tables = self._extract_named_tables(pathname)


    def _extract_named_tables(self, pathname):
        """
        extract all the 'named' tables from a Summary.htm file
        and return as a dictionary

        Named tables are <h2>...</h2><table>...</table> pairs
        The contents of the h2 tag is considered to the name
        of the table.
        """
        # tree = ElementTree.parse(pathname).getroot()
        # hack for 1.1rc1, this should be removed when possible.
        file_body = open(pathname).read()
        file_body = file_body.replace('CHASTITY<=', 'CHASTITY&lt;=')
        tree = ElementTree.fromstring(file_body)

        # are we reading the xml or the html version of the Summary file?
        if tree.tag.lower() == 'summary':
            # summary version
            tables = self._extract_named_tables_from_gerald_xml(tree)
        elif tree.tag.lower() == 'html':
            # html version
            tables = self._extract_named_tables_from_html(tree)
            table_names = [ ('Lane Results Summary', 0),
                            ('Lane Results Summary : Read 1', 0),
                            ('Lane Results Summary : Read 2', 1),]
            for name, end in table_names:
                if tables.has_key(name):
                    self._extract_lane_results_for_end(tables, name, end)

        if len(self.lane_results[0])  == 0:
            logging.warning("No Lane Results Summary Found in %s" % (pathname,))

    def _extract_named_tables_from_gerald_xml(self, tree):
        """
        Extract useful named tables from a gerald created Summary.xml file
        """
        # using the function to convert to lower instead of just writing it
        # makes the tag easier to read (IMO)
        useful_tables = ['LaneResultsSummary'.lower(),]

        tables ={}
        for child in tree.getchildren():
            if child.tag.lower() in  useful_tables:
                read_tree = child.find('Read')
                # we want 0 based.
                read = int(read_tree.find('readNumber').text)-1
                for element in read_tree.getchildren():
                    if element.tag.lower() == "lane":
                        lrs = Summary.LaneResultSummary()
                        lrs.set_elements_from_gerald_xml(read, element)
                        self.lane_results[lrs.end][lrs.lane] = lrs
        # probably not useful
        return tables
        
    ###### START HTML Table Extraction ########
    def _extract_named_tables_from_html(self, tree):
        body = tree.find('body')
        tables = {}
        for i in range(len(body)):
            if body[i].tag == 'h2' and body[i+1].tag == 'table':
                # we have an interesting table
                name = flatten(body[i])
                table = body[i+1]
                data = self._parse_table(table)
                tables[name] = data
        return tables

    def _extract_lane_results_for_end(self, tables, table_name, end):
        """
        extract the Lane Results Summary table
        """
        # parse lane result summary
        lane_summary = tables[table_name]
        # this is version 1 of the summary file
        if len(lane_summary[-1]) == 8:
            # strip header
            headers = lane_summary[0]
            # grab the lane by lane data
            lane_summary = lane_summary[1:]

        # len(lane_summary[-1] = 10 is version 2 of the summary file
        #                      = 9  is version 3 of the Summary.htm file
        elif len(lane_summary[-1]) in (9, 10):
            # lane_summary[0] is a different less specific header row
            headers = lane_summary[1]
            lane_summary = lane_summary[2:10]
            # after the last lane, there's a set of chip wide averages

        # append an extra dictionary if needed
        if len(self.lane_results) < (end + 1):
          self.lane_results.append({})

        for r in lane_summary:
            lrs = Summary.LaneResultSummary(html=r)
            lrs.end = end
            self.lane_results[lrs.end][lrs.lane] = lrs
    ###### END HTML Table Extraction ########

    def get_elements(self):
        summary = ElementTree.Element(Summary.SUMMARY,
                                      {'version': unicode(Summary.XML_VERSION)})
        for end in self.lane_results:
            for lane in end.values():
                summary.append(lane.get_elements())
        return summary

    def set_elements(self, tree):
        if tree.tag != Summary.SUMMARY:
            return ValueError("Expected %s" % (Summary.SUMMARY,))
        xml_version = int(tree.attrib.get('version', 0))
        if xml_version > Summary.XML_VERSION:
            logging.warn('Summary XML tree is a higher version than this class')
        for element in list(tree):
            lrs = Summary.LaneResultSummary()
            lrs.set_elements(element)
            if len(self.lane_results) < (lrs.end + 1):
              self.lane_results.append({})
            self.lane_results[lrs.end][lrs.lane] = lrs

    def is_paired_end(self):
      return len(self.lane_results) == 2

    def dump(self):
        """
        Debugging function, report current object
        """
        tree = self.get_elements()
        print ElementTree.tostring(tree)

def tonumber(v):
    """
    Convert a value to int if its an int otherwise a float.
    """
    try:
        v = int(v)
    except ValueError, e:
        v = float(v)
    return v

def parse_mean_range(value):
    """
    Parse values like 123 +/- 4.5
    """
    if value.strip() == 'unknown':
        return nan, nan

    values = value.split()
    if len(values) == 1:
        if values[0] == '+/-':
            return nan,nan
        else:
            return tonumber(values[0])

    average, pm, deviation = values
    if pm != '+/-':
        raise RuntimeError("Summary.htm file format changed")
    return tonumber(average), tonumber(deviation)

def make_mean_range_element(parent, name, mean, deviation):
    """
    Make an ElementTree subelement <Name mean='mean', deviation='deviation'/>
    """
    element = ElementTree.SubElement(parent, name,
                                     { 'mean': unicode(mean),
                                       'deviation': unicode(deviation)})
    return element

def parse_mean_range_element(element):
    """
    Grab mean/deviation out of element
    """
    return (tonumber(element.attrib['mean']),
            tonumber(element.attrib['deviation']))

def parse_summary_element(element):
    """
    Determine if we have a simple element or a mean/deviation element
    """
    if len(element.attrib) > 0:
        return parse_mean_range_element(element)
    else:
        return element.text

def parse_xml_mean_range(element):
    """
    Extract mean/stddev children from an element as a tuple
    """
    if element is None:
        return None
    
    mean = element.find('mean')
    stddev = element.find('stdev')
    if mean is None or stddev is None:
        raise RuntimeError("Summary.xml file format changed, expected mean/stddev tags")
    if mean.text is None: 
        mean_value = float('nan')
    else:
        mean_value = tonumber(mean.text)

    if stddev.text is None: 
        stddev_value = float('nan')
    else:
        stddev_value = tonumber(stddev.text)


    return (mean_value, stddev_value)

if __name__ == "__main__":
    # test code
    from optparse import OptionParser
    parser = OptionParser('%prog [Summary.xml/Summary.htm]+')
    opts, args = parser.parse_args()
    if len(args) == 0:
        parser.error('need at least one xml/html file')
    for fname in args:
        s = Summary(fname)
        s.dump()
        
