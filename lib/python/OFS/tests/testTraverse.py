import os, sys, unittest

import string, cStringIO, re
import ZODB, Acquisition
from OFS.Application import Application
from OFS.Folder import manage_addFolder
from OFS.Image import manage_addFile
from Testing.makerequest import makerequest
from AccessControl import SecurityManager
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager

from mimetools import Message
from multifile import MultiFile

class UnitTestSecurityPolicy:
    """
        Stub out the existing security policy for unit testing purposes.
    """
    #
    #   Standard SecurityPolicy interface
    #
    def validate( self
                , accessed=None
                , container=None
                , name=None
                , value=None
                , context=None
                , roles=None
                , *args
                , **kw):
        return 1

    def checkPermission( self, permission, object, context) :
        return 1

class UnitTestUser( Acquisition.Implicit ):
    """
        Stubbed out manager for unit testing purposes.
    """
    def getId( self ):
        return 'unit_tester'

    getUserName = getId

    def allowed( self, object, object_roles=None ):
        return 1

def makeConnection():
    import ZODB
    from ZODB.DemoStorage import DemoStorage

    s = DemoStorage(quota=(1<<20))
    return ZODB.DB( s ).open()

class TestTraverse( unittest.TestCase ):

    def setUp( self ):

        self.connection = makeConnection()
        try:
            r = self.connection.root()
            a = Application()
            r['Application'] = a
            self.root = a
            responseOut = self.responseOut = cStringIO.StringIO()
            self.app = makerequest( self.root, stdout=responseOut )
            manage_addFolder( self.app, 'folder1' )
            folder1 = getattr( self.app, 'folder1' )

            folder1.all_meta_types = \
                                    ( { 'name'        : 'File'
                                      , 'action'      : 'manage_addFile'
                                      , 'permission'  : 'Add images and files'
                                      }
                                    ,
                                    )

            manage_addFile( folder1, 'file'
                          , file='', content_type='text/plain')

            # Hack, we need a _p_mtime for the file, so we make sure that it
            # has one. We use a subtransaction, which means we can rollback
            # later and pretend we didn't touch the ZODB.
            get_transaction().commit()
        except:
            self.connection.close()
            raise
        get_transaction().begin()
        self.folder1 = getattr( self.app, 'folder1' )

        self.policy = UnitTestSecurityPolicy()
        self.oldPolicy = SecurityManager.setSecurityPolicy( self.policy )
        newSecurityManager( None, UnitTestUser().__of__( self.root ) )

    def tearDown( self ):
        noSecurityManager()
        SecurityManager.setSecurityPolicy( self.oldPolicy )
        del self.oldPolicy
        del self.policy
        del self.folder1
        get_transaction().abort()
        self.app._p_jar.sync()
        self.connection.close()
        del self.app
        del self.responseOut
        del self.root
        del self.connection

    def testTraversePath( self ):
        self.failUnless( 'file' in self.folder1.objectIds() )
        self.failUnless( self.folder1.unrestrictedTraverse( ('', 'folder1', 'file' ) ))
        self.failUnless( self.folder1.unrestrictedTraverse( ('', 'folder1' ) ))

    def testTraverseURLNoSlash( self ):
        self.failUnless( 'file' in self.folder1.objectIds() )
        self.failUnless( self.folder1.unrestrictedTraverse( '/folder1/file' ))
        self.failUnless( self.folder1.unrestrictedTraverse( '/folder1' ))

    def testTraverseURLSlash( self ):
        self.failUnless( 'file' in self.folder1.objectIds() )
        self.failUnless( self.folder1.unrestrictedTraverse( '/folder1/file/' ))
        self.failUnless( self.folder1.unrestrictedTraverse( '/folder1/' ))

    def testTraverseToNone( self ):
        self.failUnlessRaises( KeyError, self.folder1.unrestrictedTraverse, ('', 'folder1', 'file2' ) )
        self.failUnlessRaises( KeyError, self.folder1.unrestrictedTraverse,  '/folder1/file2' )
        self.failUnlessRaises( KeyError, self.folder1.unrestrictedTraverse,  '/folder1/file2/' )

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( TestTraverse ) )
    return suite

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    main()
