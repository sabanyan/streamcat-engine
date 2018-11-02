import unittest
import uuid

from kskp.engine import main
from kskp.engine.core import EmptyLink
from kskp.engine.data import PathFileSource, Frame
from kskp.mcmd import McmdLink

class MainTestCase(unittest.TestCase):
    def test_main(self):
        result = main.execute(EmptyLink(), {}, {})
        self.assertEqual(result, {})

    def test_mcut(self):    
        s = PathFileSource('csv', '', 'a.csv')
        f = Frame(uuid.uuid4(), s)
        result = main.execute(McmdLink('mcut'), {'f': 'b,c'}, {'i': f})
        self.assertEqual(result, {})