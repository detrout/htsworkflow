from __future__ import absolute_import, print_function, unicode_literals

import datetime
import glob
import logging
import os
import re
import uuid

from django.conf import settings
from django.core import urlresolvers
from django.utils import timezone
from django.db import models
from django.db.models.signals import pre_save

from samples.models import Library, HTSUser
from htsworkflow.util.conversion import parse_flowcell_id
from htsworkflow.pipelines import runfolder

import pytz

LOGGER = logging.getLogger(__name__)
default_pM = 5
try:
    default_pM = int(settings.DEFAULT_PM)
except AttributeError as e:
    LOGGER.error("invalid value for default_pm")

# how many days to wait before trying to re-import a runfolder
RESCAN_DELAY = 1
try:
    RESCAN_DELAY = int(settings.RESCAN_DELAY)
except (ValueError, AttributeError):
    LOGGER.error("Missing or invalid settings.RESCAN_DELAY, "\
                 "defaulting to %s" % (RESCAN_DELAY,))

RUN_STATUS_CHOICES = (
    (0, 'Sequencer running'),  # Solexa Data Pipeline Not Yet Started'),
    (1, 'Data Pipeline Started'),
    (2, 'Data Pipeline Interrupted'),
    (3, 'Data Pipeline Finished'),
    (4, 'Collect Results Started'),
    (5, 'Collect Results Finished'),
    (6, 'QC Started'),
    (7, 'QC Finished'),
    (255, 'DONE'),
  )
RUN_STATUS_REVERSE_MAP = dict(((v, k) for k, v in RUN_STATUS_CHOICES))


class ClusterStation(models.Model):
    """List of cluster stations"""
    name = models.CharField(max_length=50, unique=True)
    isdefault = models.BooleanField(default=False, null=False)

    class Meta:
        ordering = ["-isdefault", "name"]

    def __str__(self):
        return str(self.name)

    @staticmethod
    def update_isdefault(sender, instance, **kwargs):
        """Clear default if needed
        """
        if instance.isdefault:
            for c in ClusterStation.objects.filter(isdefault=True).all():
                if c.id != instance.id:
                    c.isdefault = False
                    c.save()

def cluster_station_default():
    d = ClusterStation.objects.filter(isdefault=True).all()
    if len(d) > 0:
        return d[0]
    d = ClusterStation.objects.order_by('-id').all()
    if len(d) > 0:
        return d[0]
    return None

pre_save.connect(ClusterStation.update_isdefault, sender=ClusterStation)

class Sequencer(models.Model):
    """Sequencers we've owned
    """
    name = models.CharField(max_length=50, db_index=True)
    instrument_name = models.CharField(max_length=50, db_index=True)
    serial_number = models.CharField(max_length=50, db_index=True)
    model = models.CharField(max_length=255)
    active = models.BooleanField(default=True, null=False)
    isdefault = models.BooleanField(default=False, null=False)
    comment = models.CharField(max_length=255)

    class Meta:
        ordering = ["-isdefault", "-active", "name"]

    def __str__(self):
        name = [str(self.name)]
        if self.instrument_name is not None:
            name.append("(%s)" % (str(self.instrument_name),))
        return " ".join(name)

    @models.permalink
    def get_absolute_url(self):
        return ('experiments.views.sequencer',
                [self.id])

    @staticmethod
    def update_isdefault(sender, instance, **kwargs):
        """Clear default if needed
        """
        if instance.isdefault:
            for s in Sequencer.objects.filter(isdefault=True).all():
                if s.id != instance.id:
                    s.isdefault = False
                    s.save()

pre_save.connect(Sequencer.update_isdefault, sender=Sequencer)

def sequencer_default():
    d = Sequencer.objects.filter(isdefault=True).all()
    if len(d) > 0:
        return d[0]
    d = Sequencer.objects.order_by('active', '-id').all()
    if len(d) > 0:
        return d[0]
    return None


class FlowCell(models.Model):
    flowcell_id = models.CharField(max_length=20, unique=True, db_index=True)
    run_date = models.DateTimeField()
    advanced_run = models.BooleanField(default=False)
    paired_end = models.BooleanField(default=False)
    read_length = models.IntegerField(default=32)  # Stanford is currenlty 25
    control_lane = models.IntegerField(choices=[(1, 1),
                                                (2, 2),
                                                (3, 3),
                                                (4, 4),
                                                (5, 5),
                                                (6, 6),
                                                (7, 7),
                                                (8, 8),
                                                (0, 'All Lanes')],
                                       null=True,
                                       blank=True)

    cluster_station = models.ForeignKey(ClusterStation,
                                        default=cluster_station_default)
    sequencer = models.ForeignKey(Sequencer, default=sequencer_default)

    notes = models.TextField(blank=True)

    def __str__(self):
        return str(self.flowcell_id)

    def Lanes(self):
        html = ['<table>']
        for lane in self.lane_set.order_by('lane_number'):
            cluster_estimate = lane.cluster_estimate
            if cluster_estimate is not None:
                cluster_estimate = "%s k" % ((int(cluster_estimate) / 1000), )
            else:
                cluster_estimate = 'None'
            library_id = lane.library_id
            library = lane.library
            element = '<tr><td>%d</td>'\
                      '<td><a href="%s">%s</a></td><td>%s</td></tr>'
            html.append(element % (lane.lane_number,
                                   library.get_admin_url(),
                                   library,
                                   cluster_estimate))
        html.append('</table>')
        return "\n".join(html)
    Lanes.allow_tags = True

    class Meta:
        ordering = ["-run_date"]

    def get_admin_url(self):
        # that's the django way... except it didn't work
        return urlresolvers.reverse('admin:experiments_flowcell_change',
                                    args=(self.id,))

    def flowcell_type(self):
        """Convert our boolean 'is paired' flag to a name
        """
        if self.paired_end:
            return "Paired"
        else:
            return "Single"

    @models.permalink
    def get_absolute_url(self):
        flowcell_id, status = parse_flowcell_id(self.flowcell_id)
        return ('experiments.views.flowcell_detail',
                [str(flowcell_id)])

    def get_raw_data_directory(self):
        """Return location of where the raw data is stored"""
        flowcell_id, status = parse_flowcell_id(self.flowcell_id)

        return os.path.join(settings.RESULT_HOME_DIR, flowcell_id)

    def update_sequencing_runs(self):
        result_root = self.get_raw_data_directory()
        LOGGER.debug("Update data runs flowcell root: %s" % (result_root,))
        if result_root is None:
            return

        result_home_dir = os.path.join(settings.RESULT_HOME_DIR, '')
        run_xml_re = re.compile(glob.fnmatch.translate('run*.xml'))

        result_dirs = []
        for dirpath, dirnames, filenames in os.walk(result_root):
            for filename in filenames:
                if run_xml_re.match(filename):
                    # we have a run directory
                    relative_pathname = get_relative_pathname(dirpath)
                    self.import_sequencing_run(relative_pathname, filename)

    def import_sequencing_run(self, relative_pathname, run_xml_name, force=False):
        """Given a result directory import files"""
        now = timezone.now()
        run_dir = get_absolute_pathname(relative_pathname)
        run_xml_path = os.path.join(run_dir, run_xml_name)

        runs = SequencingRun.objects.filter(result_dir = relative_pathname)
        if len(runs) == 0:
            run = SequencingRun()
            created = True
        elif len(runs) > 1:
            raise RuntimeError("Too many data runs for %s" % (
                relative_pathname,))
        else:
            run = runs[0]
            created = False

        if created or force or (now-run.last_update_time).days > RESCAN_DELAY:
            LOGGER.debug("Importing run from %s" % (relative_pathname,))
            run_xml_data = runfolder.load_pipeline_run_xml(run_xml_path)
            run.flowcell = self
            run.status = RUN_STATUS_REVERSE_MAP['DONE']
            run.result_dir = relative_pathname
            run.runfolder_name = run_xml_data.runfolder_name
            run.cycle_start = run_xml_data.image_analysis.start
            run.cycle_stop = run_xml_data.image_analysis.stop
            naive_run_start_time = datetime.datetime.fromordinal(run_xml_data.image_analysis.date.toordinal())
            run.run_start_time = pytz.timezone(settings.TIME_ZONE).localize(naive_run_start_time)
            run.image_software = run_xml_data.image_analysis.software
            run.image_version = run_xml_data.image_analysis.version
            run.basecall_software = run_xml_data.bustard.software
            run.basecall_version = run_xml_data.bustard.version
            # we're frequently not running alignments
            if run_xml_data.gerald:
                run.alignment_software = run_xml_data.gerald.software
                run.alignment_version = run_xml_data.gerald.version

            run.last_update_time = timezone.now()
            run.save()

            run.update_result_files()


# FIXME: should we automatically update sequencing run?
#        Or should we expect someone to call update_sequencing_runs?
#def update_flowcell_sequencingruns(sender, instance, *args, **kwargs):
#    """Update our sequencing rungs
#    """
#    if not os.path.exists(settings.RESULT_HOME_DIR):
#       return
#
#    instance.update_sequencing_runs()
#post_init.connect(update_flowcell_sequencingruns, sender=FlowCell)

LANE_STATUS_CODES = [(0, 'Failed'),
                     (1, 'Marginal'),
                     (2, 'Good'),
                     (100, 'Not run')]
LANE_STATUS_MAP = dict((int(k), v) for k, v in LANE_STATUS_CODES)
LANE_STATUS_MAP[None] = "Unknown"


def is_valid_lane(value):
    if value >= 1 and value <= 8:
        return True
    else:
        return False


class Lane(models.Model):
    flowcell = models.ForeignKey(FlowCell)
    lane_number = models.IntegerField()
    library = models.ForeignKey(Library)
    pM = models.DecimalField(max_digits=5,
                             decimal_places=2,
                             blank=False,
                             null=False,
                             default=default_pM)
    cluster_estimate = models.IntegerField(blank=True, null=True)
    status = models.IntegerField(choices=LANE_STATUS_CODES,
                                 null=True,
                                 blank=True)
    comment = models.TextField(null=True, blank=True)

    @models.permalink
    def get_absolute_url(self):
        return ('experiments.views.flowcell_lane_detail',
                [str(self.id)])

    def __str__(self):
        return self.flowcell.flowcell_id + ':' + str(self.lane_number)


class SequencingRun(models.Model):
    flowcell = models.ForeignKey(FlowCell, verbose_name="Flowcell Id")
    runfolder_name = models.CharField(max_length=50)
    result_dir = models.CharField(max_length=255)
    last_update_time = models.DateTimeField()
    run_start_time = models.DateTimeField()
    cycle_start = models.IntegerField(null=True, blank=True)
    cycle_stop = models.IntegerField(null=True, blank=True)
    run_status = models.IntegerField(choices=RUN_STATUS_CHOICES,
                                     null=True, blank=True)
    image_software = models.CharField(max_length=50)
    image_version = models.CharField(max_length=50)
    basecall_software = models.CharField(max_length=50)
    basecall_version = models.CharField(max_length=50)
    alignment_software = models.CharField(max_length=50)
    alignment_version = models.CharField(max_length=50)
    comment = models.TextField(blank=True)

    def update_result_files(self):
        abs_result_dir = get_absolute_pathname(self.result_dir)

        for dirname, dirnames, filenames in os.walk(abs_result_dir):
            for filename in filenames:
                pathname = os.path.join(dirname, filename)
                relative_pathname = get_relative_pathname(pathname)
                datafiles = self.datafile_set.filter(
                    sequencing_run=self,
                    relative_pathname=relative_pathname)
                if len(datafiles) > 0:
                    continue

                metadata = find_file_type_metadata_from_filename(filename)
                if metadata is not None:
                    metadata['filename'] = filename
                    newfile = DataFile()
                    newfile.sequencing_run = self
                    newfile.file_type = metadata['file_type']
                    newfile.relative_pathname = relative_pathname

                    lane_number = metadata.get('lane', None)
                    if lane_number is not None:
                        lane = self.flowcell.lane_set.get(
                            lane_number=lane_number)
                        newfile.library = lane.library

                    self.datafile_set.add(newfile)

        self.last_update_time = timezone.now()

    def lane_files(self):
        lanes = {}

        for datafile in self.datafile_set.all():
            metadata = datafile.attributes
            if metadata is not None:
                lane = metadata.get('lane', None)
                if lane is not None:
                    lane_file_set = lanes.setdefault(lane, {})
                    normalized_name = datafile.file_type.normalized_name
                    lane_file_set[normalized_name] = datafile
        return lanes

    def ivc_plots(self, lane):
        ivc_name = ['IVC All', 'IVC Call',
                    'IVC Percent Base', 'IVC Percent All', 'IVC Percent Call']

        plots = {}
        for rel_filename, metadata in self.get_result_files():
            if metadata.file_type.name in ivc_name:
                plots[metadata.file_type.name] = (rel_filename, metadata)


class FileType(models.Model):
    """Represent potential file types

    regex is a pattern used to detect if a filename matches this type
    data run currently assumes that there may be a (?P<lane>) and
    (?P<end>) pattern in the regular expression.
    """
    name = models.CharField(max_length=50)
    mimetype = models.CharField(max_length=50, null=True, blank=True)
    # regular expression from glob.fnmatch.translate
    regex = models.TextField(null=True, blank=True)

    def parse_filename(self, pathname):
        """Does filename match our pattern?

        Returns None if not, or dictionary of match variables if we do.
        """
        path, filename = os.path.split(pathname)
        if len(self.regex) > 0:
            match = re.match(self.regex, filename)
            if match is not None:
                # These are (?P<>) names we know about from our
                # default regexes.
                results = match.groupdict()

                # convert int parameters
                for attribute_name in ['lane', 'end']:
                    value = results.get(attribute_name, None)
                    if value is not None:
                        results[attribute_name] = int(value)

                return results

    def _get_normalized_name(self):
        """Crush data file name into identifier friendly name"""
        return self.name.replace(' ', '_').lower()
    normalized_name = property(_get_normalized_name)

    def __str__(self):
        return self.name


def str_uuid():
    """Helper function to set default UUID in DataFile"""
    return str(uuid.uuid1())


class DataFile(models.Model):
    """Store map from random ID to filename"""
    random_key = models.CharField(max_length=64,
                                  db_index=True,
                                  default=str_uuid)
    sequencing_run = models.ForeignKey(SequencingRun, db_index=True, null=True)
    library = models.ForeignKey(Library, db_index=True, null=True, blank=True)
    file_type = models.ForeignKey(FileType)
    relative_pathname = models.CharField(max_length=255, db_index=True)

    def _get_attributes(self):
        return self.file_type.parse_filename(self.relative_pathname)
    attributes = property(_get_attributes)

    def _get_pathname(self):
        return get_absolute_pathname(self.relative_pathname)
    pathname = property(_get_pathname)

    @models.permalink
    def get_absolute_url(self):
        return ('experiments.views.read_result_file',
                (), {'key': self.random_key})


def find_file_type_metadata_from_filename(pathname):
    path, filename = os.path.split(pathname)
    result = None
    for file_type in FileType.objects.all():
        result = file_type.parse_filename(filename)
        if result is not None:
            result['file_type'] = file_type
            return result

    return None


def get_relative_pathname(abspath):
    """Strip off the result home directory from a path
    """
    result_home_dir = os.path.join(settings.RESULT_HOME_DIR, '')
    relative_pathname = abspath.replace(result_home_dir, '')
    return relative_pathname


def get_absolute_pathname(relative_pathname):
    """Attach relative path to  results home directory"""
    return os.path.join(settings.RESULT_HOME_DIR, relative_pathname)
