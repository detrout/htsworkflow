'''summarize fastq file
'''
import os
import numpy

def summarize_hiseq_fastq(stream):
    reads = 0
    pass_qc = 0
    bad_read = False
    mean = None
    eol_length = len(os.linesep)

    for i, line in enumerate(stream):
        if i % 4 == 0:
            # header  looks like this
            # @HWI-ST0787:114:D0PMDACXX:8:1101:1605:2154 1:N:0:TAGCTT
            # we want the :N (passed filter) or :Y (failed filter)
            reads += 1
            # if flag is 'N' we are not a bad read
            bad_read = False if line[line.rfind(' ') + 3] == 'N' else True
            if not bad_read:
                pass_qc += 1

        elif i % 4 == 3:
            # score
            if not bad_read:
                # don't include bad reads in score
                # score = numpy.asarray(list(line.rstrip()), dtype='c') # 3.5 min
                #score = numpy.asarray(line[:-eol_length], dtype='c') # 2 min
                score = numpy.asarray(line[:-eol_length], dtype='c') # 1.4 min
                score.dtype = numpy.int8

                if mean is None:
                    mean = numpy.zeros(len(score), dtype=numpy.float)

                delta = score - mean
                mean = mean + delta / pass_qc

    return (reads, pass_qc, mean)

if __name__ == '__main__':
    import sys
    with open(sys.argv[1], 'r') as instream:
        print summarize_hiseq_fastq(instream)
