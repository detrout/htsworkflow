#!/usr/bin/env python

from optparse import OptionParser
import os
import re
import sys

def main(cmdline=None):
    parser = make_parser()
    opts, args = parser.parse_args(cmdline)

    error_happened = False
    for filename in args[1:]:
        stream = open(filename, 'r')
        
        if opts.fastq:
            errors = validate_fastq(stream,
                                    opts.format,
                                    opts.uniform_lengths,
                                    opts.max_errors)
            if errors > 0:
                print "%s failed validation" % (filename,)
                error_happened = True

        stream.close()

    if error_happened:
        return 1
    
    return 0

def make_parser():
    parser = OptionParser()
    parser.add_option("--fastq", action="store_true", default=False,
                      help="verify arguments are valid fastq file")
    parser.add_option("--uniform-lengths", action="store_true", default=False,
                      help="require all reads to be of the same length")
    parser.add_option("--max-errors", type="int", default=None)
    encodings=['phred33', 'phred64']
    parser.add_option("--format", type="choice",
                      choices=encodings,
                      default='phred64',
                      help="choose quality encoding one of: %s" % (", ".join(encodings)))
                      
    return parser


def validate_fastq(stream, format='phred33', uniform_length=False, max_errors=None):
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
    h1_re = re.compile("^@[\s\w:-]*$")
    seq_re = re.compile("^[AGCT.N]+$", re.IGNORECASE)
    h2_re = re.compile("^\+[\s\w:-]*$")
    phred33 = re.compile("^[!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJ]+$")
    phred64 = re.compile("^[@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefgh]+$")

    if format == 'phred33':
        quality_re = phred33
    elif format == 'phred64':
        quality_re = phred64
    else:
        raise ValueError("Unrecognized quality format name")

    state = FQ_H1
    length = None
    line_number = 1
    errors = 0
    for line in stream:
        line = line.rstrip()
        len_errors = 0
        if state == FQ_H1:
            # reset length at start of new record for non-uniform check
            if not uniform_length:
                length = None
            # start of record checks
            errors += validate_re(h1_re, line, line_number, "FAIL H1")
            state = FQ_SEQ
        elif state == FQ_SEQ:
            errors += validate_re(seq_re, line, line_number, "FAIL SEQ")
            length, len_errors = validate_length(line, length, line_number,
                                                 "FAIL SEQ LEN")
            errors += len_errors
            state = FQ_H2
        elif state == FQ_H2:
            errors += validate_re(h2_re, line, line_number, "FAIL H2")
            state = FQ_QUAL
        elif state == FQ_QUAL:
            errors += validate_re(quality_re, line, line_number, "FAIL QUAL")
            length, len_errors = validate_length(line, length, line_number,
                                                 "FAIL QUAL LEN")
            errors += len_errors
            state = FQ_H1
        else:
            raise RuntimeError("Invalid state: %d" % (state,))
        line_number += 1
        if max_errors is not None and errors > max_errors:
            break
        
    return errors

def validate_re(pattern, line, line_number, errmsg):
    if pattern.match(line) is None:
        print errmsg, "[%d]: %s" % (line_number, line)
        return 1
    else:
        return 0

def validate_length(line, line_length, line_number, errmsg):
    """
    if line_length is None, sets it
    """
    error_count = 0
    if line_length is None:
        line_length = len(line)
    elif len(line) != line_length:
        print errmsg, "%d: %s" %(line_number, line)
        error_count = 1
    return line_length, error_count
    
