from htsworkflow.pipelines import LANE_LIST

class SampleKey(object):
    """Identifier for a sample in a particular 'location' on a flowcell.
    """
    def __init__(self, lane=None, read=None, sample=None):
        self.lane = int(lane) if lane is not None else None
        self.read = int(read) if read is not None else None
        self.sample = sample

    def _iswild(self):
        return self.lane is None or \
               self.read is None or \
               self.sample is None
    iswild = property(_iswild)

    def matches(self, other):
        """Test non-None attributes
        """
        if not (self.lane is None or other.lane is None):
            if self.lane != other.lane: return False
        if not (self.read is None or other.read is None):
            if self.read != other.read:  return False
        if not (self.sample is None or other.sample is None):
            if self.sample != other.sample: return False
        return True

    def __eq__(self, other):
        return (self.lane == other.lane) and \
               (self.read == other.read) and \
               (self.sample == other.sample)

    def __ne__(self, other):
        return (self.lane != other.lane) or \
               (self.read != other.read) or \
               (self.sample != other.sample)

    def __lt__(self, other):
        if self.lane < other.lane:
            return True
        elif self.lane > other.lane:
            return False
        elif self.sample < other.sample:
            return True
        elif self.sample > other.sample:
            return False
        elif self.read < other.read:
            return True
        elif self.read > other.read:
            return False
        else:
            # equal
            return False

    def __le__(self, other):
        if self == other: return True
        else: return self < other

    def __gt__(self, other):
        return not self <= other

    def __ge__(self, other):
        return not self < other

    def __hash__(self):
        return hash((self.sample, self.lane, self.read))

    def __repr__(self):
        name = []

        name.append('L%s' % (self.lane,))
        name.append('R%s' % (self.read,))
        name.append('S%s' % (self.sample,))

        return '<SampleKey(' + ",".join(name) + ')>'

LANE_SAMPLE_KEYS = [ SampleKey(lane=l) for l in LANE_LIST ]