#
# Support for functional doc tests
#

# $Id: functional.py,v 1.2 2005/03/26 18:07:08 shh42 Exp $

import sys, re, base64
import warnings

from zope.testing import doctest

from Testing.ZopeTestCase import ZopeTestCase
from Testing.ZopeTestCase import FunctionalTestCase
from Testing.ZopeTestCase import Functional
from Testing.ZopeTestCase import folder_name
from Testing.ZopeTestCase import user_name
from Testing.ZopeTestCase import user_password
from Testing.ZopeTestCase import user_role
from Testing.ZopeTestCase import standard_permissions
from Testing.ZopeTestCase.sandbox import AppZapper
from Testing.ZopeTestCase.functional import ResponseWrapper


class HTTPHeaderOutput:

    # zope.interface.implements(zope.server.interfaces.IHeaderOutput)

    def __init__(self, protocol, omit):
        self.headers = {}
        self.headersl = []
        self.protocol = protocol
        self.omit = omit

    def setResponseStatus(self, status, reason):
        self.status, self.reason = status, reason

    def setResponseHeaders(self, mapping):
        self.headers.update(dict(
            [('-'.join([s.capitalize() for s in name.split('-')]), v)
             for name, v in mapping.items()
             if name.lower() not in self.omit]
        ))

    def appendResponseHeaders(self, lst):
        headers = [split_header(header) for header in lst]
        self.headersl.extend(
            [('-'.join([s.capitalize() for s in name.split('-')]), v)
             for name, v in headers
             if name.lower() not in self.omit]
        )

    def __str__(self):
        out = ["%s: %s" % header for header in self.headers.items()]
        out.extend(["%s: %s" % header for header in self.headersl])
        out.sort()
        out.insert(0, "%s %s %s" % (self.protocol, self.status, self.reason))
        return '\n'.join(out)


class DocResponseWrapper(ResponseWrapper):
    """Response Wrapper for use in doctests
    """

    def __init__(self, response, outstream, path, header_output):
        ResponseWrapper.__init__(self, response, outstream, path)
        self.header_output = header_output

    def __str__(self):
        body = self.getBody()
        if body:
            return "%s\n\n%s" % (self.header_output, body)
        return "%s\n" % (self.header_output)


headerre = re.compile('(\S+): (.+)$')
def split_header(header):
    return headerre.match(header).group(1, 2)

basicre = re.compile('Basic (.+)?:(.+)?$')
def auth_header(header):
    match = basicre.match(header)
    if match:
        import base64
        u, p = match.group(1, 2)
        if u is None:
            u = ''
        if p is None:
            p = ''
        auth = base64.encodestring('%s:%s' % (u, p))
        return 'Basic %s' % auth[:-1]
    return header


def getRootFolder():
    return AppZapper().app()

def sync():
    getRootFolder()._p_jar.sync()


def http(request_string, handle_errors=True):
    """Execute an HTTP request string via the publisher

    This is used for HTTP doc tests.
    """
    import urllib
    import rfc822
    from cStringIO import StringIO
    from ZPublisher.Response import Response
    from ZPublisher.Test import publish_module
    from AccessControl.SecurityManagement import getSecurityManager
    from AccessControl.SecurityManagement import setSecurityManager

    # Save current Security Manager
    old_sm = getSecurityManager()

    # Commit work done by previous python code.
    get_transaction().commit()

    # Discard leading white space to make call layout simpler
    request_string = request_string.lstrip()

    # split off and parse the command line
    l = request_string.find('\n')
    command_line = request_string[:l].rstrip()
    request_string = request_string[l+1:]
    method, path, protocol = command_line.split()
    path = urllib.unquote(path)

    instream = StringIO(request_string)

    env = {"HTTP_HOST": 'localhost',
           "HTTP_REFERER": 'localhost',
           "REQUEST_METHOD": method,
           "SERVER_PROTOCOL": protocol,
           }

    p = path.split('?')
    if len(p) == 1:
        env['PATH_INFO'] = p[0]
    elif len(p) == 2:
        [env['PATH_INFO'], env['QUERY_STRING']] = p
    else:
        raise TypeError, ''

    header_output = HTTPHeaderOutput(
        protocol, ('x-content-type-warning', 'x-powered-by',
                   'bobo-exception-type', 'bobo-exception-file',
                   'bobo-exception-value', 'bobo-exception-line'))

    headers = [split_header(header)
               for header in rfc822.Message(instream).headers]
    for name, value in headers:
        name = ('_'.join(name.upper().split('-')))
        if name not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            name = 'HTTP_' + name
        env[name] = value.rstrip()

    if env.has_key('HTTP_AUTHORIZATION'):
        env['HTTP_AUTHORIZATION'] = auth_header(env['HTTP_AUTHORIZATION'])

    outstream = StringIO()
    response = Response(stdout=outstream, stderr=sys.stderr)

    publish_module('Zope2', stdin=instream,
                   response=response,
                   environ=env)
    header_output.setResponseStatus(response.getStatus(), response.errmsg)
    header_output.setResponseHeaders(response.headers)

    # Restore previous security manager, which may have been changed
    # by calling the publish method above
    setSecurityManager(old_sm)

    # Sync connection
    sync()

    return DocResponseWrapper(response, outstream, path, header_output)


class ZopeSuiteFactory:

    def __init__(self, *args, **kw):
        self._args = args
        self._kw = kw
        self.setup_globs()
        self.setup_test_class()
        self.setup_optionflags()

    def doctestsuite(self):
        return doctest.DocTestSuite(*self._args, **self._kw)

    def docfilesuite(self):
        return doctest.DocFileSuite(*self._args, **self._kw)

    def setup_globs(self):
        globs = self._kw.setdefault('globs', {})
        globs['folder_name'] = folder_name
        globs['user_name'] = user_name
        globs['user_password'] = user_password
        globs['user_role'] = user_role
        globs['standard_permissions'] = standard_permissions

    def setup_test_class(self):
        test_class = self._kw.get('test_class', ZopeTestCase)

        if 'test_class' in self._kw:
            del self._kw['test_class']

        # If the test_class does not have a runTest method, we add
        # a dummy attribute so that TestCase construction works.
        if not hasattr(test_class, 'runTest'):
            setattr(test_class, 'runTest', None)

        # Create a TestCase instance which will be used to execute
        # the setUp and tearDown methods, as well as be passed into
        # the test globals as 'self'.
        test_instance = test_class()

        kwsetUp = self._kw.get('setUp')
        def setUp(test):
            test_instance.setUp()
            test.globs['test'] = test
            test.globs['self'] = test_instance
            if hasattr(test_instance, 'app'):
                test.globs['app'] = test_instance.app
            if hasattr(test_instance, 'folder'):
                test.globs['folder'] = test_instance.folder
            if hasattr(test_instance, 'portal'):
                test.globs['portal'] = test_instance.portal
                test.globs['portal_name'] = test_instance.portal.getId()
            if kwsetUp is not None:
                kwsetUp(test_instance)

        self._kw['setUp'] = setUp

        kwtearDown = self._kw.get('tearDown')
        def tearDown(test):
            if kwtearDown is not None:
                kwtearDown(test_instance)
            test_instance.tearDown()

        self._kw['tearDown'] = tearDown

    def setup_optionflags(self):
        if 'optionflags' not in self._kw:
            self._kw['optionflags'] = (doctest.ELLIPSIS
                                       | doctest.NORMALIZE_WHITESPACE)


class FunctionalSuiteFactory(ZopeSuiteFactory):

    def setup_globs(self):
        ZopeSuiteFactory.setup_globs(self)
        globs = self._kw.setdefault('globs', {})
        globs['http'] = http
        globs['getRootFolder'] = getRootFolder
        globs['sync'] = sync
        globs['user_auth'] = base64.encodestring('%s:%s' % (user_name, user_password))

    def setup_test_class(self):
        test_class = self._kw.get('test_class', FunctionalTestCase)

        # If the passed-in test_class doesn't subclass Functional,
        # we mix it in for you, but we will issue a warning.
        if not issubclass(test_class, Functional):
            name = test_class.__name__
            warnings.warn(("The test_class you are using doesn't "
                           "subclass from ZopeTestCase.Functional. "
                           "Please fix that."), UserWarning, 2)
            if not 'Functional' in name:
                name = 'Functional%s' % name
            test_class = type(name, (Functional, test_class), {})

        self._kw['test_class'] = test_class
        ZopeSuiteFactory.setup_test_class(self)

    def setup_optionflags(self):
        if 'optionflags' not in self._kw:
            self._kw['optionflags'] = (doctest.ELLIPSIS
                                       | doctest.REPORT_NDIFF
                                       | doctest.NORMALIZE_WHITESPACE)


def ZopeDocTestSuite(module=None, **kw):
    module = doctest._normalize_module(module)
    return ZopeSuiteFactory(module, **kw).doctestsuite()


def ZopeDocFileSuite(*paths, **kw):
    if kw.get('module_relative', True):
        kw['package'] = doctest._normalize_module(kw.get('package'))
    return ZopeSuiteFactory(*paths, **kw).docfilesuite()


def FunctionalDocTestSuite(module=None, **kw):
    module = doctest._normalize_module(module)
    return FunctionalSuiteFactory(module, **kw).doctestsuite()


def FunctionalDocFileSuite(*paths, **kw):
    if kw.get('module_relative', True):
        kw['package'] = doctest._normalize_module(kw.get('package'))
    return FunctionalSuiteFactory(*paths, **kw).docfilesuite()


__all__ = [
    'ZopeDocTestSuite',
    'ZopeDocFileSuite',
    'FunctionalDocTestSuite',
    'FunctionalDocFileSuite',
    ]
