
__doc__="""Application management component"""
__version__='$Revision: 1.1 $'[11:-2]


import sys,os,time,Globals
from Acquisition import Acquirer
from Management import Management
from Globals import ManageHTMLFile

class ApplicationManager(Acquirer,Management):
    """Application management component."""

    manage_main    =ManageHTMLFile('App/appMain')
    manage_packForm=ManageHTMLFile('App/pack')
    manage_undoForm=ManageHTMLFile('App/undo')

    manage_options=(
    {'icon':'App/arrow.jpg', 'label':'Application Manager',
     'action':'manage_main',   'target':'manage_main'},
    {'icon':'App/arrow.jpg', 'label':'Compact Database',
     'action':'manage_packForm','target':'manage_main'},
    {'icon':'App/arrow.jpg','label':'Undo Changes',
     'action':'manage_undoForm','target':'manage_main'},
    )

    title        ='Application Manager'
    name         ='application manager'
    process_id   =os.getpid()
    process_start=int(time.time())

    def parentObject(self):
	try:    return (self.aq_parent,)
	except: return ()

    def process_time(self):
        s=int(time.time())-self.process_start   
        d=int(s/86400)
        s=s-(d*86400)
        h=int(s/3600)
        m=int((s-(h*3600))/60)
        d=d and ('%s day%s'  % (d,(d!=1 and 's' or ''))) or ''
        return '%s %02d:%02d' % (d,h,m)

    def db(self):      return Globals.Bobobase

    def db_name(self): return Globals.BobobaseName

    def db_size(self):
        s=os.stat(self.db_name())[6]
	if s >= 1048576.0: return '%.1fM' % (s/1048576.0)
        return '%.1fK' % (s/1024.0)

    def manage_shutdown(self):
        """Shut down the application"""
	sys.exit(0)

    def revert_points(self): return ()
