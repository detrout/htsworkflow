import unittest

from StringIO import StringIO
from gaworkflow import copier

class testCopier(unittest.TestCase):
    def test_runfolder_validate(self):
        self.failUnlessEqual(copier.runfolder_validate(""), False)
        self.failUnlessEqual(copier.runfolder_validate("1345_23"), False)
        self.failUnlessEqual(copier.runfolder_validate("123456_asdf-$23'"), False)
        self.failUnlessEqual(copier.runfolder_validate("123456_USI-EAS44"), True)
        self.failUnlessEqual(copier.runfolder_validate("123456_USI-EAS44 "), False)
        
    def test_empty_config(self):
        cfg = StringIO("""[fake]
something: unrelated
""")
        bot = copier.CopierBot('fake', configfile=cfg)
        self.failUnlessRaises(RuntimeError, bot.read_config)
        
    def test_full_config(self):
        cfg = StringIO("""[copier]        
jid: copier@example.fake
password: badpassword
authorized_users: user1@example.fake user2@example.fake
rsync_password_file: ~/.sequencer
rsync_source: /tmp/sequencer_source
rsync_destination: /tmp/sequencer_destination
notify_users: user3@example.fake
# who to run to
#runner:
""")
        c = copier.CopierBot("copier", configfile=cfg)
        c.read_config()
        self.failUnlessEqual(c.jid, 'copier@example.fake')
        self.failUnlessEqual(c.cfg['password'], 'badpassword')
        self.failUnlessEqual(len(c.authorized_users), 2)
        self.failUnlessEqual(c.authorized_users[0], 'user1@example.fake')
        self.failUnlessEqual(c.authorized_users[1], 'user2@example.fake')
        self.failUnlessEqual(c.rsync.source_base, '/tmp/sequencer_source')
        self.failUnlessEqual(c.rsync.dest_base, '/tmp/sequencer_destination')
        self.failUnlessEqual(len(c.notify_users), 1)
        self.failUnlessEqual(c.notify_users[0], 'user3@example.fake')

def suite():
    return unittest.makeSuite(testCopier,'test')

if __name__ == "__main__":
    unittest.main(defaultTest="suite")
