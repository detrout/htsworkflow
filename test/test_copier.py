from unittest import TestCase, skipIf

from six.moves import StringIO
from htsworkflow.automation.solexa import is_runfolder

try:
    from htsworkflow.automation import copier
    BENDERJAB_UNAVAILABLE = False
except ImportError as e:
    BENDERJAB_UNAVAILABLE = True

@skipIf(BENDERJAB_UNAVAILABLE, "Can't test copier daemon without a working benderjab")
class testCopier(TestCase):
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
rsync_sources: rsync://localhost/tmp/sequencer_source rsync://user@server:1234/other_sequencer
rsync_destination: /tmp/sequencer_destination
notify_users: user3@example.fake
# who to run to
#runner:
""")
        c = copier.CopierBot("copier", configfile=cfg)
        c.read_config()
        c._init_rsync()
        self.assertEqual(c.jid, 'copier@example.fake')
        self.assertEqual(c.cfg['password'], 'badpassword')
        self.assertEqual(len(c.authorized_users), 2)
        self.assertEqual(c.authorized_users[0], 'user1@example.fake')
        self.assertEqual(c.authorized_users[1], 'user2@example.fake')
        self.assertEqual(c.rsync.source_base_list[0],
                             'rsync://localhost/tmp/sequencer_source/')
        self.assertEqual(c.rsync.dest_base, '/tmp/sequencer_destination')
        self.assertEqual(len(c.notify_users), 1)
        self.assertEqual(c.notify_users[0], 'user3@example.fake')
        self.assertEqual(c.validate_url('rsync://other/tmp'), None)
        self.assertEqual(c.validate_url('http://localhost/tmp'), None)
        # In the rsync process the URL gets a trailing '/' added to it
        # But in the bot config its still slash-less.
        # It is debatable when to add the trailing slash.
        self.assertEqual(
          c.validate_url('rsync://localhost/tmp/sequencer_source'),
          'rsync://localhost/tmp/sequencer_source')
        self.assertEqual(
          c.validate_url('rsync://localhost/tmp/sequencer_source/'),
          'rsync://localhost/tmp/sequencer_source/')
        self.assertEqual(
          c.validate_url('rsync://localhost/tmp/sequencer_source/bleem'),
          'rsync://localhost/tmp/sequencer_source/bleem')
        self.assertEqual(
          c.validate_url('rsync://user@server:1234/other_sequencer'),
          'rsync://user@server:1234/other_sequencer')


    def test_dirlist_filter(self):
       """
       test our dir listing parser
       """
       # everyone should have a root dir, and since we're not
       # currently writing files... it should all be good
       r = copier.rsync('/', '/', '/')

       listing = [
         'drwxrwxr-x           0 2007/12/29 12:34:56 071229_USI-EAS229_001_FC1234\n',
         '-rwxrw-r--      123268 2007/12/29 17:39:31 2038EAAXX.rtf\n',
         '-rwxrw-r--           6 2007/12/29 15:10:29 New Text Document.txt\n',
       ]

       result = r.list_filter(listing)
       self.assertEqual(len(result), 1)
       self.assertEqual(result[0][-1], '4')


def suite():
    from unittest import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(testCopier))
    return suite


if __name__ == "__main__":
    from unittest import main
    main(defaultTest="suite")
