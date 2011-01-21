#!/usr/bin/env python

from optparse import OptionParser
import os
import re
import sys

def main(cmdline=None):
    parser = make_parser()
    opts, args = parser.parse_args(cmdline)

    for filename in args[1:]:
        stream = open(filename, 'r')
        if opts.fastq:
            validate_fastq(f, opts.uniform_lengths)
        stream.close()
    return 0

def make_parser():
    parser = OptionParser()
    parser.add_option("--fastq", action="store_true", default=False,
                      help="verify arguments are valid fastq file")
    parser.add_option("--uniform-lengths", action="store_true", default=False,
                      help="require all reads to be of the same length")
                      
    return parser


def validate_fastq(stream, uniform_length=False):
    """Validate that a fastq file isn't corrupted

    uniform_length - requires that all sequence & qualities must be
                     the same lengths.

    returns number of errors found
    """
    FQ_NONE = 0
    FQ_H1 = 1
    FQ_SEQ = 2
    FQ_H2 = 3
    FQ_QUAL = 4
    h1_re = re.compile("^>[ \t\w]*$")
    seq_re = re.compile("^[AGCT.N]+$", re.IGNORECASE)
    h2_re = re.compile("^@[ \t\w]*$")
    phred33 = re.compile("^[!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJ]+$")
    phred64 = re.compile("^[@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefgh]+$")

    state = FQ_H1
    length = None
    line_number = 1
    errors = 0
    for line in stream:
        line = line.rstrip()
        if state == FQ_H1:
            # reset length at start of new record for non-uniform check
            if not uniform_length:
                length = None
            # start of record checks
            errors = validate_re(h1_re, line, line_number, errors,
                                 "FAIL H1")
            state = FQ_SEQ
        elif state == FQ_SEQ:
            errors = validate_re(seq_re, line, line_number, errors,
                                 "FAIL SEQ")
            length, errors = validate_length(line, length, line_number,
                                             errors,
                                             "FAIL SEQ LEN")
            state = FQ_H2
        elif state == FQ_H2:
            errors = validate_re(h2_re, line, line_number, errors, "FAIL H2")
            state = FQ_QUAL
        elif state == FQ_QUAL:
            errors = validate_re(phred64, line, line_number, errors,
                                 "FAIL QUAL")
            length, errors = validate_length(line, length, line_number, errors,
                                            "FAIL QUAL LEN")
            state = FQ_H1
        else:
            raise RuntimeError("Invalid state: %d" % (state,))
        line_number += 1
    return errors

def validate_re(pattern, line, line_number, error_count, errmsg):
    if pattern.match(line) is None:
        print errmsg, "[%d]: %s" % (line_number, line)
        error_count += 1
    return error_count

def validate_length(line, line_length, line_number, error_count, errmsg):
    """
    if line_length is None, sets it
    """
    if line_length is None:
        line_length = len(line)
    elif len(line) != line_length:
        print errmsg, "%d: %s" %(line_number, line)
        error_count += 1
    return line_length, error_count
    
