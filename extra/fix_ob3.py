"""
Fix off by 3 error in our database
"""
from optparse import OptionParser
import os
import re
import sys

from django.core.management import setup_environ
from django.conf import settings
setup_environ(settings)

import htsworkflow.frontend.samples.models as samples

def main(cmdline=None):
    parser = make_parser()
    opts, args = parser.parse_args(cmdline)

    dry_run = not opts.run
    fix_ob3(dry_run=dry_run)

    return 0

def make_parser():
    parser = OptionParser("%prog: fix off by 3 error that creeped in")
    parser.add_option("--run", default=False, action="store_true",
                      help="change the database")
    return parser

def fix_ob3(dry_run=True):
    libraries = samples.Library.objects.order_by('id')

    mismatch = 0
    wrong_amp = 0
    wrong_amp_ids = set()
    for lib in libraries:
        if lib.amplified_from_sample is not None:
            amp_sample = lib.amplified_from_sample
            alt_sample = samples.Library.objects.get(pk=int(amp_sample.id)-3)
            if is_alt_sample_right(lib, alt_sample):
                wrong_amp += 1
                wrong_amp_ids.add(int(lib.id))
                print "--- wrong lib ---"
                display_names(lib, amp_sample, alt_sample)
                if not dry_run:
                    lib.amplified_from_sample = alt_sample
                    lib.save()
            #elif lib_name != amp_sample.library_name:
            #    mismatch += 1
            #    print "--- didn't match ---"
            #    display_names(lib_name, lib, amp_sample, other_sample)
    print "-----"
    print "{0} mismatches".format(mismatch)
    print "{0} obviously wrong libs".format(wrong_amp)
    if len(wrong_amp_ids) > 0:
        print "    {0} - {1}".format(min(wrong_amp_ids), max(wrong_amp_ids))

def clean_lib_name(lib):
    """Strip trailing amplified marker character"""
    return re.sub(" *a$", "", lib.library_name)

def is_alt_sample_right(lib, alt_sample):
    """Check to see if the alt sample is the right sample
    """
    lib_name = clean_lib_name(lib)
    return lib_name == alt_sample.library_name
    
def display_names(lib, amp_from_sample, alt_from_sample):
    lib_name = clean_lib_name(lib)
    print "NonA: "+lib.id+"|"+lib_name+"|"
    print "   A: "+lib.id+"|"+lib.library_name+"|"
    print "AmpF: "+ amp_from_sample.id+"|"+amp_from_sample.library_name+"|"
    print "FixF: "+ alt_from_sample.id+"|"+alt_from_sample.library_name+"|"


if __name__ == "__main__":
    sys.exit(main())
