#!/opt/cont/bin/python
# Server for Continuity


import sys
import os
from os import *
from select import *
from socket import *
from sys import *
from time import *
import string
from cont_classes.HelperUtilities import DynamicBinPathCreator


if "linux" in sys.platform: #XXX:and we are trying to run this on a rocks system...
    from server.SetupServerPaths import SetupServerPaths
    SetupServerPaths()
    try:
      import server.mpi as mpi
    except:
      print "Could not import mpi!!!"
    import gethostname
    hostname = gethostname.gethostname()
    print "starting ContinuityDaemon.py on %s with pid %s"%(hostname,os.getpid())

currentPyVersion = "2.7"

if sys.version[0:3] != currentPyVersion:
    if "linux" in sys.platform:
        sys.stderr.write("Not run with python version %s!  Attempting to run at /opt/cont/bin/python.  If this fails as well, you should put a symbolic link at this location to python version %s.\n"%(currentPyVersion,currentPyVersion))
        os.system("/opt/cont/bin/python ContinuityDaemon.py")
    else:
        sys.stderr.write("Not run with python version %s!  On windows, set environment variable CONTPYTHON to be the directory of python %s, and restart your system."(currentPyVersion, currentPyVersion))
    sys.exit(1)

# Initialize python relative to the location of the pcty directory
#    this allows users to have their own copies of the server
#    independent of the global one
# Adds the path to the particular local copy of the pcty directory
#    in which this file is located to the users path. This has
#    the same effect as setting the PYTHONPATH environment variable.
path = string.splitfields( sys.argv[0], '/' )[:-3]
path = string.joinfields( path, '/' )
if path == '':
  path = '.'
if path not in sys.path:
  sys.path.insert(0,path)

# Setup Continuity Path for the rest of the program

import os
cwd = os.getcwd()
if 'win32' in sys.platform:
  contPath = cwd[:cwd.rfind("\\")]
  mglToolsDir = "MglToolsLibWin"
else:
  contPath = cwd[:cwd.rfind("/")]
  mglToolsDir = "MglToolsLibLinux"

if not os.access(contPath+"//pcty", os.F_OK): #if not run from a directory with path
  sys.stderr.write("Warning, ran from directory other than continuity root!, %s; %s\n"%(os.getcwd(),sys.argv))
  if 'CONTINUITYPATH' in os.environ.keys():
    contPath = os.environ['CONTINUITYPATH']
  else:
    sys.stderr.write("Warning!  CONTINUITYPATH not defined!  This environment variable should be the path of the directory that contains pcty.\n")
    if 'win32' in sys.platform:
      contPath = "C:/Python23\\lib\\site-packages\\"
    elif 'linux' in sys.platform:
      contPath = "/usr/local/lib/python2.23/site-packages/"
      contPath = '/'.join(sys.argv[0].split('/')[:-2])
      os.chdir(contPath)
    sys.stderr.write("Pretending that your path was set to: %s though this probably won't work.  You need to set the CONTINUITYPATH environment variable.\n"%contPath)
else:
  print "Running from directory with pcty"
  os.environ['CONTINUITYPATH'] = contPath
sys.stderr.write("Using CONTINUITYPATH: %s\n"%contPath)
sys.path.insert(0,"%s"%contPath)
sys.path.insert(0,"%s/pcty/%s"%(contPath, mglToolsDir))
#sys.path.insert(0,"%s/pcty/%s/numpy"%(contPath,mglToolsDir))
sys.path.insert(0,"%s/pcty/%s/PIL"%(contPath,mglToolsDir))


from client.forms.updateServerBinaries import checkBinaryTime,doBinaryUpdate
try:
    upToDate = checkBinaryTime() #simply will fail in distributed version
except Exception, msg:
    #print "exception:", msg
    upToDate = True

if '--update-binaries' in sys.argv:
    doBinaryUpdate()
elif not upToDate:
    print "Server binaries are not up to date!  You should run with '--update-binaries' flag!"


from pcty.server.cont_server import Cont_Server
from pcty.cont_classes.ContCom import *

activeServers = []

class ContinuityDaemon(ContCom):
  def __init__( self, threads, database, mpi ):
    self.mpi = mpi
    # Need to make sure that the location of binaries is in the python path
    dynamicBinPath = DynamicBinPathCreator()
    dynamicBinPath.create()    
    PythonVersion = sys.version
    self.database = database
    self.threads = threads
    self.activeServers = []
    ContCom.__init__(self, DAEMON, threads=threads )

  def mainLoop( self, server ):
    start = 1
    while start:
      connection, address = self.conn.accept()
      name = address[0] + ':' + str(address[1])
      acceptTime = strftime("%m/%d/%y %H:%M:%S", localtime(time()))
      print acceptTime, name
      self.waitServers()
      if ( server ):
        serverPid = fork()
      else:
        serverPid = 0
      #end if
      if ( serverPid == 0 ):
        cs = Cont_Server( Daemon = self, database = self.database, mpi = self.mpi )
        self.conn = connection
        self.addr = address
        if ( self.threads ):
          self.startcomm()
        #end if
        cs.mainLoop( )
        if ( self.threads ):
          self.close()
        start = 0
      else:
        activeServers.append( serverPid )
      #end if
    #end while
  #end def main

  def waitServers( self ):
    while activeServers:
      pid,stat = waitpid( 0, WNOHANG )
      if not pid:
        break
      print 'Removing server: ',pid
      activeServers.remove( pid )
  #end def waitServers
#end class ContinuityDaemon

def main( server, threads, database, mpi ):
  cd = ContinuityDaemon( threads, database, mpi )
  cd.mainLoop( server )
  os._exit(0)
#end def main
  
if __name__ == '__main__':
  # Single server is default
  server = 0
  
  """ Look for command line arguments """
  if (( '-h' in sys.argv) or ('--help' in sys.argv) ):
    print 'ContinuityDaemon [single/multi] \n'
    print '[-h/--help]\t\tDisplay this help'
    print '[--multi]\t\t\tRun multiple servers'
    print '[--no-threads]\t\tRun Server with no threads'
    print '[--single]\t\tRun single server, this the default'
    print '[--database]\t\tRun multiuser database server'
    print '[--update-binaries]\t\tUpdate Server Binaries'
    sys.exit(0)
  #end if
  server =  '--multi' in sys.argv
  database = '--database' in sys.argv
  threads = not '--no-threads' in sys.argv
  main( server, threads, database, None )

#end main
