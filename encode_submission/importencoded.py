import argparse
import logging
import json
import pprint

logger = logging.getLogger('ImportEncoded')

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, create_engine
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Item(Base):
    __tablename__ = 'item'

    uuid = Column(UUID, primary_key=True)
    uri = Column(String)
    object_type = Column(String)
    payload = Column(JSONB)


def create_item(row):
    uuid = row['uuid']
    uri = row['@id']
    object_type = row['@type'][0]

    payload = row.copy()
    del payload['@id']
    del payload['uuid']
    del payload['@type']

    return Item(uri=uri, uuid=uuid, object_type=object_type, payload=payload)


def create_session():
    logger.info("Creating schema")
    engine = create_engine('postgresql://felcat.caltech.edu/htsworkflow')
    Base.metadata.create_all(engine)
    sessionfactory = sessionmaker(bind=engine)
    session = sessionfactory()
    return session


def load_data(session, graph, duplicates):
    seen_pkeys = set()

    for i, row in enumerate(graph):
        obj_id = row['uuid']
        if obj_id not in seen_pkeys:
            session.add(create_item(row))
            seen_pkeys.add(obj_id)
        else:
            duplicates.setdefault(obj_id, []).append(row)

        if (i + 1) % 10000 == 0:
            session.commit()
            print("{} of {}".format(i+1, len(graph)))

    session.commit()
    return duplicates

def load_dump_file(session, filename, collisions):
    logger.info("Parsing %s", filename)
    with open(filename, 'r') as instream:
        data = json.load(instream)

    graph = data['@graph']
    logging.info("Loading")
    load_data(session, graph, collisions)

from htsworkflow.submission import encoded
def stream_load(session, collisions):
    server = encoded.ENCODED('www.encodeproject.org')
    server.load_netrc()

    kwargs = {
        'type': 'Item',
        'frame': 'object',
        'limit': 'all',
    }
    response = server.get_response('/search/', **kwargs)
    data = response.json()
    load_data(session, data['@graph'], collisions)
    response.close()

def main(cmdline=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--encoded', default=False, action='store_true',
                        help='download directly from encoded')
    parser.add_argument('filename', nargs='*', help='json dump file to load')

    args = parser.parse_args(cmdline)

    logging.basicConfig(level=logging.DEBUG)
    collisions = {}
    session = create_session()
    session.execute('TRUNCATE item RESTART IDENTITY;')

    for filename in args.filename:
        load_dump_file(session, filename, collisions)

    if args.encoded:
        stream_load(session, collisions)

    if len(collisions) > 0:
        with open('bad.txt', 'a') as outstream:
            outstream.write(pprint.pformat(collisions))


if __name__ == '__main__':
    main()

