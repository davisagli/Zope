
"""Rendering object hierarchies as Trees
"""
############################################################################
#     Copyright 
#
#       Copyright 1997 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved. 
#
############################################################################ 
__rcs_id__='$Id: TreeTag.py,v 1.15 1997/12/04 23:30:29 brian Exp $'
__version__='$Revision: 1.15 $'[11:-2]

from DocumentTemplate.DT_Util import *
from DocumentTemplate.DT_String import String

from string import join, split, rfind, find
from urllib import quote, unquote
from zlib import compress, decompress
from binascii import b2a_base64, a2b_base64

class Tree:
    name='tree'
    blockContinuations=()
    expand=None

    def __init__(self, blocks):
	tname, args, section = blocks[0]
	args=parse_params(args, name=None, expr=None,
			  expand=None, leaves=None,
			  header=None, footer=None,
			  nowrap=1, branches=None, sort=None)
	has_key=args.has_key

	if has_key('name'): name=args['name']
	elif has_key(''): name=args['name']=args['']
	else: name='a tree tag'

	if not has_key('branches'): args['branches']='tpValues'
	
	self.__name__ = name
	self.section=section
	self.args=args
	if args.has_key('expr'):
	    if args.has_key('name'):
		raise ParseError, _tm('name and expr given', 'tree')
	    args['expr']=VSEval.Eval(args['expr'], expr_globals)
	    

    def render(self,md):
	args=self.args
	have=args.has_key

	if have('name'): v=md[args['name']]
	elif have('expr'): v=args['expr'].eval(md)
	else: v=md.this
	return tpRender(v,md,self.section, self.args)

    __call__=render

String.commands['tree']=Tree

pyid=id # Copy builtin

def tpRender(self, md, section, args):
    """Render data organized as a tree.

    We keep track of open nodes using a cookie.  The cookie stored the
    tree state. State should be a tree represented like:

      []  # all closed
      ['eagle'], # eagle is open
      ['eagle'], ['jeep', [1983, 1985]]  # eagle, jeep, 1983 jeep and 1985 jeep

    where the items are object ids. The state will be converted to a
    compressed and base64ed string that gets unencoded, uncompressed, 
    and evaluated on the other side.

    Note that ids used in state need not be connected to urls, since
    state manipulation is internal to rendering logic.

    Note that to make eval safe, we do not allow the character '*' in
    the state.
    """

    data=[]

    if hasattr(self, 'tpId'): id=self.tpId()
    elif hasattr(self, '_p_oid'): id=self._p_oid
    else: id=pyid(self)

    try:
	# see if we are being run as a sub-document
	root=md['tree-root-url']
	url=md['tree-item-url']
	state=md['tree-state']
	diff=md['tree-diff']
	substate=md['-tree-substate-']
	colspan=md['tree-colspan']	
	level=md['tree-level']

    except KeyError:
	# OK, we are a top-level invocation
	level=-1

	if md.has_key('collapse_all'):
	    state=[id,[]],
	elif md.has_key('expand_all'):
	    state=[id, tpValuesIds(self, args['branches'])],
	else:
	    if md.has_key('tree-s'):
		state=md['tree-s']
		state=decode_seq(state)
		try:
		    if state[0][0] != id: state=[id,[]],
		except IndexError: state=[id,[]],
	    else: state=[id,[]],

	    if md.has_key('tree-e'):
		diff=decode_seq(md['tree-e'])
		apply_diff(state, diff, 1)

	    if md.has_key('tree-c'):
		diff=decode_seq(md['tree-c'])
		apply_diff(state, diff, 0)

	colspan=tpStateLevel(state)
	substate=state
	diff=[]

	url=''
	root=md['URL']
	l=rfind(root,'/')
	if l >= 0: root=root[l+1:]

    treeData={'tree-root-url': root,
	      'tree-colspan': colspan,
	      'tree-state': state }
    
    md._push(treeData)

    try: tpRenderTABLE(self,id,root,url,state,substate,diff,data,colspan,
		       section,md,treeData, level, args)
    finally: md._pop(1)

    if state is substate:
	state=state or ([id],)
	state=encode_seq(state)
	md['RESPONSE'].setCookie('tree-s',state)

    return join(data,'')

def tpRenderTABLE(self, id, root_url, url, state, substate, diff, data,
                  colspan, section, md, treeData, level=0, args=None):
    "Render a tree as a table"

    have_arg=args.has_key

    if level >= 0:
	tpUrl=self.tpURL()
	url = (url and ('%s/%s' % (url, tpUrl))) or tpUrl
	root_url = root_url or tpUrl

    treeData['tree-item-url']=url
    treeData['tree-level']=level
    treeData['tree-item-expanded']=0

    exp=0
    sub=None
    output=data.append

    try:    items=getattr(self, args['branches'])()
    except: items=None
    if not items and have_arg('leaves'): items=1

    if (args.has_key('sort')) and (items is not None) and (items != 1):
	# Faster/less mem in-place sort
	sort=args['sort']
	size=range(len(items))
	for i in size:
	    v=items[i]
	    k=getattr(v,sort)
	    try:    k=k()
	    except: pass
	    items[i]=(k,v)
	items.sort()
	for i in size:
	    items[i]=items[i][1]

    diff.append(id)

    if substate is state:
	output('<TABLE CELLSPACING="0">\n')
	sub=substate[0]
	exp=items
    else:
	# Add prefix
	output('<TR>\n')

	# Add +/- icon
	if items:
	    if level:
		if level > 3: output(  '<TD COLSPAN="%s"></TD>' % (level-1))
		elif level > 1: output('<TD></TD>' * (level-1))
		output('<TD WIDTH="16"></TD>\n')
	    output('<TD WIDTH="16" VALIGN="TOP">')
	    for i in range(len(substate)):
		sub=substate[i]
		if sub[0]==id:
		    exp=i+1
		    break

	    ####################################
	    # Mostly inline encode_seq for speed
	    s=compress(str(diff))
	    if len(s) > 57: s=encode_str(s)
	    else:
		s=b2a_base64(s)[:-1]
		l=find(s,'=')
		if l >= 0: s=s[:l]
	    ####################################


	    if exp:
		treeData['tree-item-expanded']=1
		output('<A HREF="%s?tree-c=%s">%s</A>' %
		       (root_url,s, icoMinus))
	    else:
		output('<A HREF="%s?tree-e=%s">%s</A>' %
		       (root_url,s, icoPlus))
	    output('</TD>\n')
	else:
	    if level > 2: output('<TD COLSPAN="%s"></TD>' % level)
	    elif level > 0: output('<TD></TD>' * level)
	    output('<TD WIDTH="16"></TD>\n')
	    
    
	# add item text
	dataspan=colspan-level
	output('<TD%s%s VALIGN="TOP">' %
	       ((dataspan > 1 and (' COLSPAN="%s"' % dataspan) or ''),
	       (have_arg('nowrap') and args['nowrap'] and ' NOWRAP' or ''))
	       )
	output(section(self, md))
	output('</TD>\n</TR>\n')


    if exp:

	level=level+1
	dataspan=colspan-level
	if level > 3: h='<TD COLSPAN="%s"></TD>' % (level-1)
	elif level > 1: h='<TD></TD>' * (level-1)
	else: h=''

	if have_arg('header'):
	    if md.has_key(args['header']):
		output(md.getitem(args['header'],0)(
		    self, md,
		    standard_html_header=(
			'<TR>%s<TD WIDTH="16"></TD>'
			'<TD%s VALIGN="TOP">'
			% (h,
			   (dataspan > 1 and (' COLSPAN="%s"' % dataspan)
			    or ''))),
		    standard_html_footer='</TD></TR>',
		    ))
	    
	if items==1:
	    # leaves
	    treeData['-tree-substate-']=sub
	    treeData['tree-level']=level
	    md._push(treeData)
	    output(md.getitem(args['leaves'],0)(
		self,md,
		standard_html_header=(
		    '<TR>%s<TD WIDTH="16"></TD>'
		    '<TD%s VALIGN="TOP">'
		    % (h,
		       (dataspan > 1 and (' COLSPAN="%s"' % dataspan) or ''))),
		standard_html_footer='</TD></TR>',
		))
	    md._pop(1)
	elif have_arg('expand'):
	    treeData['-tree-substate-']=sub
	    treeData['tree-level']=level
	    md._push(treeData)
	    output(md.getitem(args['expand'],0)(self,md))
	    md._pop(1)
	else:
	    __traceback_info__=sub, args, state, substate
	    ids={}
	    for item in items:
		if hasattr(item, 'tpId'): id=item.tpId()
		elif hasattr(item, '_p_oid'): id=item._p_oid
		else: id=pyid(item)
		if len(sub)==1: sub.append([])
		substate=sub[1]
		ids[id]=1
		data=tpRenderTABLE(
		    item,id,root_url,url,state,substate,diff,data,
		    colspan, section, md, treeData, level, args)
		if not sub[1]: del sub[1]

	    ids=ids.has_key
	    for i in range(len(substate)-1,-1):
		if not ids(substate[i][0]): del substate[i]

	if have_arg('footer'):
	    if md.has_key(args['footer']):
		output(md.getitem(args['footer'],0)(
		    self, md,
		    standard_html_header=(
			'<TR>%s<TD WIDTH="16"></TD>'
			'<TD%s VALIGN="TOP">'
			% (h,
			   (dataspan > 1 and (' COLSPAN="%s"' % dataspan)
			    or ''))),
		    standard_html_footer='</TD></TR>',
		    ))

    del diff[-1]
    if not diff: output('</TABLE>\n')

    return data


def apply_diff(state, diff, expand):
    if not diff: return
    s=[None, state]
    diff.reverse()
    __traceback_info__=s, diff
    while diff:
	id=diff[-1]
	del diff[-1]
	if len(s)==1: s.append([])
	s=s[1]
	loc=-1
	for i in range(len(s)):
	    if s[i][0]==id:
		loc=i
		break

	if loc >= 0:
	    if not diff and not expand:
		del s[loc]
	    else:
		s=s[loc]
	elif diff or expand:
	    s.append([id,[]])
	    s=s[-1][1]
	    while diff:
		id=diff[-1]
		del diff[-1]
		if diff or expand:
                    s.append([id,[]])
                    s=s[-1][1]


def encode_seq(state):
    "Convert a sequence to an encoded string"
    state=compress(str(state))
    l=len(state)

    if l > 57:
	states=[]
	for i in range(0,l,57):
	    states.append(b2a_base64(state[i:i+57])[:-1])
	state=join(states,'')
    else: state=b2a_base64(state)[:-1]

    l=find(state,'=')
    if l >= 0: state=state[:l]
	
    return state

def encode_str(state):
    "Convert a sequence to an encoded string"
    l=len(state)

    if l > 57:
	states=[]
	for i in range(0,l,57):
	    states.append(b2a_base64(state[i:i+57])[:-1])
	state=join(states,'')
    else: state=b2a_base64(state)[:-1]

    l=find(state,'=')
    if l >= 0: state=state[:l]
	
    return state

def decode_seq(state):
    "Convert an encoded string to a sequence"

    l=len(state)

    if l > 76:
	states=[]
	j=0
	for i in range(l/76):
	    k=j+76
	    states.append(a2b_base64(state[j:k]))
	    j=k

	if j < l:
	    state=state[j:]
	    l=len(state)
	    k=l%4
	    if k: state=state+'='*(4-k)
	    states.append(a2b_base64(state))
	state=join(states,'')
    else:
	l=len(state)
	k=l%4
	if k: state=state+'='*(4-k)
	state=a2b_base64(state)

    state=decompress(state)
    if find(state,'*') >= 0: raise 'Illegal State', state
    try: return list(eval(state,{'__builtins__':{}}))
    except: return []
    

def tpStateLevel(state, level=0):
    for sub in state:
        if len(sub)==2: level = max(level, 1+tpStateLevel(sub[1]))
        else: level=max(level,1)
    return level

def tpValuesIds(self, branches):
    # This should build the ids of subitems which are
    # expandable (non-empty). Leaves should never be
    # in the state - it will screw the colspan counting.
    r=[]
    try:
	try: items=getattr(self, branches)()
	except AttributeError: items=()
	for item in items:
	    try:
		if getattr(item, branches)():

		    if hasattr(item, 'tpId'): id=item.tpId()
		    elif hasattr(item, '_p_oid'): id=item._p_oid
		    else: id=pyid(item)

		    e=tpValuesIds(item, branches)
		    if e: id=[id,e]
		    else: id=[id]
		    r.append(id)
	    except: pass
    except: pass
    return r
    

icoSpace='<IMG SRC="%s/TreeDisplay/Blank_icon.gif" BORDER="0">' % SOFTWARE_URL
icoPlus ='<IMG SRC="%s/TreeDisplay/Plus_icon.gif" BORDER="0">' % SOFTWARE_URL
icoMinus='<IMG SRC="%s/TreeDisplay/Minus_icon.gif" BORDER="0">' % SOFTWARE_URL











