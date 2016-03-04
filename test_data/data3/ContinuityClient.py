#!/usr/bin/env python
import sys
import string
import warnings
import cPickle
import shutil
from client.PrefsManager import GetPreference
from cont_classes.HelperUtilities import DynamicBinPathCreator
from platform import uname

currentPyVersion = "2.7"
currentPythonLink = "http://www.python.org/ftp/python/2.5.2/python-2.5.2.msi"
warnings.simplefilter("ignore")


def handleWrongPythonVersion():
    from PromptString import showHyperMessage
    from tkMessageBox import showerror
    from Tkinter import Tk
    root = Tk()
    root.withdraw()

    try:
        from checkRegistry import getPythonPath, setEnviron
        pythonPath = getPythonPath()
    except Exception, msg:
        errorMessage = "Could not find python %s installed on your system.\n"\
                       "Please install python %s before attempting to run Continuity:\n %s \n"%(currentPyVersion, currentPyVersion, currentPythonLink)
        errorMessage += "\n%s"%msg
        showHyperMessage("Python %s required!"%currentPyVersion, errorMessage)
        sys.exit(1)
    try:
        setEnviron("CONTPYTHON",pythonPath)
    except Exception, msg:
        errorMessage = "Could not find python %s installed on your system.\n"\
                       "Please install python %s before attempting to run Continuity:\n %s \n"%(currentPyVersion, currentPyVersion, currentPythonLink)
        errorMessage += "\n%s"%msg
        showHyperMessage("Python %s required!"%currentPyVersion, errorMessage)
        sys.exit(1)

    version = sys.version.split()[0]
    errorMessage = "Continuity was just run with an incompatible version of python (%s).\n"\
                   "The correct version, however, was found at %s.\n"\
                   "Please restart your system, and run Continuity from ContinuityClient.bat in your installation directory."%(version,pythonPath)
    showerror("Python %s required!"%currentPyVersion, errorMessage)


import os
cwd = os.getcwd()
if 'win32' in sys.platform:
  contPath = cwd[:cwd.rfind("\\")]
  mglToolsDir = "MglToolsLibWin"
else:
  contPath = cwd[:cwd.rfind("/")]
  mglToolsDir = "MglToolsLib"

def mgl_lib():
    pf = uname()[0]
    if "Microsoft" in pf or "Windows" in pf: 
        if '64' in uname()[4]:
            return "64winlib"
        else:
            return "winlib"
    elif "Linux" in pf:
        if "64" in uname()[4]: 
            return "64linuxlib"
        else: 
            return "linuxlib"
    elif "Darwin" in pf:
        if "i386" in uname()[4]:
            if uname()[2].startswith("8"):
                return "i386tigerlib"
            else:
                return "64darwinlib"
        else: 
            return "64darwinlib"

def mgl_uptodate():
    pf = mgl_lib()
    mglrevold="%s/pcty/%s/mglrevision"%(contPath, mglToolsDir)
    mglrevnew="%s/pcty/client/mglrevision.dat"%(contPath)
    oldrev = 0
    newrev = int(dict(map(lambda s: s.strip().split(':='), open(mglrevnew).readlines()))[pf])
    if os.path.exists(mglrevold):
        oldrev = int(open(mglrevold).readline())
        if oldrev < newrev: return [False, newrev]
    else: return [False, newrev]

    return [True, newrev]

def updateMgl(doSplash = True):
    from tkMessageBox import showinfo
    if 'win32' in sys.platform:
        from cont_classes.unzip import unzip
        extracter = unzip()
        arch = contPath+"/%s/MglToolsLibWin.zip" % mgl_lib()
    else:
        showinfo("Cannot update automatically on this system...",'Please click OK, and then run "updatemgl" from your continuity root directory.')
        sys.exit(0)

    sys.stderr.write("\n\t*** Please wait, the mgltools update may take a while...\n")
    import shutil
    try:
        extracter.extract(arch,contPath)
    except IOError, (errno, strerror):
        from tkMessageBox import showerror
        showerror("Mgltools update failed!","There was a problem in extracting the archive. Please try to manually update mgltools: " + strerror)
        return

    try:
        shutil.rmtree(contPath+"/pcty/"+mglToolsDir)
    except Exception,v:
        print "Error removing old Mgltools: "+str(v)
    shutil.move(contPath+"/"+mglToolsDir, contPath+"/pcty/" + mglToolsDir)
    sys.stderr.write("\n\t*** Update complete!\n")
    if doSplash:
        showinfo("Update complete", "MglTools has been updated. Click OK to exit, and then run Continuity again.")
    sys.exit(0)

print "Initializing python files; please wait..."
# Initialize python relative to the location of this file
path = string.splitfields( sys.argv[0], '/' )[:-2]
path = string.joinfields( path, '/' )
if path == '':
  path = '.'

if path not in sys.path:
  sys.path.insert(0,path)

# Setup Continuity Path for the rest of the program


if not os.access(contPath+"//pcty", os.F_OK): #if not run from a directory with path
  print "Warning, ran from directory other than continuity root!"
  if 'CONTINUITYPATH' in os.environ.keys():
    contPath = os.environ['CONTINUITYPATH']
  else:
    sys.stderr.write("Warning!  CONTINUITYPATH not defined!  This environment variable should be the path of the directory that contains pcty.\n")
    if 'win32' in sys.platform:
      contPath = "C:/Python23\\lib\\site-packages\\"
    elif 'linux' in sys.platform:
      contPath = "/usr/local/lib/python2.23/site-packages/"
    sys.stderr.write("Pretending that your path was set to: %s though this probably won't work.  You need to set the CONTINUITYPATH environment variable.\n"%contPath)
else:
  os.environ['CONTINUITYPATH'] = contPath

# We also need Python in the OS path for Instant to be able to compile
if 'CONTPYTHON' in os.environ:
    os.environ['PATH'] += ';' + os.environ['CONTPYTHON']
sys.stderr.write("  *CONTINUITYPATH: %s\n"%contPath)
sys.path.insert(0,"%s"%contPath)
sys.path.insert(0,"%s/pcty/%s"%(contPath, mglToolsDir))
sys.path.insert(0,"%s/pcty/%s/Numeric"%(contPath,mglToolsDir))
sys.path.insert(0,"%s/pcty/%s/PIL"%(contPath,mglToolsDir))
sys.path.insert(0,"%s/pcty/client/forms"%contPath)
if 'win32' in sys.platform:
    # Needed when running in batch mode
    sys.path.insert(0,"%s\\pcty\\MglToolsLibWin\\pyCompilePkgs"%contPath)

if sys.version.split()[0][:3] != currentPyVersion:
    foundversion = sys.version.split()[0]
    if mgl_lib() == 'winlib':
        handleWrongPythonVersion()
    else:
        print "***Python version %s was detected, but %s is needed to run this version of Continuity.\n"%(foundversion,currentPyVersion) + \
                  'The correct python might be present in the MglTools archive, and you can update by running "updatemgl". Exiting!'
        sys.exit(0)

if sys.platform == "win32":
    try:
        from checkRegistry import checkRegistry
        checkRegistry(contPath)
    except:
        print "Error updating registry.  Perhaps not running as admin?"

def main( threads, gui=1, full=0, standAlone=0,startupFile = None, doSplash = True,withShell = 1,batch=0,openFile=None,mpi=None ):
  """ start up continuity with specified arguments """

  if True:  #default to gui client
    # Need to make sure that the location of binaries is in the python path
    dynamicBinPath = DynamicBinPathCreator()
    dynamicBinPath.create()    

    if batch:
        from client.gui_client_no_vf import ContinuityNoVF as Continuity
        if 'win32' in sys.platform:
            # needed to run properly in batch mode
            os.environ['PATH'] = "%s\\pcty\\MglToolsLibWin\\msys\\1.0\\mingw\\x86_64-w64-mingw32\\lib;"%(contPath) + os.environ['PATH']
    else:
        from client.gui_client import Continuity

    sys.ps1 = 'CONTINUITY6.4 >> '
    

    #Creates a Continuity Client instance
    cont = Continuity( threads=threads, full=full, standAlone=standAlone, doSplash = doSplash, gui = gui, withShell = withShell, mpi = mpi )
    global self
    self = cont  #give gui python shell access to Continuity instance
    from pcty.client.forms.SafeDialog import SafeDialog
    SafeDialog.vf = cont
    if openFile != None:
        cont.Load_File(openFile)

    if startupFile != None:
      try:
        #execfile(startupFile)
        if startupFile[:5] == "pcty/": startupFile = startupFile[5:]
        self.source(startupFile, log = 0)
        print "startupFile loaded successfully"
        if batch:
            cont.Reset(('Server'), log=0)
            cont.closeCommunications()
      except Exception, detail:
        print "Error in startupFile: ", detail
        import traceback
        traceback.print_exc()
    cont.mainloop()
#end def main

def findIn(myList, myStr):
  #return element of myList which has an entry that contains myStr
  #if it's not found return None
  for i, elem in enumerate(myList):
    if myStr in elem:
      return elem
  return None


  return len(filter(lambda x:x, (map(lambda x:myStr in x, myList)))) > 0

def checkMgl(doSplash = True):
  from client.PrefsManager import GetPreference,SavePreference
  checkmgl = GetPreference("checkMgl")
  mglrev = GetPreference("mglRev")

  uptodate = mgl_uptodate()
  if not uptodate[0] and (checkmgl or uptodate[1] > mglrev):
    from Tkinter import Tk
    root = Tk()
    root.withdraw()
    from tkMessageBox import askyesno
    if doSplash:
        if(askyesno("Attention developers: Revised Mgltools found","Possibly due to a recent svn update, a revised version of Mgltools has been obtained. It is recommended to apply the update. Perform the update now?")):
            updateMgl(doSplash)
        else:
            from PromptString import showHyperMessage
            if(showHyperMessage("Attention developers: Revised Mgltools found", "Mgltools was not updated. You can manually apply the update yourself at a later time.\n "
                                +"Go to the link below to to read how to do this correctly. hl[0]",
                   option = "Check this box to disable this alert at startup (a subsequent revision will re-enable this alert).",
                   inserts=[("Click here","http://www.continuity.ucsd.edu/Continuity/Documentation/DeveloperDocs/UpgradingPython#mgltoolswin")])):
                SavePreference("checkMgl","0")
            else:
                SavePreference("checkMgl","1")
    
            SavePreference("mglRev",str(uptodate[1]))
    else:
        updateMgl(doSplash)

if __name__ == '__main__':
  """ look for command line arguments """
  if ('-h' in sys.argv) or ('--help' in sys.argv):
    print 'Continuity [--opt] [--unbuffered] [--no-gui] [--no-threads] [--run yourScript.py] [--no-splash] [--no-shell] [-fh] '
    print '[-h/--help]\t\tdisplay this help'
    print '[--opt]\t\t\tRemove doc strings and optimize generated Python bytecode. Must be first option specified.'
    print '[--unbuffered]\t\tForce stdin, stdout and stderr to be unbuffered: Must follow --opt or be first option listed.'
    print '[--no-gui]\t\trun commandline client'
    print '[--no-threads]\t\tRun Server with no threads'
    print '[-f/--full]\t\trun server within client (no socket communication)'
    print '[--run]\t\t\tRun specified script immediately.'
    print '[--no-splash]\t\tSuppress Splash Screen.'
    print '[--no-shell]\t\tSuppress Viewer Framework Python Shell.  \n\t\t\tRecommended if Continuity Fails on startup to diagnose problem.'
    print '[--batch]\t\tRun specified script in batch mode'
    sys.exit(0)
  #end if

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



  startupFile = None

  # use threads?
  if ( '--no-threads' in sys.argv ):
    threads = 0
  else:
    threads = 1


  # Load preferences specified by preferences form; these are overwritten by command line options
  try:
     from client.PrefsManager import GetPrefs
  except ImportError:
     import sys
     sys.path.insert(0, r'client/nogui/')
     from client.PrefsManager import GetPrefs

  # gui or no gui?
  if '--no-gui' in sys.argv:
    gui = 0
  else:  #default to gui client
    gui = 1

  # full (standalone) or client only?
  if ('full' in sys.argv) or ('-f' in sys.argv) or ('--full' in sys.argv):
    full = 1
  else:
    full = 0

  # standAlone mode is not used as far as I can tell...use full mode instead
  standAlone = 0
  if ('-s' in sys.argv) or ('--standalone' in sys.argv):
    standAlone = 1



  # Load splash?
  if '--no-splash' in sys.argv:
      doSplash = False
  else:
      doSplash = True

  # Run a startup script?
  if '--run' in sys.argv:
    startupFile = sys.argv[sys.argv.index('--run')+1]

  if '--batch' in sys.argv:
    startupFile = sys.argv[sys.argv.index('--batch')+1]
    withShell = 0
    gui = 0
    doSplash = False
    #full = 1 #probably true, but not necessarily
    batch = 1
  else:
    batch = 0

  if not gui:
    sys.path.insert(0,"client/nogui")
    
  # We need to make sure that the path to the dynamic models is in the Python path
  # regardless if they supplied a startupFile or not
  from client.PrefsManager import GetPrefs
  prefs = GetPrefs()    

  # Load preferences specified by preferences form; these are overwritten by command line options
  if not startupFile:
    from client.PrefsManager import GetPrefs
    prefs = GetPrefs()

    susFile = None
    if prefs != {}:
      if 'useThreads' in prefs.keys() and threads == 1:
        threads = prefs['useThreads']
      if 'susFile' in prefs.keys():
        susFile = prefs['susFile']
      if susFile not in (None, ''):
        startupFile = susFile
        
                    
    # Also for Windows, we need to make sure that 'swig' is in the path.
    # We will include swig with the distribution, so we want our swig to be at 
    # the front of the path
    # We can't add these to the path until mgltools actually gets installed
    if 'win32' in sys.platform and 'swigwin' not in os.environ['PATH'] and os.path.exists(contPath+'/pcty/MglToolsLibWin'):
        import win32api        
        swig_location = win32api.GetShortPathName(os.environ['CONTINUITYPATH'] + "\\pcty\\MglToolsLibWin\\swigwin-2.0.4")
        compiler_tools = win32api.GetShortPathName(os.environ['CONTINUITYPATH'] + "\\pcty\\MglToolsLibWin\\msys\\1.0\\mingw\\bin")
        current_path = os.environ['PATH']

        # Put our stuff at the front of the currently set path
        os.environ['PATH'] = swig_location + ';' + compiler_tools + ';' + current_path
        
        # We need to make sure Python can find all the required libraries, which
        # are also included in the the pyCompilePkgs dir, in addition to
        # the standard MglToolsLibWin directory
        pyCompilePath = win32api.GetShortPathName(os.environ['CONTINUITYPATH'] + "\\pcty\\MglToolsLibWin\\pyCompilePkgs")
        if pyCompilePath not in sys.path:
            sys.path.insert(0,pyCompilePath)
        
    # TODO: need to see if we need/want to implement something like this    
    # Lastly, see if there are any old binaries that we need to remove
    # These binaries are alternative compiled versions of the same model
    # We are only deleting models that have been recompiled (unless a user
    # has directly removed them previously)
    # Open existing file that holds the files we will delete on startup
    
    # The file might not exist, so catch that error
    # First see if the file exists, if not, just put an empty list into the file
    '''
    if not os.access(GetPreference('dynamicBinDir') + "old_bins_to_delete.pickle", os.F_OK):
        try:
            delete_file = open(GetPreference('dynamicBinDir') + "old_bins_to_delete.pickle", 'w')
            files_to_delete = []
            cPickle.dump(files_to_delete, delete_file)
            delete_file.close()
        except IOError, msg:
            sys.stderr.write('Warning: Issue creating empty delete list, message'%(msg))
    else:   
        files_to_delete = []
        try:
            delete_file = open(GetPreference('dynamicBinDir') + "old_bins_to_delete.pickle", 'r')
            files_to_delete = cPickle.load(delete_file)
            delete_file.close()
        except IOError, msg:
            sys.stderr.write('Issue opening pickle file (%s), message: %s'%(GetPreference('dynamicBinDir') + "old_bins_to_delete.pickle", msg))
        
        deleted_files = False
        for file in files_to_delete:
            if 'lock' in file:
                # This is a file, just delete it
                try:
                    pass
                    os.remove(GetPreference('dynamicBinDir') + "/" + file)
                except IOError, msg:
                    sys.stderr.write("ERROR removing file:  %s error is: %s"%(file, msg))
            else:
                # This is a directory, remove the entire thing including the files inside
                try:
                    shutil.rmtree(GetPreference('dynamicBinDir') + "/" + file, False)
                except IOError, msg:
                    sys.stderr.write('ERROR removing directory: %s  error is: %s'%(file, msg))
    
        # If we actually deleted some models, clear out the model list
        if len(files_to_delete) > 0:
            try:
                delete_file = open(GetPreference('dynamicBinDir') + "old_bins_to_delete.pickle", 'w')
                files_to_delete = []
                cPickle.dump(files_to_delete, delete_file)
                delete_file.close()
            except IOError, msg:
                sys.stderr.write('ERROR clearing file list, message: %s'% msg)
    '''
    

  if '--no-shell' in sys.argv:
     withShell = 0
  else:
     withShell = 1

  openFile = findIn(sys.argv, ".cont6")

  if (threads): print "  *Using Threads"
  if (threads and full):  print "Warning:  full mode does not usually work well with threads; most threading will be disabled."

  #set up correct LD_LIBRARY_PATH for binaries
  if full and "linux" in sys.platform:
    from server.addToPath import addToPath
    path = "../linuxlib/fortranLib/"
    addToPath("LD_LIBRARY_PATH",path)
    import server.fem_mesh

  if "mpiexec" in sys.argv or "mpirun" in sys.argv:
    try:
      from ContinuityMPI import ContinuityMPI
      cont_mpi = ContinuityMPI(releaseMaster = True)
    except Exception, msg:
      print "MPI not available:", msg
      mpi = None
    else:
      print "MPI available!"
      mpi = cont_mpi = cont_mpi.mpi
  else:
      print "MPI not available (not executed with mpirun or mpiexec)"
      mpi = None

  if gui and os.path.exists(contPath+'/'+mgl_lib()): 
      checkMgl(doSplash)

  # For Windows, we need to make sure we use the included versions
  # of our Python packages
  #if 'win32' in sys.platform:
  #    sys.path[0] = win32api.GetShortPathName(os.environ['CONTINUITYPATH'] + "\\pcty\\MglToolsLibWin\\pyCompilePkgs")
  main( threads, gui, full, standAlone,startupFile,doSplash = doSplash, withShell = withShell,batch=batch, openFile=openFile, mpi = mpi )


#end if __name__

"""
C Copyright (1998) The Regents of the University of California
C All Rights Reserved
C Permission to use, copy, and modify, any part of this software for
C academic purposes only, including non-profit  education and research,
C without fee, and without a written agreement is hereby granted, provided
C that the above copyright notice, this paragraph and the following three
C paragraphs appear in all copies.
C The receiving party agrees not to further distribute nor disclose the
C source code to third parties without written permission and not to use
C the software for research under commercial sponsorship or for any other
C any commercial undertaking.  Those desiring to incorporate this software
C into commercial products of to use it for commercial purposes should
C contact the Technology Transfer Office, University of California, San
C Diego, 9500 Gilman Drive, La Jolla, California, 92093-0910, Ph: (619)
C 534 5815, referring to Case SDC98008.
C IN NO EVENT SHALL THE UNIVERSITY OF CALIFORNIA BE LIABLE TO ANY PARTY
C FOR DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES,
C INCLUDING LOST PROFITS, ARISING OUT OF THE USE OF THIS SOFTWARE, EVEN IF
C THE UNIVERSITY OF CALIFORNIA HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH
C DAMAGE.
C THE SOFTWARE PROVIDED HEREUNDER IS ON AN AS IS BASIS, AND THE
C UNIVERSITY OF CALIFORNIA HAS NO OBLIGATIONS TO PROVIDE MAINTENANCE,
C SUPPORT, UPDATES, ENHANCEMENTS, OR MODIFICATIONS.  THE UNIVERSITY OF
C CALIFORNIA MAKES NO REPRESENTATIONS AND EXTENDS NO WARRANTIES OF ANY
C KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE
C IMPLIED WARRANTIES OF MECHANT ABILITY OR FITNESS FOR A PARTICULAR
C PURPOSE, OR THAT THE USE OF THE MATERIAL WILL NOT INFRINGE ANY PATENT,
C TRADEMARK OR OTHER RIGHTS.
"""
