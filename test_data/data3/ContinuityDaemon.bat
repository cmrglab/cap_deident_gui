@echo off
if not exist "%CONTPYTHON%python.exe" goto NOPYTHON
if not exist "%CONTINUITYPATH%/pcty" goto NOCONTINUITY
cd /d "%CONTINUITYPATH%/pcty"
if exist ContinuityDaemon.pyc goto RUNPYC
if exist ContinuityDaemon.py goto RUNPY

echo Neither ContinuityDaemon.py nore ContinuityDaemon.pyc could be found at %CONTINUITYPATH%/pcty.
echo Continuity installation probably failed?
pause
goto done

:RUNPYC
echo Running ContinuityDaemon.pyc
"%CONTPYTHON%python" ContinuityDaemon.pyc %1 %2 %3 %4 %5 %6 %7 %8 %9
goto done

:RUNPY
echo Running ContinuityDaemon.py
"%CONTPYTHON%python" ContinuityDaemon.py %1 %2 %3 %4 %5 %6 %7 %8 %9
goto done

:NOPYTHON
@echo off
echo Sorry, the python executable was not found!
echo Make sure python 2.3 is installed and that the
echo environment variable CONTPYTHON is set to the
echo directory that contains python.exe.
echo See http://www.continuity.ucsd.edu/Continuity/Download/Prerequisites
echo for more information.
pause
goto DONE

:NOCONTINUITY
@echo off
echo Sorry, CONTINUITYPATH was not set to the directory containing pcty.
echo Perhaps the installation failed?  Verify that pcty exists in the
echo Continuity installation directory, and try
echo setting CONTINUITYPATH to the directory that contains pcty.
echo Information on setting environment variables can be found here:
echo http://www.microsoft.com/resources/documentation/windows/xp/all/proddocs/en-us/environment_variables.mspx?mfr=true
pause
goto DONE

:DONE
