#!/usr/bin/python3
from argparse import ArgumentParser
from htsworkflow.submission.encoded import ENCODED
import re


def main(cmdline=None):
    parser = make_parser()
    args = parser.parse_args(cmdline)

    server = ENCODED('www.encodeproject.org')
    server.load_netrc()

    search = server.get_json(args.search)

    for row in search['@graph']:
        if 'Experiment' in row['@type']:
            report_experiment_aliases(server, row)
        else:
            print("Unrecognized type {}".format(row['@type']))


def make_parser():
    parser = ArgumentParser()
    parser.add_argument('search', help='search string')
    return parser


def report_experiment_aliases(server, experiment):
    for replicate in experiment['replicates']:
        library = replicate['library']
        if 'Library' not in library.get('@type', []):
            replicate = server.get_json(replicate['@id'])
            library = replicate['library']

        aliases = library['aliases']
        url = ''
        for a in aliases:
            prefix, payload = a.split(':', 1)
            if re.match('[0-9][0-9][0-9][0-9][0-9]', payload):
                url = 'https://jumpgate.caltech.edu/library/{}/'.format(payload)
        print(experiment['accession'], library['accession'], library['aliases'], url)


if __name__ == '__main__':
    main()
