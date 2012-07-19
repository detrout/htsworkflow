"""Convert chromosome names to genome/chromsome names
"""
from glob import glob
import os
import collections
from htsworkflow.pipelines.runfolder import ElementTree

vldInfo = collections.namedtuple('vldInfo', 'name is_link')

class GenomeMap(collections.MutableMapping):
    def __init__(self, items=None):
        self._contigs = {}
        if items is not None:
            self._contigs.update(items)

    def __len__(self):
        return len(self._contigs)

    def __iter__(self):
        return self._contigs.iterkeys()

    def __getitem__(self, name):
        return self._contigs[name]

    def __setitem__(self, name, value):
        self._contigs[name] = value

    def __delitem__(self, name):
        del self._contigs[name]

    def scan_genome_dir(self, genome_dir):
        """Build map from a genome directory"""
        genome = genome_dir.split(os.path.sep)[-1]
        vld_files = glob(os.path.join(genome_dir, '*.vld'))
        vld = [ vldInfo(f, os.path.islink(f)) for f in vld_files ]
        self.build_map_from_dir(genome, vld)

    def build_map_from_dir(self, genome_name, vld_list):
        """Initialize contig genome map from list of vldInfo tuples
        """
        # build fasta to fasta file map
        for vld_file, is_link in vld_list:
            vld_file = os.path.realpath(vld_file)
            path, vld_name = os.path.split(vld_file)
            name, ext = os.path.splitext(vld_name)
            if is_link:
                self._contigs[name] = name
            else:
                self._contigs[name] = genome_name + '/' + name

    def parse_genomesize(self, pathname):
        """Parse genomesize.xml file
        """
        tree = ElementTree.parse(pathname)
        self.build_map_from_element(tree.getroot())

    def build_map_from_element(self, root):
        """Build genome map from a parsed HiSeq genomesizes.xml file
        """
        sizes = {}
        filenames = {}
        for element in root:
            contig = element.attrib['contigName']
            filename = element.attrib['fileName']
            filenames[contig] = filename
            bases = int(element.attrib['totalBases'])
            sizes[contig] = bases

        genome = guess_genome(sizes)

        for contig, basese in sizes.items():
            name = filenames[contig]
            self._contigs[name] = genome + '/' + name

def guess_genome(contig_sizes):
    """Guess what genome we're using"""
    # guess genome names

    genomes = {'chr1': {197195432: 'mm9',
                        247249719: 'hg19',
                        200994015: 'galGal3',
                        },
               'chrI': {230218: 'sacCer3',
                        15072421: 'elegans190'},
               '1': {60348388: 'danRe6'},
               'chr2L': { 23011544: 'dm3' },

               }

    for key in genomes:
        size = contig_sizes.get(key, 0)
        if size in genomes[key]:
            return genomes[key][size]

    if len(contig_sizes) == 1:
        return os.path.splitext(contig_sizes.keys()[0])[0]

    raise RuntimeError("Unrecognized genome type, update detection code.")
