##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""A 'PageTemplateFile' without security restrictions.

$Id$
"""
from os.path import basename
from zope.app.pagetemplate import viewpagetemplatefile

from Acquisition import aq_get
from AccessControl import getSecurityManager
from Products.PageTemplates.Expressions import SecureModuleImporter
from Products.PageTemplates.Expressions import createTrustedZopeEngine

from Products.Five.bbb import AcquisitionBBB

_engine = createTrustedZopeEngine()
def getEngine():
    return _engine

class ViewPageTemplateFile(viewpagetemplatefile.ViewPageTemplateFile):

    def getId(self):
        return basename(self.filename)

    id = property(getId)

    def pt_getEngine(self):
        return getEngine()

    def pt_getContext(self, instance, request, **kw):
        context = super(ViewPageTemplateFile, self).pt_getContext(
            instance, request, **kw)

        # get the root
        obj = context['context']
        root = None
        meth = aq_get(obj, 'getPhysicalRoot', None)
        if meth is not None:
            root = meth()

        context.update(here=context['context'],
                       # philiKON thinks container should be the view,
                       # but BBB is more important than aesthetics.
                       container=context['context'],
                       root=root,
                       modules=SecureModuleImporter,
                       traverse_subpath=[],  # BBB, never really worked
                       user = getSecurityManager().getUser()
                       )
        return context

    def __get__(self, instance, type):
        return BoundPageTemplate(self, instance)


# When a view's template is accessed e.g. as template.view, a
# BoundPageTemplate object is retured.  For BBB reasons, it needs to
# support the aq_* methods and attributes known from Acquisition.  For
# that it also needs to be locatable thru __parent__.

class BoundPageTemplate(viewpagetemplatefile.BoundPageTemplate,
                        AcquisitionBBB):

    __parent__ = property(lambda self: self.im_self)


# BBB
ZopeTwoPageTemplateFile = ViewPageTemplateFile
