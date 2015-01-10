import datetime

import factory
from factory.django import DjangoModelFactory
from . import models
from samples.samples_factory import LibraryFactory


class ClusterStationFactory(DjangoModelFactory):
    class Meta:
        model = models.ClusterStation

    name = factory.Sequence(lambda x: 'cluster station %d' % (x,))
    isdefault = True


class SequencerFactory(DjangoModelFactory):
    class Meta:
        model = models.Sequencer

    name = factory.Sequence(lambda x: 'sequencer %d' % (x,))
    instrument_name = factory.Sequence(lambda x: 'instrument name %d' % (x,))
    serial_number = factory.Sequence(lambda x: 'squencer serial number %d' % (x,))
    model = 'HiSeq 1'
    active = True
    isdefault = True
    comment = 'example sequencer'


class FlowCellFactory(DjangoModelFactory):
    class Meta:
        model = models.FlowCell

    flowcell_id = '1234AAAAXX'
    run_date = datetime.datetime.now()
    advanced_run = False
    paired_end = True
    read_length = 100
    control_lane = 0
    cluster_station = factory.SubFactory(ClusterStationFactory)
    sequencer = factory.SubFactory(SequencerFactory)
    notes = 'flowcell notes'


class LaneFactory(DjangoModelFactory):
    class Meta:
        model = models.Lane

    flowcell = factory.SubFactory(FlowCellFactory)
    lane_number = 1
    library = factory.SubFactory(LibraryFactory)
    pM = 1.2
    cluster_estimate = 12345
    status = 2
    comment = 'lane comment'


class DataRunFactory(DjangoModelFactory):
    class Meta:
        model = models.DataRun

    flowcell = factory.SubFactory(FlowCellFactory)
    runfolder_name = '102030_UAW-EAS22_1234AAAAXX'
    result_dir = runfolder_name + '/Unaligned'
    run_start_time = datetime.datetime.now()
    cycle_start = 1
    cycle_stop = 101
    run_status = 2
    image_software = 'RTA'
    image_version = '1.1'
    basecall_software = 'RTA'
    basecall_version = '2.2'
    alignment_software = 'eland'
    alignment_version = '2.2'
    comment = 'comment'


class FileTypeFactory(DjangoModelFactory):
    class Meta:
        model = models.FileType

    name = 'file type'
    mimetype = 'application/file'
    regex = '.file$'

