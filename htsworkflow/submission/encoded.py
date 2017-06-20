"""Interface with encoded software for ENCODE3 data submission & warehouse

This allows retrieving blocks
"""
from __future__ import print_function
import pandas
import base64
import collections
import hashlib
import logging
import json
import jsonschema
import numpy
import os
from pprint import pformat
import re
import requests
from cachecontrol import CacheControl
import six
from six.moves.urllib.parse import urljoin, urlparse, urlunparse

LOGGER = logging.getLogger(__name__)

ENCODED_CONTEXT = {
    # The None context will get added to the root of the tree and will
    # provide common defaults.
    None: {
        # terms in multiple encoded objects
        'award': {'@type': '@id'},
        'dataset': {'@type': '@id'},
        'description': 'rdf:description',
        'documents': {'@type': '@id'},
        'experiment': {'@type': '@id'},
        'href': {'@type': '@id'},
        'lab': {'@type': '@id'},
        'library': {'@type': '@id'},
        'pi': {'@type': '@id'},
        'platform': {'@type': '@id'},
        'replicates': {'@type': '@id'},
        'submitted_by': {'@type': '@id'},
        'url': {'@type': '@id'},
    },
    # Identify and markup contained classes.
    # e.g. in the tree there was a sub-dictionary named 'biosample'
    # That dictionary had a term 'biosample_term_id, which is the
    # term that should be used as the @id.
    'Biosample': {
        'biosample_term_id': {'@type': '@id'},
    },
    'Experiment': {
        "assay_term_id": {"@type": "@id"},
        "files": {"@type": "@id"},
        "original_files": {"@type": "@id"},
    },
    # I tried to use the JSON-LD mapping capabilities to convert the lab
    # contact information into a vcard record, but the encoded model
    # didn't lend itself well to the vcard schema
    #'lab': {
    #    "address1": "vcard:street-address",
    #    "address2": "vcard:street-address",
    #    "city": "vcard:locality",
    #    "state": "vcard:region",
    #    "country": "vcard:country"
    #},
    'Library': {
        'nucleic_acid_term_id': {'@type': '@id'}
    }
}

#FIXME: this needs to be initialized from rdfns
ENCODED_NAMESPACES = {
    # JSON-LD lets you define namespaces so you can used the shorted url syntax.
    # (instead of http://www.w3.org/2000/01/rdf-schema#label you can do
    # rdfs:label)
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "dc": "htp://purl.org/dc/elements/1.1/",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "vcard": "http://www.w3.org/2006/vcard/ns#",

    # for some namespaces I made a best guess for the ontology root.
    "EFO": "http://www.ebi.ac.uk/efo/",  # EFO ontology
    "OBO": "http://purl.obolibrary.org/obo/",  # OBO ontology
    "OBI": "http://purl.obolibrary.org/obo/OBI_",  # Ontology for Biomedical Investigations
    # OBI: available from http://svn.code.sf.net/p/obi/code/releases/2012-07-01/merged/merged-obi-comments.owl
    "SO": "http://purl.obolibrary.org/obo/SO_",  # Sequence ontology
    # SO: available from http://www.berkeleybop.org/ontologies/so.owl
    # NTR: New Term Request space for DCC to implement new ontology terms

}

ENCODED_SCHEMA_ROOT = '/profiles/'

COLLECTION_TO_TYPE = {
    '/annotations/': 'Annotation',
    '/award/': 'Award',
    '/biosamples/': 'Biosample',
    '/datasets/': 'Dataset',
    '/documents/': 'Document',
    '/experiments/': 'Experiment',
    '/labs/': 'Lab',
    '/libraries/': 'Library',
    '/organisms/': 'Organism',
    '/replicates/': 'Replicate',
    '/files/': 'File',
}

TYPE_TO_COLLECTION = {COLLECTION_TO_TYPE[k]: k for k in COLLECTION_TO_TYPE}


class ENCODED:
    '''Programatic access encoded, the software powering ENCODE3's submit site.
    '''
    def __init__(self, server, contexts=None, namespaces=None):
        self.server = server
        self.scheme = 'https'
        self._session = requests.session()
        self._cached_session = CacheControl(self._session)
        self.username = None
        self.password = None
        self._user = None
        self.contexts = contexts if contexts else ENCODED_CONTEXT
        self.namespaces = namespaces if namespaces else ENCODED_NAMESPACES
        self.json_headers = {'content-type': 'application/json', 'accept': 'application/json'}
        self.schemas = {}

    @property
    def auth(self):
        return (self.username, self.password)

    def load_netrc(self):
        import netrc
        session = netrc.netrc()
        authenticators = session.authenticators(self.server)
        if authenticators:
            self.username = authenticators[0]
            self.password = authenticators[2]

    def add_jsonld_context(self, tree, default_base):
        """Add contexts to various objects in the tree.

        tree is a json tree returned from the DCC's encoded database.
        contexts is a dictionary of dictionaries containing contexts
                for the various  possible encoded classes.
        base, if supplied allows setting the base url that relative
            urls will be resolved against.
        """
        self.add_jsonld_child_context(tree, default_base)
        self.add_jsonld_namespaces(tree['@context'])

    def add_jsonld_child_context(self, obj, default_base):
        '''Add JSON-LD context to the encoded JSON.

        This is recursive because some of the IDs were relative URLs
        and I needed a way to properly compute a the correct base URL.
        '''
        # pretend strings aren't iterable
        if isinstance(obj, six.string_types):
            return

        # recurse on container types
        if isinstance(obj, collections.Sequence):
            # how should I update lists?
            for v in obj:
                self.add_jsonld_child_context(v, default_base)
            return

        if isinstance(obj, collections.Mapping):
            for v in obj.values():
                self.add_jsonld_child_context(v, default_base)

        # we have an object. attach a context to it.
        if self._is_encoded_object(obj):
            context = self.create_jsonld_context(obj, default_base)
            if len(context) > 0:
                # this is a total hack for relese 33 of
                # encoded. They changed their model and
                # i'm not sure what to do about it.
                if obj.get('@context') == '/terms/':
                    del obj['@context']
                obj.setdefault('@context', {}).update(context)

    def add_jsonld_namespaces(self, context):
        '''Add shortcut namespaces to a context

        Only needs to be run on the top-most context
        '''
        context.update(self.namespaces)

    def create_jsonld_context(self, obj, default_base):
        '''Synthesize the context for a encoded type

        self.contexts[None] = default context attributes added to any type
        self.contexts[type] = context attributes for this type.
        '''
        obj_type = self.get_object_type(obj)
        context = {'@base': urljoin(default_base, obj['@id']),
                   '@vocab': self.get_schema_url(obj_type)}
        # add in defaults
        context.update(self.contexts[None])
        for t in obj['@type']:
            if t in self.contexts:
                context.update(self.contexts[t])
        return context

    def get_json(self, obj_id, **kwargs):
        '''GET an ENCODE object as JSON and return as dict

        Uses prepare_url to allow url short-cuts
        if no keyword arguments are specified it will default to adding limit=all
        Alternative keyword arguments can be passed in and will be sent to the host.

        Known keywords are:
          limit - (integer or 'all') how many records to return, all for all of them
          embed - (bool) if true expands linking ids into their associated object.
          format - text/html or application/json
        '''
        if len(kwargs) == 0:
            kwargs['limit'] = 'all'

        response = self.get_response(obj_id, **kwargs)
        data = response.json()
        response.close()
        return data

    def get_jsonld(self, obj_id, **kwargs):
        '''Get ENCODE object as JSONLD annotated with classses contexts

        see get_json for documentation about what keywords can be passed.
        '''
        url = self.prepare_url(obj_id)
        json = self.get_json(obj_id, **kwargs)
        self.add_jsonld_context(json, url)
        return json

    def get_object_type(self, obj):
        """Return type for a encoded object
        """
        obj_type = obj.get('@type')
        if not obj_type:
            raise ValueError('None type')
        if isinstance(obj_type, six.string_types):
            raise ValueError('@type should be a list, not a string')
        if not isinstance(obj_type, collections.Sequence):
            raise ValueError('@type is not a sequence')
        return obj_type[0]

    def get_response(self, fragment, **kwargs):
        '''GET an ENCODED url and return the requests request

        Uses prepare_url to allow url short-cuts
        if no keyword arguments are specified it will default to adding limit=all
        Alternative keyword arguments can be passed in and will be sent to the host.

        Known keywords are:
          limit - (integer or 'all') how many records to return, all for all of them
          embed - (bool) if true expands linking ids into their associated object.
          format - text/html or application/json
        '''
        url = self.prepare_url(fragment)
        LOGGER.info('requesting url: {}'.format(url))

        # do the request
        LOGGER.debug('username: %s, password: %s', self.username, self.password)
        arguments = {}
        if self.username and self.password:
            arguments['auth'] = self.auth

        if 'stream' in kwargs:
            arguments['stream'] = kwargs['stream']
            del kwargs['stream']

        response = self._cached_session.get(
            url, headers=self.json_headers, params=kwargs, **arguments)
        if not response.status_code == requests.codes.ok:
            LOGGER.error("Error http status: {}".format(response.status_code))
            response.raise_for_status()

        return response

    def get_schema_url(self, object_type):
        """Create the ENCODED jsonschema url.

        Return the ENCODED object schema url be either
        object type name or the collection name one posts to.

        For example
           server.get_schema_url('experiment') and
           server.get_schema_url('/experiments/') both resolve to
           SERVER/profiles/experiment.json

        Arguments:
           object_type (str): either ENCODED object name or collection

        Returns:
           Schema URL
        """
        object_type = COLLECTION_TO_TYPE.get(object_type, object_type).lower()

        return self.prepare_url(ENCODED_SCHEMA_ROOT + object_type + '.json') + '#'

    def get_accession_name(self, collection):
        """Lookup common object accession name given a collection name.

        This is used by the sheet parsing code to know what column the
        objects accession is in.
        """
        collection_to_accession_name = {
            '/annotations/': 'annotation_accession',
            '/biosamples/': 'biosample_accession',
            '/experiments/': 'experiment_accession',
            '/files/': 'file_accession',
            '/libraries/': 'library_accession',
            '/replicates/': 'uuid',
        }

        accession_name = collection_to_accession_name.get(collection, None)
        if accession_name is None:
            raise RuntimeError("Update list of collection to accession names for %s",
                               collection)

        return accession_name

    def _is_encoded_object(self, obj):
        '''Test to see if an object is a JSON-LD object

        Some of the nested dictionaries lack the @id or @type
        information necessary to convert them.
        '''
        if not isinstance(obj, collections.Iterable):
            return False

        if '@id' in obj and '@type' in obj:
            return True
        return False

    def patch_json(self, obj_id, changes):
        """Given a dictionary of changes push them as a HTTP patch request
        """
        url = self.prepare_url(obj_id)
        LOGGER.info('PATCHing to %s', url)
        payload = json.dumps(changes)
        response = requests.patch(url, auth=self.auth, headers=self.json_headers, data=payload)
        if response.status_code != requests.codes.ok:
            LOGGER.error("Error http status: {}".format(response.status_code))
            LOGGER.error("Response: %s", response.text)
            response.raise_for_status()
        return response.json()

    def put_json(self, obj_id, new_object):
        url = self.prepare_url(obj_id)
        LOGGER.info('PUTing to %s', url)
        payload = json.dumps(new_object)
        response = requests.put(url, auth=self.auth, headers=self.json_headers, data=payload)
        if response.status_code != requests.codes.created:
            LOGGER.error("Error http status: {}".format(response.status_code))
            response.raise_for_status()
        return response.json()

    def post_json(self, collection_id, new_object):
        url = self.prepare_url(collection_id)
        LOGGER.info('POSTing to %s', url)
        payload = json.dumps(new_object)

        response = requests.post(url, auth=self.auth, headers=self.json_headers, data=payload)
        if response.status_code != requests.codes.created:
            LOGGER.error("http status: {}".format(response.status_code))
            LOGGER.error("message: {}".format(response.content))
            response.raise_for_status()
        return response.json()

    def post_sheet(self, collection, sheet, dry_run=True, verbose=False):
        """Create new ENCODED objects using metadata encoded in pandas DataFrame

        The DataFrame column names need to encode the attribute names,
        and in some cases also include some additional type information.
        (see TypedColumnParser)

        Arguments:
           collection (str): name of collection to create new objects in
           sheet (pandas.DataFrame): DataFrame with objects to create,
               assuming the appropriate accession number is empty.
               additional the accession number and uuid is updated if the object
               is created.
           dry_run (bool): whether or not to skip the code to post the objects
           verbose (bool): print the http responses.

        Returns:
           list of created objects.

        Raises:
           jsonschema.ValidationError if the object doesn't validate against
              the encoded jsonschema.
        """
        accession_name = self.get_accession_name(collection)

        to_create = self.prepare_objects_from_sheet(collection, sheet)

        created = []
        accessions = []
        uuids = []
        for i, new_object in to_create:
            if new_object:
                accession = new_object.get('accession')
                uuid = new_object.get('uuid')
                description = new_object.get('description')

                posted_object = self.post_object_from_row(
                    collection, i, new_object, dry_run, verbose
                )
                created.append(posted_object)

                if posted_object:
                    accession = posted_object.get('accession')
                    uuid = posted_object.get('uuid')
                    description = posted_object.get('description')

                if description is None:
                    description = new_object.get('aliases')

                accessions.append(accession)
                uuids.append(uuid)

                LOGGER.info('row {} ({}) -> {}'.format(
                    (i+2), description, accession))
                # +2 comes from python row index + 1 to convert to
                # one based indexing + 1 to account for
                # row removed by header parsing
            else:
                accessions.append(numpy.nan)
                uuids.append(numpy.nan)

        if accession_name in sheet.columns:
            sheet[accession_name] = accessions
        if 'uuid' in sheet.columns:
            sheet['uuid'] = uuids

        return created

    def prepare_objects_from_sheet(self, collection, sheet):
        accession_name = self.get_accession_name(collection)
        to_create = []
        for i, row in sheet.iterrows():
            new_object = {}
            for name, value in row.items():
                if pandas.notnull(value):
                    name, value = typed_column_parser(name, value)
                    if name is None:
                        continue
                    new_object[name] = value

            if new_object and new_object.get(accession_name) is None:
                try:
                    self.validate(new_object, collection)
                except jsonschema.ValidationError as e:
                    LOGGER.error("Validation error row %s", i)
                    raise e
                to_create.append((i, new_object))

            else:
                to_create.append((i, None))

        return to_create

    def post_object_from_row(self, collection, i, new_object,
                             dry_run=True, verbose=True):
        accession_name = self.get_accession_name(collection)

        if not dry_run:
            response = self.post_json(collection, new_object)
            if verbose:
                print("Reponse {}".format(response))

            obj = response['@graph'][0]

            accession = obj.get(accession_name)
            if not accession:
                accession = obj.get('uuid')

            print("row {} created: {}".format(i, accession))
            return obj
        else:
            new_object[accession_name] = 'would create'
            return new_object

    def prepare_url(self, request_url):
        '''This attempts to provide some convienence for accessing a URL

        Given a url fragment it will default to :
        * requests over http
        * requests to self.server

        This allows fairly flexible urls. e.g.

        prepare_url('/experiments/ENCSR000AEG')
        prepare_url('submit.encodedcc.org/experiments/ENCSR000AEG')
        prepare_url('http://submit.encodedcc.org/experiments/ENCSR000AEG?limit=all')

        should all return the same url
        '''
        # clean up potentially messy urls
        url = urlparse(request_url)._asdict()
        if not url['scheme']:
            url['scheme'] = self.scheme
        if not url['netloc']:
            url['netloc'] = self.server
        url = urlunparse(url.values())
        return url

    def search_jsonld(self, **kwargs):
        '''Send search request to ENCODED

        to do a general search do
            searchTerm=term
        '''
        url = self.prepare_url('/search/')
        result = self.get_json(url, **kwargs)
        self.convert_search_to_jsonld(result)
        return result

    def convert_search_to_jsonld(self, result):
        '''Add the context to search result

        Also remove hard to handle nested attributes
          e.g. remove object.term when we have no id
        '''
        graph = result['@graph']
        for i, obj in enumerate(graph):
            # suppress nested attributes
            graph[i] = {k: v for k, v in obj.items() if '.' not in k}

        self.add_jsonld_context(result, self.prepare_url(result['@id']))
        return result

    def validate(self, obj, object_type=None):
        """Validate an object against the ENCODED schema

        Args:
            obj (dictionary): object attributes to be submitted to encoded
            object_type (string): ENCODED object name.

        Raises:
            ValidationError: if the object does not conform to the schema.
        """
        object_type = object_type if object_type else self.get_object_type(obj)
        schema_url = self.get_schema_url(object_type)
        if not schema_url:
            raise ValueError("Unable to construct schema url")

        if object_type not in self.schemas:
            self.schemas[object_type] = self.get_json(schema_url)
        schema = self.schemas[object_type]
        hidden = obj.copy()
        if '@id' in hidden:
            del hidden['@id']
        if '@type' in hidden:
            del hidden['@type']
        jsonschema.validate(hidden, schema)

        # Additional validation rules passed down from the DCC for our grant
        assay_term_name = hidden.get('assay_term_name')
        if assay_term_name is not None:
            if assay_term_name.lower() == 'rna-seq':
                if assay_term_name != 'RNA-seq':
                    raise jsonschema.ValidationError('Incorrect capitialization of RNA-seq')

        species = hidden.get('species')
        if species == '/organisms/human/':
            model_age_terms = ['model_organism_age', 'model_organism_age_units']
            for term in model_age_terms:
                if term in obj:
                    raise jsonschema.ValidationError('model age terms not needed in human')

    @property
    def user(self):
        """Return my user object

        The programatic API uses an access code, which is different
        from the user ID
        """
        if self._user is None:
            if self.username is None:
                return None

            access_key = self.get_json('/access_key/' + self.username)
            if access_key is None:
                return None

            self._user = self.get_json(access_key['user'])

        return self._user


class TypedColumnParser(object):
    @staticmethod
    def parse_sheet_array_type(value):
        """Helper function to parse :array columns in sheet
        """
        return re.split(',\s*', value)

    @staticmethod
    def parse_sheet_integer_type(value):
        """Helper function to parse :integer columns in sheet
        """
        return int(value)

    @staticmethod
    def parse_sheet_boolean_type(value):
        """Helper function to parse :boolean columns in sheet
        """
        return bool(value)

    @staticmethod
    def parse_sheet_timestamp_type(value):
        """Helper function to parse :date columns in sheet
        """
        if isinstance(value, str):
            return value
        return value.strftime('%Y-%m-%d')

    @staticmethod
    def parse_sheet_string_type(value):
        """Helper function to parse :string columns in sheet (the default)
        """
        return str(value)

    def __getitem__(self, name):
        parser = {
            'array': self.parse_sheet_array_type,
            'boolean': self.parse_sheet_boolean_type,
            'integer': self.parse_sheet_integer_type,
            'date': self.parse_sheet_timestamp_type,
            'string': self.parse_sheet_string_type
        }.get(name)
        if parser:
            return parser
        else:
            raise RuntimeError("unrecognized column type")

    def __call__(self, header, value):
        header = header.split(':')
        column_type = 'string'
        if len(header) > 1:
            if header[1] == 'skip':
                return None, None
            else:
                column_type = header[1]
        return header[0], self[column_type](value)

typed_column_parser = TypedColumnParser()

class Document(object):
    """Helper class for registering documents

    Usage:
    lysis_uuid = 'f0cc5a7f-96a5-4970-9f46-317cc8e2d6a4'
    lysis = Document(url_to_pdf, 'extraction protocol', 'Lysis Protocol')
    lysis.create_if_needed(server, lysis_uuid)
    """
    award = 'U54HG006998'
    lab = '/labs/barbara-wold'

    def __init__(self, url, document_type, description, aliases=None):
        self.url = url
        self.filename = os.path.basename(url)
        self.document_type = document_type
        self.description = description

        self.references = []
        self.aliases = None
        if aliases:
            if isinstance(aliases, list):
                self.aliases = aliases
            else:
                raise ValueError("Aliases needs to be a list")
        self.content_type = None
        self.document = None
        self.md5sum = None
        self.urls = None
        self.uuid = None

        self.get_document()

    def get_document(self):
        if os.path.exists(self.url):
            with open(self.url, 'rb') as instream:
                assert self.url.endswith('pdf')
                self.content_type = 'application/pdf'
                self.document = instream.read()
                self.md5sum = hashlib.md5(self.document)
        else:
            req = self._cached_session.get(self.url)
            if req.status_code == 200:
                self.content_type = req.headers['content-type']
                self.document = req.content
                self.md5sum = hashlib.md5(self.document)
                self.urls = [self.url]

    def create_payload(self):
        document_payload = {
            'attachment': {
              'download': self.filename,
              'type': self.content_type,
              'href': 'data:'+self.content_type+';base64,' + base64.b64encode(self.document).decode('ascii'),
              'md5sum': self.md5sum.hexdigest()
            },
            'document_type': self.document_type,
            'description': self.description,
            'award': self.award,
            'lab': self.lab,
        }
        if self.aliases:
            document_payload['aliases'] = self.aliases
        if self.references:
            document_payload['references'] = self.references
        if self.urls:
            document_payload['urls'] = self.urls

        return document_payload

    def post(self, server):
        document_payload = self.create_payload()
        server.validate(document_payload, 'document')
        return server.post_json('/documents/', document_payload)

    def save(self, filename):
        payload = self.create_payload()
        with open(filename, 'w') as outstream:
            outstream.write(pformat(payload))

    def create_if_needed(self, server, uuid):
        self.uuid = uuid
        if uuid is None:
            return self.post(server)
        else:
            return server.get_json(uuid, embed=False)


if __name__ == '__main__':
    # try it
    from rdflib import Graph
    model = Graph()
    logging.basicConfig(level=logging.DEBUG)
    encoded = ENCODED('test.encodedcc.org')
    encoded.load_netrc()
    body = encoded.get_jsonld('/experiments/ENCSR000AEC/')
    model.parse(body)
    print(model.serialize(format='turtle'))
