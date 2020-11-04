#!/usr/bin/python3
from argparse import ArgumentParser
import datetime
from htsworkflow.submission.encoded import ENCODED
import numpy
import pandas


def main(cmdline=None):
    # parser = ArgumentParser()
    # args = parser.parse_args(cmdline)

    server = ENCODED('www.encodeproject.org')
    server.load_netrc()

    experiments = find_experiments(server)
    experiments.sort_values(['release_time'], inplace=True)
    cols = list(experiments.columns)
    del cols[cols.index('release_time')]
    experiments[cols].to_csv('encode4_status.csv', index=False)


def find_experiments(server):
    searchTerm = '/search/?type=Experiment&award.rfa=ENCODE4' \
                 '&lab.title=Barbara+Wold%2C+Caltech'\
                 '&lab.title=Ali+Mortazavi%2C+UCI'\
                 '&lab.title=Rob+Spitale%2C+UCI'
    graph = server.get_jsonld(searchTerm)

    experiments = []
    for row in graph['@graph']:
        experiment = server.get_json(row['@id'])
        experiments.append({
            '@id': 'https://www.encodeproject.org' + row['@id'],
            'accession': row['accession'],
            'biosample_summary': row['biosample_summary'],
            'description': row['description'],
            'lab': row['lab']['title'],
            'status': row['status'],
            'audits': count_audits(row),
            'month_released': experiment.get('month_released'),
            'release_time': release_time(experiment.get('month_released')),
        })
    return pandas.DataFrame(experiments)


def release_time(release):
    if release == 'None' or release is None:
        return numpy.inf
    else:
        return datetime.datetime.strptime(release, '%B, %Y').timestamp()


def count_audits(row):
    count = 0
    for level in row['audit']:
        if level != 'INTERNAL_ACTION':
            count += len(row['audit'][level])
    return count


if __name__ == '__main__':
    main()
