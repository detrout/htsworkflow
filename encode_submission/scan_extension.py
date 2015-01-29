from __future__ import print_function, unicode_literals

from optparse import OptionParser
import os
import sys
from pprint import pprint

def main(cmdline=None):
    parser = make_parser()
    opts, args = parser.parse_args(cmdline)

    extensions = scan(args)
    common_extensions = find_common_suffix(extensions)

    if opts.rdf:
        print_rdf(common_extensions)
    else:
        print(common_extensions)
        
def make_parser():
    parser = OptionParser("%prog: directory [directory...]")
    parser.add_option('--rdf', action="store_true", default=False,
                      help="Produce rdf configuration file for ucsc_gather")
    return parser

def scan(toscan):
    index = {}
    for cur_scan_dir in toscan:
        for path, dirnames, filenames in os.walk(cur_scan_dir):
            for filename in filenames:
                base, ext = os.path.splitext(filename)
                if ext in ('.daf', 'ddf'):
                    continue
                next_index = index
                for c in filename[::-1]:
                    next_index = next_index.setdefault(c, {})
    return index

def find_common_suffix(index, tail=[]):
    if len(tail) > 0 and len(index) > 1:
        return "".join(tail[::-1])

    results = []
    for key, choice in index.items():
        r = find_common_suffix(choice, tail+[key])
        if r is not None:
            results.append (r)
        
    if len(results) == 0:
        return None
    elif len(results) == 1:
        return results[0]
    else:
        return results

def print_rdf(common_extensions):
    import RDF
    from htsworkflow.util import rdfhelp
    model = rdfhelp.get_model()

    viewName = 'http://jumpgate.caltech.edu/wiki/SubmissionsLog/NAME/view/'
    subView = RDF.NS(viewName)
    fileReTerm = rdfhelp.dafTermOntology['filename_re']

    count = 1
    for ext in common_extensions:
        s = RDF.Statement(subView['VIEW{0}'.format(count)],
                          fileReTerm,
                          '.*{0}$'.format(ext.replace('.', '\\.')))
        model.add_statement(s)
        count += 1
        
    writer = rdfhelp.get_serializer()
    writer.set_namespace('thisSubmissionView', subView._prefix)
    print(writer.serialize_model_to_string(model))

if __name__ == "__main__":
    main()
