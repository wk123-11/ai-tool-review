import sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'scripts'))
import publish_state
class Tests(unittest.TestCase):
    def test_duplicate(self):
        with tempfile.TemporaryDirectory() as td:
            old=publish_state.STATE_FILE; publish_state.STATE_FILE=Path(td)/'state.json'
            try:
                publish_state.record('toutiao','cid','unique-test-title','published',remote_id='123')
                self.assertEqual(publish_state.load_state()['items']['cid']['toutiao']['remote_id'],'123')
                with self.assertRaises(publish_state.AlreadyPublishedError): publish_state.assert_publishable('toutiao','cid','unique-test-title')
                publish_state.assert_publishable('toutiao','cid','unique-test-title',force=True)
            finally: publish_state.STATE_FILE=old
if __name__=='__main__': unittest.main()
