#
# Test for auth_header
#

# $Id: testAuthHeaderTest.py,v 1.2 2005/03/26 18:07:08 shh42 Exp $

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from unittest import TestSuite, makeSuite
from Testing.ZopeTestCase import TestCase
from Testing.ZopeTestCase import zopedoctest

auth_header = zopedoctest.functional.auth_header


class AuthHeaderTestCase(TestCase):

    def test_auth_encoded(self):
        header = 'Basic Z2xvYmFsbWdyOmdsb2JhbG1ncnB3'
        self.assertEquals(auth_header(header), header)

    def test_auth_non_encoded(self):
        header = 'Basic globalmgr:globalmgrpw'
        expected = 'Basic Z2xvYmFsbWdyOmdsb2JhbG1ncnB3'
        self.assertEquals(auth_header(header), expected)

    def test_auth_non_encoded_empty(self):
        header = 'Basic globalmgr:'
        expected = 'Basic Z2xvYmFsbWdyOg=='
        self.assertEquals(auth_header(header), expected)
        header = 'Basic :pass'
        expected = 'Basic OnBhc3M='
        self.assertEquals(auth_header(header), expected)

    def test_auth_non_encoded_colon(self):
        header = 'Basic globalmgr:pass:pass'
        expected = 'Basic Z2xvYmFsbWdyOnBhc3M6cGFzcw=='
        self.assertEquals(auth_header(header), expected)


def test_suite():
    return TestSuite((
        makeSuite(AuthHeaderTestCase),
    ))

if __name__ == '__main__':
    framework()
