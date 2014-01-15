import logging
import os
from pprint import pformat
import string
import re

import RDF

from htsworkflow.submission.submission import Submission

from htsworkflow.util.rdfhelp import \
     fromTypedNode, \
     geoSoftNS, \
     submissionOntology
from htsworkflow.util.url import parse_ssh_url
from htsworkflow.util.ucsc import bigWigInfo

from django.conf import settings
from django.template import Context, loader
from trackhub import default_hub, CompositeTrack, Track, SuperTrack, ViewTrack
from trackhub.track import TRACKTYPES, SubGroupDefinition
from trackhub.helpers import show_rendered_files
from trackhub.upload import upload_track, upload_hub

LOGGER = logging.getLogger(__name__)

class TrackHubSubmission(Submission):
    def __init__(self, name, model, baseurl, baseupload, host):
        """Create a trackhub based submission

        :Parameters:
          - `name`: Name of submission
          - `model`: librdf model reference
          - `baseurl`: web root where trackhub will be hosted
          - `baseupload`: filesystem root where trackhub will be hosted
          - `host`: hostname for library pages.
        """
        super(TrackHubSubmission, self).__init__(name, model, host)
        if baseurl is None:
            raise ValueError("Need a web root to make a track hub")
        self.baseurl = os.path.join(baseurl, self.name)
        if baseupload:
            sshurl = parse_ssh_url(baseupload)
            print sshurl
            self.user = sshurl.user
            self.host = sshurl.host
            self.uploadpath =  sshurl.path
        else:
            self.uploadpath = None

    def make_hub_template(self, result_map):
        samples = []
        for an_analysis in self.analysis_nodes(result_map):
            metadata = self.get_sample_metadata(an_analysis)
            if len(metadata) == 0:
                errmsg = 'No metadata found for {0}'
                LOGGER.error(errmsg.format(str(an_analysis),))
                continue
            elif len(metadata) > 1:
                errmsg = 'Confused there are more than one sample for %s'
                LOGGER.debug(errmsg % (str(an_analysis),))
            metadata = metadata[0]
            samples.append(metadata)

        template = loader.get_template('trackDb.txt')
        context = Context({
            'samples': samples,
        })
        return str(template.render(context))

    def make_hub(self, result_map):
        genome_db = 'hg19'
        hub_url = self.baseurl + '/'
        hub, genomes_file, genome, trackdb = default_hub(
            hub_name=self.name,
            short_label=self.name,
            long_label=self.name,
            email='email',
            genome=genome_db)

        hub.remote_dir = self.uploadpath

        # build higher order track types
        composite = CompositeTrack(
            name=self.sanitize_name(self.name),
            short_label = self.sanitize_name(self.name),
            long_label = str(self.name),
            tracktype="bed 3",
            dragAndDrop='subtracks',
            visibility='full',
        )
        trackdb.add_tracks(composite)

        subgroups = self.add_subgroups(composite)

        view_type = None
        view = None

        for track in self.get_tracks():
            if track['file_type'] not in TRACKTYPES:
                LOGGER.info('Unrecognized file type %s', track['file_type'])
                continue

            view = self.add_new_view_if_needed(composite, view, track)
            track_name = self.make_track_name(track)

            track_subgroup = self.make_track_subgroups(subgroups, track)
            track_type = self.make_track_type(track)

            if 'file_label' in track:
                track_label = self.sanitize_name(track['file_label'])
            else:
                track_label = track_name

            attributes = {
                'name': track_name,
                'tracktype': track_type,
                'url': hub_url + str(track['relative_path']),
                'short_label': str(track['library_id']),
                'long_label': str(track_label),
                'subgroups': track_subgroup,
            }

            LOGGER.debug('track attributes: %s', pformat(attributes))
            newtrack = Track(**attributes)
            view.add_tracks([newtrack])

        results = hub.render()
        if hub.remote_dir:
            LOGGER.info("Uploading to %s @ %s : %s",
                        self.user, self.host, hub.remote_dir)
            upload_hub(hub=hub, host=self.host, user='diane')

    def add_new_view_if_needed(self, composite, view, track):
        """Add new trakkhub view if we've hit a new type of track.

        :Parameters:
          - `composite`: composite track to attach to
          - `view_type`: name of view type
          - `track`: current track record
        """
        current_view_type = str(track['output_type'])
        if not view or current_view_type != view.name:
            attributes = {
                'name': current_view_type,
                'view': current_view_type,
                'visibility': str(track.get('visibility', 'squish')),
                'short_label': current_view_type,
                'tracktype': str(track['file_type'])
            }
            maxHeightPixels = track.get('maxHeightPixels')
            if maxHeightPixels:
                attributes['maxHeightPixels'] = str(maxHeightPixels)
            autoScale = track.get('autoScale')
            if autoScale:
                attributes['autoScale'] = str(autoScale)
            view = ViewTrack(**attributes)
            composite.add_view(view)
            view_type = current_view_type
        return view

    def make_manifest(self, result_map):
        files = []
        for an_analysis in self.analysis_nodes(result_map):
            metadata = self.get_manifest_metadata(an_analysis)
            files.extend(metadata)

        template = loader.get_template('manifest.txt')
        context = Context({
            'files': files
        })
        return str(template.render(context))

    def make_track_name(self, track):
        return '{}_{}_{}'.format(
            track['library_id'],
            track['replicate'],
            track['output_type'],
        )

    def make_track_subgroups(self, subgroups, track):
        track_subgroups = {}
        for k in subgroups:
            if k in track and track[k]:
                value = self.sanitize_name(track[k])
                track_subgroups[k] = value
        return track_subgroups

    def make_track_type(self, track):
        """Further annotate tracktype.

        bigWig files can have additional information. Add it if we can
        """
        track_type = track['file_type']
        if track_type.lower() == 'bigwig':
            # something we can enhance
            info = bigWigInfo(track['relative_path'])
            if info.min is not None and info.max is not None:
                track_type = '{} {} {}'.format(track_type, int(info.min), int(info.max))

        LOGGER.debug("track_type: %s", track_type)
        return str(track_type)

    def add_subgroups(self, composite):
        """Add subgroups to composite track"""
        search = [ ('htswlib:cell_line', 'cell'),
                   ('encode3:rna_type', 'rna_type'),
                   ('encode3:protocol', 'protocol'),
                   ('htswlib:replicate', 'replicate'),
                   ('encode3:library_id', 'library_id'),
                   ('encode3:assay', 'assay'),
                 ]
        subgroups = []
        names = []
        sortorder = []
        dimnames = ('dim{}'.format(x) for x in string.ascii_uppercase)
        dimensions = []
        filtercomposite = []
        for term, name in search:
            definitions = self.make_subgroupdefinition(term, name)
            if definitions:
                subgroups.append(definitions)
                names.append(name)
                sortorder.append("{}=+".format(name))
                d = dimnames.next()
                dimensions.append("{}={}".format(d, name))
                filtercomposite.append("{}=multi".format(d))

        composite.add_subgroups(subgroups)
        composite.add_params(sortOrder=' '.join(sortorder))
        composite.add_params(dimensions=' '.join(dimensions))
        composite.add_params(filterComposite=' '.join(filtercomposite))
        return names


    def make_subgroupdefinition(self, term, name):
        """Subgroup attributes need to be an attribute of the library.
        """
        template = loader.get_template('trackhub_term_values.sparql')
        context = Context({'term': term})
        results = self.execute_query(template, context)
        values = {}
        for row in results:
            value = str(row['name'])
            values[self.sanitize_name(value)] = value

        if values:
            return SubGroupDefinition(
                    name=name,
                    label=name,
                    mapping=values,
            )
        else:
            return None

    def get_tracks(self):
        """Collect information needed to describe trackhub tracks.
        """
        query_template = loader.get_template('trackhub_samples.sparql')

        context = Context({ })

        results = self.execute_query(query_template, context)
        return results

    def sanitize_name(self, name):
        replacements = [('poly-?a\+', 'PolyAplus'),
                        ('poly-?a-', 'PolyAminus'),
                        ('RNA-Seq', 'RNASeq'),
                        ('rna-seq', 'rnaseq'),
                        ('-', '_'),
                        (' ', '_'),
                        ('^0', 'Zero'),
                        ('^1', 'One'),
                        ('^2', 'Two'),
                        ('^3', 'Three'),
                        ('^4', 'Four'),
                        ('^5', 'Five'),
                        ('^6', 'Six'),
                        ('^7', 'Seven'),
                        ('^8', 'Eight'),
                        ('^9', 'Nine'),
                        ]

        for regex, substitution in replacements:
            name = re.sub(regex, substitution, name, flags=re.IGNORECASE)

        return name

    def get_manifest_metadata(self, analysis_node):
        query_template = loader.get_template('trackhub_manifest.sparql')

        context = Context({
            'submission': str(analysis_node.uri),
            'submissionSet': str(self.submissionSetNS[''].uri),
            })
        results = self.execute_query(query_template, context)
        LOGGER.info("scanned %s for results found %s",
                    str(analysis_node), len(results))
        return results
