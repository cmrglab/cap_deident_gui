#fix path problems
import sys
import os
if 'win32' in sys.platform:
    import win32api
    pyCompilePath = win32api.GetShortPathName(os.environ['CONTINUITYPATH'] + "\\pcty\\MglToolsLibWin\\pyCompilePkgs")
    if pyCompilePath not in sys.path:
        sys.path.insert(0,pyCompilePath)
        
    mingw_path = win32api.GetShortPathName(os.environ['CONTINUITYPATH'] + "\\pcty\\MglToolsLibWin\\msys\\1.0\\mingw\\bin")
    swigwin_path = win32api.GetShortPathName(os.environ['CONTINUITYPATH'] + "\\pcty\\MglToolsLibWin\\swigwin-2.0.4")
    if mingw_path not in os.environ['PATH']:
        os.environ['PATH'] =  mingw_path + ';' + os.environ['PATH']
    if swigwin_path not in os.environ['PATH']:
        os.environ['PATH'] =  swigwin_path + ';' + os.environ['PATH']    
    
        
sys.path.insert(0, ".") #XXX: This shouldn't be necessary!
sys.path.insert(0, "..") #XXX: This shouldn't be necessary!
sys.path.insert(0, "server/problem/Electrophysiology") #XXX: This shouldn't be necessary!

#some sanity checks
import pcty

#other modules
from pcty.server.mympi_API import mympi_API
import pcty.server.problem.Biomechanics.ParallelSolverBM as parallelBM
import pcty.server.problem.Electrophysiology.cont2ODEsolver_parallel as parallelEP
from cont_classes.HelperUtilities import DynamicBinPathCreator
import numpy

try:
    import pcty.server.dist_superlu as dist_superlu
except ImportError:
    dist_superlu_available = False
else:
    dist_superlu_available = True
print "dist_superlu_available?", dist_superlu_available

class ContinuityMPI:
    def __init__(self, releaseMaster = False):
        # Need to make sure that the location of binaries is in the python path
        DynamicBinPathCreator()
        mpi = mympi_API()
        self.mpi = mpi
        myid = mpi.myid
        num_procs = mpi.num_procs
        print "on proc %d of %d, args were %s"%(myid, num_procs, sys.argv)
        
        #enable and initialize distributed superlu if available
        self.mpi.dist_superlu_available = dist_superlu_available
        if self.mpi.dist_superlu_available:
            dist_superlu.initialize_grid(mpi.num_procs,1)

        if not mpi.isRoot:
            self.handleSlave()
            sys.exit(0)
        elif not releaseMaster:
            self.handleMaster()

    
    def printHelp(self):
        print "\n\n./continuityparallel [--serveronly|myscript.py]"
        print "[--serveronly]\t\tRun server only without client (runs both client and server by default)."
        print "[--mpi-fast]\t\tUse an mpi that is configured to use a fast interface"
        print "myscript.py\t\tThe path of the script to execute\n\n"
    
    def handleMaster(self):
        if "--help" in sys.argv or "-h" in sys.argv:
            self.printHelp()
            return

        if "--serveronly" in sys.argv:
            self.runContinuityDaemon()
        else:
            self.runContinuityClient()

    def runContinuityDaemon(self):
        #import and launch ContinuityDaemon
        #XXX: pass it mpi pointer
        from pcty.ContinuityDaemon import main
        main(0,0,0,self.mpi)
    
    def runContinuityClient(self):
        # Check to see if the user has supplied a step parameter
        if sys.argv[len(sys.argv)-2] == '--step':
            script = sys.argv[len(sys.argv)-3] + ' ' + sys.argv[len(sys.argv)-2] + ' ' + sys.argv[len(sys.argv)-1]
        else:
            script = sys.argv[-1]
        
        if script == "--server" or script == sys.argv[0]:
            self.printHelp()
            return
        #import and launch ContinuityClient in full mode and pass it script
        #XXX: pass it mpi pointer

        from pcty.ContinuityClient import main
        main( 0, gui=0, full=1, standAlone=0,startupFile = script,
              doSplash = False,withShell = 0,batch=1,openFile=None, mpi = self.mpi )


    def handleSlave(self):
        mpi = self.mpi
        bm = parallelBM.bmsolver_parallel(mpi)
        ep = parallelEP.cont2ODEsolver_parallel(mpi)
        while True:
            state = mpi.bcast(0)
            if state == mpi.EXIT:
                print "slave exiting..."
                mpi.barrier()
                mpi.finalize()
                break
            elif state == mpi.DIST_SUPER_LU:
                junk_args = 0, 0, 0, numpy.zeros([1], numpy.float64),numpy.zeros([1], numpy.int32), numpy.zeros([1], numpy.int32), numpy.zeros([1], numpy.float64)
                dist_superlu.pdgssvx_ABglobal_dist(*junk_args)
            elif mpi.isBmCmd(state):
                bm.handleState(state)
            else:
                ep.handleState(state)


if __name__ == "__main__":
    ContinuityMPI()
