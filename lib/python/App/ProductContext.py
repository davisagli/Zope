##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
"""Objects providing context for product initialization
"""
from AccessControl.PermissionRole import PermissionRole
import Globals, os, OFS.ObjectManager, OFS.misc_, Products
import AccessControl.Permission
from HelpSys import HelpTopic, APIHelpTopic
from HelpSys.HelpSys import ProductHelp
from FactoryDispatcher import FactoryDispatcher
from zLOG import LOG, WARNING
import string, os.path, re
import stat
from DateTime import DateTime
from types import ListType, TupleType
from Interface import instancesOfObjectImplements

import ZClasses # to enable 'PC.registerBaseClass()'

if not hasattr(Products, 'meta_types'): Products.meta_types=()
if not hasattr(Products, 'meta_classes'):
    Products.meta_classes={}
    Products.meta_class_info={}

_marker = []  # Create a new marker object

class ProductContext:

    def __init__(self, product, app, package):
        self.__prod=product
        self.__app=app
        self.__pack=package

    def registerClass(self, instance_class=None, meta_type='', 
                      permission=None, constructors=(),
                      icon=None, permissions=None, legacy=(),
                      visibility="Global",interfaces=_marker
        ):
        """Register a constructor

        Keyword arguments are used to provide meta data:

        instance_class -- The class of the object that will be created.
        
          This is not currently used, but may be used in the future to
          increase object mobility.

        meta_type -- The kind of object being created
           This appears in add lists.  If not specified, then the class
           meta_type will be used.

        permission -- The permission name for the constructors.
           If not specified, then a permission name based on the
           meta type will be used.

        constructors -- A list of constructor methods
          A method can me a callable object with a __name__
          attribute giving the name the method should have in the
          product, or the method may be a tuple consisting of a
          name and a callable object.  The method must be picklable.

          The first method will be used as the initial method called
          when creating an object.

        icon -- The name of an image file in the package to
                be used for instances. Note that the class icon
                attribute will be set automagically if an icon is
                provided.

        permissions -- Additional permissions to be registered
           If not provided, then permissions defined in the
           class will be registered.
        
        legacy -- A list of legacy methods to be added to ObjectManager
                  for backward compatibility

        visibility -- "Global" if the object is globally visible, None else

        interfaces -- a list of the interfaces the object supports

        """
        app=self.__app
        pack=self.__pack
        initial=constructors[0]
        tt=type(())
        productObject=self.__prod
        pid=productObject.id

        if icon and instance_class is not None:
            setattr(instance_class, 'icon', 'misc_/%s/%s' %
                    (pid, os.path.split(icon)[1]))

        OM=OFS.ObjectManager.ObjectManager

        if permissions:
            for p in permissions:
                if type(p) is tt:
                    p, default= p
                    AccessControl.Permission.registerPermissions(
                        ((p, (), default),))
                else:
                    AccessControl.Permission.registerPermissions(
                        ((p, ()),))

        ############################################################
        # Constructor permission setup
        if permission is None:
            permission="Add %ss" % (meta_type or instance_class.meta_type)

        if type(permission) is tt:
            permission, default = permission
        else:
            default = ('Manager',)

        pr=PermissionRole(permission,default)
        AccessControl.Permission.registerPermissions(
            ((permission, (), default),))
        ############################################################

        for method in legacy:
            if type(method) is tt:
                name, method = method
                aliased = 1
            else:
                name=method.__name__
                aliased = 0
            if not OM.__dict__.has_key(name):
                setattr(OM, name, method)
                setattr(OM, name+'__roles__', pr)
                if aliased:
                    # Set the unaliased method name and its roles
                    # to avoid security holes.  XXX: All "legacy"
                    # methods need to be eliminated.
                    setattr(OM, method.__name__, method)
                    setattr(OM, method.__name__+'__roles__', pr)

        if type(initial) is tt: name, initial = initial
        else: name=initial.__name__

        fd=getattr(pack, '__FactoryDispatcher__', None)
        if fd is None:
            class __FactoryDispatcher__(FactoryDispatcher):
                "Factory Dispatcher for a Specific Product"

            fd = pack.__FactoryDispatcher__ = __FactoryDispatcher__

        if not hasattr(pack, '_m'): pack._m=fd.__dict__
        m=pack._m

        if interfaces is _marker:
            interfaces = instancesOfObjectImplements(instance_class)

        Products.meta_types=Products.meta_types+(
            { 'name': meta_type or instance_class.meta_type,
              'action': ('manage_addProduct/%s/%s' % (pid, name)),
              'product': pid,
              'permission': permission,
              'visibility': visibility,
              'interfaces': interfaces,
              'instance': instance_class,
              },)

        m[name]=initial
        m[name+'__roles__']=pr

        for method in constructors[1:]:
            if type(method) is tt: name, method = method
            else:
                name=os.path.split(method.__name__)[-1]
            if not productObject.__dict__.has_key(name):
                m[name]=method
                m[name+'__roles__']=pr

        if icon:
            name=os.path.split(icon)[1]
            icon=Globals.ImageFile(icon, self.__pack.__dict__)
            icon.__roles__=None
            if not hasattr(OFS.misc_.misc_, pid):
                setattr(OFS.misc_.misc_, pid, OFS.misc_.Misc_(pid, {}))
            getattr(OFS.misc_.misc_, pid)[name]=icon


    def registerZClass(self, Z, meta_type=None):
        #
        #   Convenience method, now deprecated -- clients should
        #   call 'ZClasses.createZClassForBase()' themselves at
        #   module import time, passing 'globals()', so that the
        #   ZClass will be available immediately.
        #
        base_class=Z._zclass_
        if meta_type is None:
            if hasattr(base_class, 'meta_type'): meta_type=base_class.meta_type
            else:                                meta_type=base_class.__name__

        module=base_class.__module__
        name=base_class.__name__
            
        key="%s/%s" % (module, name)

        if module[:9]=='Products.': module=string.split(module,'.')[1]
        else: module=string.split(module,'.')[0]
            
        info="%s: %s" % (module, name)

        Products.meta_class_info[key]=info # meta_type
        Products.meta_classes[key]=Z
        
        

    def registerBaseClass(self, base_class, meta_type=None):
        #
        #   Convenience method, now deprecated -- clients should
        #   call 'ZClasses.createZClassForBase()' themselves at
        #   module import time, passing 'globals()', so that the
        #   ZClass will be available immediately.
        #
        Z = ZClasses.createZClassForBase( base_class, self.__pack )
        return Z


    def getProductHelp(self):
        """
        Returns the ProductHelp associated with the current Product.
        """
        return self.__prod.__of__(self.__app.Control_Panel.Products).getProductHelp()

    def registerHelpTopic(self, id, topic):
        """
        Register a Help Topic for a product.
        """
        self.getProductHelp()._setObject(id, topic)

    def registerHelpTitle(self, title):
        """
        Sets the title of the Product's Product Help
        """
        h = self.getProductHelp()
        if getattr(h, 'title', None) != title:
            h.title = title

    def registerHelp(self, directory='help', clear=1,
            title_re=re.compile(r'<title>(.+?)</title>', re.I)):
        """
        Registers Help Topics for all objects in a directory.

        Nothing will be done if the files in the directory haven't
        changed since the last registerHelp call.

        'clear' indicates whether or not to delete all existing
        Topics from the Product.

        HelpTopics are created for these kind of files

        .dtml            -- DTMLHelpTopic
        .html .htm       -- TextHelpTopic        
        .stx .txt        -- STXHelpTopic
        .jpg .png .gif   -- ImageHelpTopic
        .py              -- APIHelpTopic
        """
        help=self.getProductHelp()
        path=os.path.join(Globals.package_home(self.__pack.__dict__),
                          directory)

        # If help directory does not exist, log a warning and return.
        try:
            dir_mod_time=DateTime(os.stat(path)[stat.ST_MTIME])
        except OSError, (errno, text):
            LOG("Zope", WARNING, '%s: %s' % (text, path))
            return

        # test to see if nothing has changed since last registration
        if help.lastRegistered is not None and \
                help.lastRegistered >= dir_mod_time:
            return
        help.lastRegistered=DateTime()

        if clear:
            for id in help.objectIds(['Help Topic','Help Image']):
                help._delObject(id)

        for file in os.listdir(path):
            ext=os.path.splitext(file)[1]
            ext=string.lower(ext)
            if ext in ('.dtml',):
                contents = open(os.path.join(path,file),'rb').read()
                m = title_re.search(contents)
                if m:
                    title = m.group(1)
                else:
                    title = ''
                ht=HelpTopic.DTMLTopic(file, '', os.path.join(path,file))
                self.registerHelpTopic(file, ht)
            elif ext in ('.html', '.htm'):
                contents = open(os.path.join(path,file),'rb').read()
                m = title_re.search(contents)
                if m:
                    title = m.group(1)
                else:
                    title = ''
                ht=HelpTopic.TextTopic(file, title, os.path.join(path,file))
                self.registerHelpTopic(file, ht)
            elif ext in ('.stx', '.txt'):
                title=string.split(open(os.path.join(path,file),'rb').readline(), ':')[0]
                ht=HelpTopic.STXTopic(file, title, os.path.join(path, file))
                self.registerHelpTopic(file, ht)
            elif ext in ('.jpg', '.gif', '.png'):
                ht=HelpTopic.ImageTopic(file, '', os.path.join(path, file))
                self.registerHelpTopic(file, ht)
            elif ext in ('.py',):
                if file[0] == '_': # ignore __init__.py
                    continue
                ht=APIHelpTopic.APIHelpTopic(file, '', os.path.join(path, file))
                self.registerHelpTopic(file, ht)
            
