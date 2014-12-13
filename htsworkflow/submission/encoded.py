"""Interface with encoded software for ENCODE3 data submission & warehouse

This allows retrieving blocks
"""


from __future__ import print_function
import collections
import logging
import json
import jsonschema
import requests
import types
from urlparse import urljoin, urlparse, urlunparse

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
    'biosample': {
        'biosample_term_id': {'@type': '@id'},
    },
    'experiment': {
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
    'library': {
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


class ENCODED:
    '''Programatic access encoded, the software powering ENCODE3's submit site.
    '''
    def __init__(self, server, contexts=None, namespaces=None):
        self.server = server
        self.scheme = 'https'
        self.username = None
        self.password = None
        self.contexts = contexts if contexts else ENCODED_CONTEXT
        self.namespaces = namespaces if namespaces else ENCODED_NAMESPACES
        self.json_headers = {'content-type': 'application/json', 'accept': 'application/json'}
        self.schemas = {}

    def get_auth(self):
        return (self.username, self.password)
    auth = property(get_auth)

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
        if type(obj) in types.StringTypes:
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
        context = {'@base': urljoin(default_base, obj['@id']),
                   '@vocab': self.get_schema_url(obj)}
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

        url = self.prepare_url(obj_id)
        LOGGER.info('requesting url: {}'.format(url))

        # do the request

        LOGGER.debug('username: %s, password: %s', self.username, self.password)
        response = requests.get(url, auth=self.auth, headers=self.json_headers, params=kwargs)
        if not response.status_code == requests.codes.ok:
            LOGGER.error("Error http status: {}".format(response.status_code))
            response.raise_for_status()
        return response.json()

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
        if type(obj_type) in types.StringTypes:
            raise ValueError('@type should be a list, not a string')
        if not isinstance(obj_type, collections.Sequence):
            raise ValueError('@type is not a sequence')
        return obj_type[0]

    def get_schema_url(self, obj):
        obj_type = self.get_object_type(obj)
        if obj_type:
            return self.prepare_url(ENCODED_SCHEMA_ROOT + obj_type + '.json') + '#'

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
            LOGGER.error("Error http status: {}".format(response.status_code))
            response.raise_for_status()
        return response.json()

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

    def search_jsonld(self, term, **kwargs):
        '''Send search request to ENCODED
        '''
        url = self.prepare_url('/search/')
        result = self.get_json(url, searchTerm=term, **kwargs)
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

    def validate(self, obj):
        obj_type = self.get_object_type(obj)
        schema_url = self.get_schema_url(obj)
        if not schema_url:
            raise ValueError("Unable to construct schema url")

        schema = self.schemas.setdefault(obj_type, self.get_json(schema_url))
        hidden = obj.copy()
        del hidden['@id']
        del hidden['@type']
        jsonschema.validate(hidden, schema)


if __name__ == '__main__':
    # try it
    from htsworkflow.util.rdfhelp import get_model, dump_model
    from htsworkflow.util.rdfjsonld import load_into_model
    from pprint import pprint
    model = get_model()
    logging.basicConfig(level=logging.DEBUG)
    encoded = ENCODED('test.encodedcc.org')
    encoded.load_netrc()
    body = encoded.get_jsonld('/experiments/ENCSR000AEC/')
    pprint(body)
    load_into_model(model, body)
    #dump_model(model)
