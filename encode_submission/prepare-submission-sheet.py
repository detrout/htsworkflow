#!/usr/bin/env python
# coding: utf-8
from argparse import ArgumentParser
import logging
import pandas
import json
from pathlib import Path
import xopen

from woldrnaseq.models import (
    load_library_tables,
    load_experiments,
)
from woldrnaseq.common import (
    find_fastqs_by_glob,
)

from rdflib import Graph


from encoded_client.encoded import ENCODED, DCCValidator

from htsworkflow.util.api import (
    add_auth_options,
    make_auth_from_opts,
    HtswApi,
)
from encoded_client.hashfile import make_md5sum
from encoded_client.rdfhelp import load_into_model


def main(cmdline=None):
    parser = make_parser()
    args = parser.parse_args(cmdline)
    configure_logging(args)

    print("HEY ME")
    print("You didn't test this with fastqs on multiple flowcells or paired end data")

    apidata = make_auth_from_opts(args)
    htsw = HtswApi(args.host, apidata)

    server = ENCODED("www.encodeproject.org")
    server.load_netrc()
    validator = DCCValidator(server)

    award = "UM1HG009443"
    lab = "barbara-wold"

    book = pandas.ExcelFile(args.spreadsheet_file)
    biosample_sheet = book.parse("Biosample")
    library_sheet = book.parse("Library")
    replicate_sheet = book.parse("Replicate")
    experiment_sheet = book.parse("Experiment")

    server.prepare_objects_from_sheet("/biosamples/", biosample_sheet, validator)
    server.prepare_objects_from_sheet("/libraries/", library_sheet, validator)
    server.prepare_objects_from_sheet("/experiments/", experiment_sheet, validator)
    server.prepare_objects_from_sheet("/replicates/", replicate_sheet, validator)

    ff = FlowcellFastqs(htsw, Path("~/proj/flowcells").expanduser())
    fd = FlowcellDetails(htsw)

    file_sheet_order = [
        "uuid",
        "accession",
        "dataset",
        "submitted_file_name",
        "md5sum",
        "run_type",
        "flowcell_details:json",
        "read_length:integer",
        "file_size:integer",
        "file_format",
        "output_type",
        "platform",
        "library_id:skip",
        "replicate",
        "lab",
        "award",
    ]

    file_sheet = []

    for i, row in library_sheet.iterrows():
        library_alias = row["aliases:array"].split(",")[0]
        library_id = library_alias[len("barbara-wold:"):]
        replicate_row = replicate_sheet.set_index("library").loc[library_alias]

        dataset = replicate_row["experiment"]
        biorep = replicate_row["biological_replicate_number:integer"]
        if pandas.isnull(biorep):
            biorep = ""
        else:
            biorep = int(biorep)
        techrep = replicate_row["technical_replicate_number:integer"]

        reads = ff[library_id]
        if 'read_2' in reads:
            run_type = 'paired-ended'
        else:
            run_type = 'single-ended'

        for read in reads:
            for fastq in reads[read]:
                shortened_name = Path(fastq).relative_to(ff.root)
                if shortened_name.exists():
                    md5sum = make_md5sum(str(shortened_name))
                else:
                    md5sum = None

                flowcell_id = shortened_name.parts[0]
                flowcell_details = fd.get_flowcell_details(flowcell_id, library_id)

                flowcell_info = json.dumps([flowcell_details])

                file_sheet.append(
                    {
                        "uuid": None,
                        "accession": None,
                        "dataset": dataset,
                        "submitted_file_name": shortened_name,
                        "md5sum": md5sum,
                        "flowcell_details:json": flowcell_info,
                        "read_length:integer": get_read_length(fastq),
                        "file_format": "fastq",
                        "output_type": "reads",
                        "run_type": run_type,
                        "platform": "/platforms/OBI%3A0002002/",
                        "library_id:skip": row["aliases:array"],
                        "biosample:skip": row["biosample"],
                        "replicate": f"barbara-wold:{library_id}_b{biorep}_t{techrep}",
                        "lab": lab,
                        "award": award,
                    }
                )

    file_sheet = pandas.DataFrame(file_sheet)
    server.prepare_objects_from_sheet("/files/", file_sheet, validator)

    base = Path(args.spreadsheet_file).stem
    file_sheet.to_excel(Path(base + "-file.xlsx"), index=False)


def make_parser():
    parser = ArgumentParser()
    parser.add_argument("-f", "--spreadsheet-file", required=True)
    parser.add_argument("-s", "--sheet-name", default="Library")
    parser.add_argument("-n", "--dry-run", default=False, action="store_true")
    add_auth_options(parser)
    add_debug_arguments(parser)
    return parser


def add_debug_arguments(parser):
    """Add arguments for tuning logging"""
    group = parser.add_argument_group("Verbosity", "Set logging level")
    group.add_argument(
        "-v",
        "--verbose",
        default=False,
        action="store_true",
        help="Display informational level log messages",
    )
    group.add_argument(
        "-d",
        "--debug",
        default=False,
        action="store_true",
        help="Display debugging level log messages",
    )
    return group


def configure_logging(args, **kwargs):
    """run logging.basicConfig based on common verbosity command line arguments"""
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, **kwargs)
    elif args.verbose:
        logging.basicConfig(level=logging.INFO, **kwargs)
    else:
        logging.basicConfig(level=logging.WARNING, **kwargs)


def get_library_rdf_details(library_id):
    model = Graph()
    load_into_model(
        model, "rdfa", "http://jumpgate.caltech.edu/library/{}/".format(library_id)
    )
    query = """PREFIX lo: <http://jumpgate.caltech.edu/wiki/LibraryOntology#>
    select ?library_id ?gel_cut ?insert_size ?index ?flowcell_id ?lane_id ?lane_status
    where {
      ?library a lo:Library ;
               lo:library_id ?library_id ;
               lo:gel_cut ?gel_cut ;
               lo:insert_size ?insert_size ;
               lo:multiplex_index ?index ;
               lo:has_lane ?lane .

      ?lane lo:flowcell ?flowcell ;
            lo:lane_number ?lane_id .

      ?flowcell lo:flowcell_id ?flowcell_id .
    }
    """
    for row in model.query(query):
        record = row.asdict()

        for name in record:
            record[name] = record[name].toPython()
        _, record["index"] = record["index"].split(":")
        yield record


# This doesn't support paired end
class FlowcellFastqs:
    def __init__(self, htsw, root):
        self.root = Path(root)
        self.htsw = htsw
        self._fastqs = {}

    def __getitem__(self, library_id):
        if library_id not in self._fastqs:
            for column in ["read_1", "read_2"]:
                reads = list(self.find_fastqs(library_id, column))
                if len(reads) > 0:
                    self._fastqs.setdefault(library_id, {})[column] = reads
        return self._fastqs[library_id]

    def find_fastqs(self, library_id, read_column="read_1"):
        library = self.htsw.get_library(library_id)
        for lane in library["lane_set"]:
            if lane["status"] in ("Good", ""):
                flowcell_id = lane["flowcell"]
                library_row = self.load_library_row(library_id, flowcell_id)
                if read_column in library_row:
                    read = library_row[read_column]
                    for r in read:
                        yield from find_fastqs_by_glob([Path(flowcell_id) / r])

    def load_library_row(self, library_id, flowcell_id):
        library_tsv_files = list((self.root / flowcell_id).glob("lib*.tsv"))
        if len(library_tsv_files) == 0:
            raise RuntimeError("No library tsv for {}".format(flowcell_id))
        elif len(library_tsv_files) == 1:
            libraries = load_library_tables(library_tsv_files)
        elif len(library_tsv_files) > 1:
            raise RuntimeError(
                "unexpected number of matches {} {}".format(
                    flowcell_id, len(library_tsv_files)
                )
            )
        return libraries.loc[library_id]


class FlowcellDetails:
    def __init__(self, htsw):
        self.htsw = htsw
        self._flowcell_details = {}
        self._library_details = {}

    def get_flowcell_details(self, flowcell_id, library_id):
        if flowcell_id not in self._flowcell_details:
            self._flowcell_details[flowcell_id] = self.htsw.get_flowcell(flowcell_id)
        if library_id not in self._library_details:
            self._library_details[library_id] = list(
                get_library_rdf_details(library_id)
            )[0]

        flowcell = self._flowcell_details[flowcell_id]
        library = self._library_details[library_id]

        flowcell_info = {
            "machine": "http://jumpgate.caltech.edu/sequencer/{}".format(
                flowcell["sequencer_id"]
            ),
            "flowcell": flowcell_id,
            "lane": "1",
            "barcode": library["index"],
        }

        return flowcell_info


def get_read_length(submission_pathname):
    stream = xopen.xopen(submission_pathname, "rt")
    header = stream.readline().strip()
    sequence = stream.readline().strip()
    stream.close()
    read_length = len(sequence)
    return read_length


def find_tsvs(library_sheet):
    flowcells = {}
    libraries = {}
    library_tsvs = {}
    experiment_tsvs = {}

    for i, row in library_sheet.iterrows():
        aliases = row["aliases:array"].split(",")
        library_id = aliases[0][len("barbara-wold:") :]
        library = htsw.get_library(library_id)
        libraries[library_id] = library
        for lane in library["lane_set"]:
            flowcell_id = lane["flowcell"]
            if flowcell_id not in flowcells:
                flowcells[flowcell_id] = htsw.get_flowcell(flowcell_id)
            if flowcell_id not in library_tsvs:
                experiment_tsv_files = list(Path(flowcell_id).glob("exp*.tsv"))
                if len(experiment_tsv_files) == 1:
                    experiment_tsvs[flowcell_id] = load_experiments(experiment_tsv_files)
                if len(experiment_tsv_files) > 1:
                    raise RuntimeError(
                        "unexpected number of matches {} {}".format(
                            flowcell_id, len(experiment_tsv_files)
                        )
                    )

                library_tsv_files = list(Path(flowcell_id).glob("lib*.tsv"))
                if len(library_tsv_files) == 1:
                    library_tsvs[flowcell_id] = load_library_tables(library_tsv_files)
                if len(library_tsv_files) > 1:
                    raise RuntimeError(
                        "unexpected number of matches {} {}".format(
                            flowcell_id, len(library_tsv_files)
                        )
                    )
            if flowcell_id in library_tsvs:
                read_1 = library_tsvs[flowcell_id].loc[library_id]["read_1"]
                for r in read_1:
                    fastqs = find_fastqs_by_glob([Path(flowcell_id) / r])
                    libraries[library_id].setdefault("read_1", []).extend(fastqs)

    return library_tsvs


if __name__ == "__main__":
    main()
