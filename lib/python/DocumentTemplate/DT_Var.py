##############################################################################
#
# Copyright (c) 1998, Digital Creations, Fredericksburg, VA, USA.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
#   o Redistributions of source code must retain the above copyright
#     notice, this list of conditions, and the disclaimer that follows.
# 
#   o Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions, and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
# 
#   o All advertising materials mentioning features or use of this
#     software must display the following acknowledgement:
# 
#       This product includes software developed by Digital Creations
#       and its contributors.
# 
#   o Neither the name of Digital Creations nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
# 
# 
# THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS AND CONTRIBUTORS *AS IS*
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL
# CREATIONS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
# TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.
#
# 
# If you have questions regarding this software, contact:
#
#   Digital Creations, L.C.
#   910 Princess Ann Street
#   Fredericksburge, Virginia  22401
#
#   info@digicool.com
#
#   (540) 371-6909
#
##############################################################################
__doc__='''Variable insertion parameters

    When inserting variables, parameters may be specified to
    control how the data will be formatted.  In HTML source, the
    'fmt' parameter is used to specify a C-style or custom format
    to be used when inserting an object.  In EPFS source, the 'fmt'
    parameter is only used for custom formats, a C-style format is
    specified after the closing parenthesis.

    Custom formats

       A custom format is used when outputing user-defined
       objects.  The value of a custom format is a method name to
       be invoked on the object being inserted.  The method should
       return an object that, when converted to a string, yields
       the desired text.  For example, the HTML source::

          <!--#var date fmt=DayOfWeek-->

       Inserts the result of calling the method 'DayOfWeek' of the
       object bound to the variable 'date', with no arguments.

       In addition to object methods, serveral additional custom
       formats are available:

           'whole-dollars' -- Show a numeric value with a dollar symbol.

           'dollars-and-cents' -- Show a numeric value with a dollar
             symbol and two decimal places.

           'collection-length' -- Get the length of a collection of objects.

       Note that when using the EPFS source format, both a
       C-style and a custom format may be provided.  In this case,
       the C-Style format is applied to the result of calling
       the custom formatting method.

    Null values

       In some applications, and especially in database applications,
       data variables may alternate between "good" and "null" or
       "missing" values.  A format that is used for good values may be
       inappropriate for null values.  For this reason, the 'null'
       parameter can be used to specify text to be used for null
       values.  Null values are defined as values that:

         - Cannot be formatted with the specified format, and

         - Are either the special Python value 'None' or 
	   are false and yield an empty string when converted to
	   a string.

       For example, when showing a monitary value retrieved from a
       database that is either a number or a missing value, the
       following variable insertion might be used::

           <!--#var cost fmt="$%.2d" null=\'n/a\'-->

    String manipulation

       A number of special attributes are provided to transform the
       value after formatting has been applied.  These parameters
       are supplied without arguments.

       'lower' --  cause all upper-case letters to be converted to lower case. 

       'upper' --  cause all upper-case letters to be converted to lower case. 

       'capitalize' -- cause the first character of the inserted value
       to be converted to upper case. 

       'spacify' -- cause underscores in the inserted value to be
       converted to spaces.

       'thousands_commas' -- cause commas to be inserted every three
       digits to the left of a decimal point in values containing
       numbers.  For example, the value, "12000 widgets" becomes
       "12,000 widgets".

       'html_quote' -- convert characters that have special meaning
       in HTML to HTML character entities.

       'url_quote' -- convert characters that have special meaning
       in URLS to HTML character entities using decimal values.

       'sql_quote' -- Convert single quotes to pairs of single
       quotes. This is needed to safely include values in
       Standard Query Language (SQL) strings.

       'newline_to_br' -- Convert newlines and carriage-return and
       newline combinations to break tags.

    Truncation

       The attributes 'size' and 'etc'  can be used to truncate long
       strings.  If the 'size' attribute is specified, the string to
       be inserted is truncated at the given length.  If a space
       occurs in the second half of the truncated string, then the
       string is further truncated to the right-most space.  After
       truncation, the value given for the 'etc' attribute is added to
       the string.  If the 'etc' attribute is not provided, then '...'
       is used.  For example, if the value of spam is
       '"blah blah blah blah"', then the tag       
       '<!--#var spam size=10-->' inserts '"blah blah ..."'.


Evaluating expressions without rendering results

   A 'call' tag is provided for evaluating named objects or expressions
   without rendering the result.
   

''' # '
__rcs_id__='$Id: DT_Var.py,v 1.16 1998/09/02 14:35:54 jim Exp $'
__version__='$Revision: 1.16 $'[11:-2]

from DT_Util import *
import ts_regex
from string import find, split, join

class Var: 
    name='var'
    expr=None

    def __init__(self, args, fmt='s'):
	args = parse_params(args, name='', lower=1, upper=1, expr='',
			    capitalize=1, spacify=1, null='', fmt='s',
			    size=0, etc='...', thousands_commas=1,
			    html_quote=1, url_quote=1, sql_quote=1,
			    newline_to_br=1)
	self.args=args
	
	self.modifiers=tuple(
	    map(lambda t: t[1],
		filter(lambda m, args=args, used=args.has_key:
		       used(m[0]) and args[m[0]],
		       modifiers)))

	name, expr = name_param(args,'var',1)

	self.__name__, self.expr = name, expr
	self.fmt = fmt

	if len(args)==1 and fmt=='s':
	    if expr is None: expr=name
	    else: expr=expr.eval
	    self.simple_form=expr,

    def render(self, md):
	name=self.__name__
	val=self.expr
	if val is None:
	    val = md[name]
	else:
	    val=val.eval(md)

	args=self.args
	have_arg=args.has_key

	__traceback_info__=name, val, args

	# handle special formats defined using fmt= first
	if have_arg('fmt'):
	    fmt=args['fmt']
	    if have_arg('null') and not val and val != 0:
		try:
		    if hasattr(val, fmt):
			val = getattr(val,fmt)()
		    elif special_formats.has_key(fmt):
			val = special_formats[fmt](val, name, md)
		    elif fmt=='': val=''
		    else: val = fmt % val
		except:
		    t, v = sys.exc_type, sys.exc_value
		    if val is None or not str(val): return args['null']
		    raise t, v

	    else:
		# We duplicate the code here to avoid exception handler
		# which tends to screw up stack or leak
		if hasattr(val, fmt):
		    val = getattr(val,fmt)()
		elif special_formats.has_key(fmt):
		    val = special_formats[fmt](val, name, md)
		elif fmt=='': val=''
		else: val = fmt % val

	# finally, pump it through the actual string format...
	fmt=self.fmt
	if fmt=='s': val=str(val)
	else: val = ('%'+self.fmt) % (val,)

	# next, look for upper, lower, etc
	for f in self.modifiers: val=f(val)

	if have_arg('size'):
	    size=args['size']
	    try: size=atoi(size)
	    except: raise 'Document Error',(
		'''a <code>size</code> attribute was used in a <code>var</code>
		tag with a non-integer value.''')
	    if len(val) > size:
		val=val[:size]
		l=rfind(val,' ')
		if l > size/2:
		    val=val[:l+1]
		if have_arg('etc'): l=args['etc']
		else: l='...'
		val=val+l

	return val

    __call__=render

class Call: 
    name='call'
    expr=None

    def __init__(self, args):
	args = parse_params(args, name='', expr='')
	name, expr = name_param(args,'call',1)
	if expr is None: expr=name
	else: expr=expr.eval
	self.simple_form=expr,None


def html_quote(v, name='(Unknown name)', md={},
	       character_entities=(
		       (('&'), '&amp;'),
		       (("<"), '&lt;' ),
		       ((">"), '&gt;' ),
		       (('"'), '&quot;'))): #"
        text=str(v)
	for re,name in character_entities:
            if find(text, re) >= 0: text=join(split(text,re),name)
	return text

def url_quote(v, name='(Unknown name)', md={}):
    import urllib
    return urllib.quote(str(v))

def newline_to_br(v, name='(Unknown name)', md={},
                  nl=ts_regex.compile('\r?\n')):
    return gsub(nl,'<br>\n',str(v))

def whole_dollars(v, name='(Unknown name)', md={}):
    try: return "$%d" % v
    except: return ''

def dollars_and_cents(v, name='(Unknown name)', md={}):
    try: return "$%.2f" % v
    except: return ''

def thousands_commas(v, name='(Unknown name)', md={},
                     thou=ts_regex.compile("\([0-9]\)\([0-9][0-9][0-9]\([,.]\|$\)\)")):
    v=str(v)
    while thou.search(v) >= 0:
	v=sub(thou,"\\1,\\2",v)
    return v
    
def whole_dollars_with_commas(v, name='(Unknown name)', md={}):
    try: v= "$%d" % v
    except: v=''
    return thousands_commas(v)

def dollars_and_cents_with_commas(v, name='(Unknown name)', md={}):
    try: v= "$%.2f" % v
    except: v= ''
    return thousands_commas(v)

def len_format(v, name='(Unknown name)', md={}):
    return str(len(v))

def len_comma(v, name='(Unknown name)', md={}):
    return thousands_commas(str(len(v)))

StructuredText=None
def structured_text(v, name='(Unknown name)', md={}):
    global StructuredText
    if StructuredText is None: import StructuredText
    return str(StructuredText.html_with_references(str(v), 3))

def sql_quote(v, name='(Unknown name)', md={}):
    """Quote single quotes in a string by doubling them.

    This is needed to securely insert values into sql
    string literals in templates that generate sql.
    """
    if find(v,"'") >= 0: return join(split(v,"'"),"''")
    return v

special_formats={
    'whole-dollars': whole_dollars,
    'dollars-and-cents': dollars_and_cents,
    'collection-length': len_format,
    'structured-text': structured_text,

    # The rest are depricated:
    'sql-quote': sql_quote,
    'html-quote': html_quote,
    'url-quote': url_quote,
    'multi-line': newline_to_br,
    'comma-numeric': thousands_commas,
    'dollars-with-commas': whole_dollars_with_commas,
    'dollars-and-cents-with-commas': dollars_and_cents_with_commas,
    }

def spacify(val): return gsub('_', ' ', val)

modifiers=(html_quote, url_quote, newline_to_br, lower, upper,
	   capitalize, spacify, thousands_commas, sql_quote)
modifiers=map(lambda f: (f.__name__, f), modifiers)


############################################################################
# $Log: DT_Var.py,v $
# Revision 1.16  1998/09/02 14:35:54  jim
# open source copyright
#
# Revision 1.15  1998/08/11 19:36:54  jim
# Made use (or non-use) of regex thread safe.
#
# Revision 1.14  1998/04/14 11:58:21  jim
# Fixed bug in handling: %(foo)d
# and in handling <!--#var foo--> where foo is a tuple.
#
# Revision 1.13  1998/04/02 19:06:21  jim
# *** empty log message ***
#
# Revision 1.12  1998/04/02 17:37:38  jim
# Major redesign of block rendering. The code inside a block tag is
# compiled as a template but only the templates blocks are saved, and
# later rendered directly with render_blocks.
#
# Added with tag.
#
# Also, for the HTML syntax, we now allow spaces after # and after end
# or '/'.  So, the tags::
#
#   <!--#
#     with spam
#     -->
#
# and::
#
#   <!--#
#     end with
#     -->
#
# are valid.
#
# Revision 1.11  1998/03/24 20:21:39  jim
# Added 'call' tag.
#
# Revision 1.10  1998/03/10 20:32:32  jim
# Fixed miss-spelling of newline_to_br
#
# Revision 1.9  1998/01/12 16:47:34  jim
# Changed a number of custom formats to modifiers, since they can
# be applies cumulatively.
# Updated documentation.
#
# Revision 1.8  1998/01/08 20:57:34  jim
# *** empty log message ***
#
# Revision 1.7  1998/01/05 21:23:01  jim
# Added support for fmt="" to allow vars with side effects.
#
# Revision 1.6  1997/12/12 16:19:06  jim
# Added additional special formats, structured-text and sql-quote.
# Also changed the way formats are handled.  This has (and will)
# reveal now hidden fmt=invalid-thing errors.
#
# Revision 1.5  1997/10/27 17:39:27  jim
# removed a comment burp.
#
# Revision 1.4  1997/10/23 14:27:47  jim
# Added truncation support via size and etc attributes.
#
# Revision 1.3  1997/10/23 13:30:16  jim
# Added comma-numeric format.
#
# Revision 1.2  1997/09/22 14:42:51  jim
# added expr
#
# Revision 1.1  1997/08/27 18:55:44  jim
# initial
#
#
