from optparse import OptionParser
import os
import sys
from pprint import pprint

def main(cmdline=None):
    parser = make_parser()
    opts, args = parser.parse_args(cmdline)

    extensions = scan(args)
    #pprint(extensions)
    print find_common_suffix(extensions)

def make_parser():
    parser = OptionParser("%prog: directory [directory...]")
    return parser

def scan(toscan):
    index = {}
    for cur_scan_dir in toscan:
        for path, dirnames, filenames in os.walk(cur_scan_dir):
            for filename in filenames:
                next_index = index
                for c in filename[::-1]:
                    next_index = next_index.setdefault(c, {})
    return index

def find_common_suffix(index, tail=[]):
    if len(tail) > 0 and len(index) > 1:
        return "".join(tail[::-1])

    results = []
    for key, choice in index.items():
        r = find_common_suffix(choice, tail+[key])
        if r is not None:
            results.append (r)
        
    if len(results) == 0:
        return None
    elif len(results) == 1:
        return results[0]
    else:
        return results

if __name__ == "__main__":
    main()
