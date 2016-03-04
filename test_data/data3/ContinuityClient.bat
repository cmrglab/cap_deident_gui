echo off

set HOME=%USERPROFILE%

if not exist "%CONTPYTHON%python.exe" goto NOPYTHON
if not exist "%CONTINUITYPATH%/pcty" goto NOCONTINUITY
cd /d "%CONTINUITYPATH%/pcty"
REM Pick off any Python specifc flags
SET optflag=
SET unbufflag=
:loop
IF NOT [%1]==[] (
    IF [%1]==[--opt] (
        SET optflag=-OO
    )
    IF [%1]==[--unbuffered] (
        SET unbufflag=-u
    )
    SHIFT
    GOTO :loop
)

SET pyflags=%optflag% %unbufflag%

if exist ContinuityClient.py goto RUNPY
if exist ContinuityClient.pyc goto RUNPYC


echo Neither ContinuityClient.py nore ContinuityClient.pyc could be found at %CONTINUITYPATH%/pcty.
echo Continuity installation probably failed?
pause 
goto done

:RUNPYC
echo Running ContinuityClient.pyc
"%CONTPYTHON%python" %pyflags% ContinuityClient.pyc --no-threads %*
goto done

:RUNPY
echo Running ContinuityClient.py
"%CONTPYTHON%python" %pyflags% ContinuityClient.py --no-threads %*
goto done

:NOPYTHON
@echo off
echo Sorry, the python executable was not found!
echo Make sure python 2.7 is installed and that the
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
