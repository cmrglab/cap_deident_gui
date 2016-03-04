import sys
import os
import _winreg as wreg

def ForceMakeKey(keyname, value):
    exists = False
    try:
      key = wreg.OpenKey(wreg.HKEY_CLASSES_ROOT, keyname)
      wreg.CloseKey(key)
      exists = True
      print "  *%s already in registry!"%keyname
    except:
      key = wreg.CreateKey(wreg.HKEY_CLASSES_ROOT, keyname)
      wreg.SetValue(key, "", wreg.REG_SZ, str(value))
      wreg.CloseKey(key)
    return exists

def ForceDeleteKey(keyname):
    wreg.DeleteKey(wreg.HKEY_CLASSES_ROOT, keyname)

def keyExists(keyname):
    try:
      key = wreg.OpenKey(wreg.HKEY_CLASSES_ROOT, keyname)
      wreg.CloseKey(key)
      return True
    except:
      return False

def clearContRegistry():
    if keyExists(".cont6"):
        ForceDeleteKey(".cont6")

    if keyExists("Cont6.Document"):
        ForceDeleteKey("Cont6.Document\\Shell\\Open\\Command")
        ForceDeleteKey("Cont6.Document\\Shell\\Open")
        ForceDeleteKey("Cont6.Document\\Shell")
        ForceDeleteKey("Cont6.Document\\DefaultIcon")
        ForceDeleteKey("Cont6.Document")
        print "  *Deleting Continuity entries from registry..."

def setEnviron(keyname, value):
    print "  *permanently setting environment variable %s to %s"%(keyname, value)
    key = wreg.CreateKey(wreg.HKEY_CURRENT_USER, "Environment")
    wreg.SetValueEx(key, keyname, 0, wreg.REG_SZ, value)
    
    #XXX:to update the variable immediately, you need win32gui, and win32con.  It could be done like this:
    #win32gui.SendMessage(win32con.HWND_BROADCAST, win32con.WM_SETTINGCHANGE, 0, 'Environment')

def getPythonPath():
    pythonPath = wreg.QueryValue(wreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Python\\PythonCore\\2.7\\InstallPath")
    pythonPath = pythonPath.replace("\\","/")
    return pythonPath

def setupRegistry(contPath):
    contPath = os.path.abspath(contPath)
    if (not os.access("%s\pcty\client\icons\continuityFileIcon.ico"%contPath, os.F_OK) or
            not os.access("%s\pcty\ContinuityClient.bat"%contPath, os.F_OK)):
        print "  *CONTINUITYPATH of %s is missing icon, or bat files at the appropriate locations.  NOT setting registry!"%contPath
        return False


    pythonPath = getPythonPath()
    #set CONTINUITYPATH
    setEnviron("CONTINUITYPATH",contPath)
    setEnviron("CONTPYTHON",pythonPath)

    if keyExists(".cont6"):
      print "  *Registry already initialized for Continuity!"
      return True
      iconPath = wreg.QueryValue(wreg.HKEY_CLASSES_ROOT, "Cont6.Document\\DefaultIcon")
      if iconPath == os.path.abspath(iconPath):
        return True
      else:
        print "clear cont registry..."
        clearContRegistry()

    ForceMakeKey(".cont6", "Cont6.Document")
    ForceMakeKey("Cont6.Document", "Continuity 6 Document")
    ForceMakeKey("Cont6.Document\\DefaultIcon", '"%s\pcty\client\icons\continuityFileIcon.ico"'%contPath)
    ForceMakeKey("Cont6.Document\\Shell", "")
    ForceMakeKey("Cont6.Document\\Shell\\Open", "")
    ForceMakeKey("Cont6.Document\\Shell\\Open\\Command", '"%s\pcty\ContinuityClient.bat" "%%1"'%contPath)
    print "  *Initialized registry!"
    return True


def verifyPath(guessPath):
      if os.access(guessPath+"//pcty", os.F_OK):
          print "  *pcty found in CONTINUITYPATH"
          return True
      else:
          print "  *CONTINUITYPATH (%s) is missing pcty.  NOT modifying registry!"%guessPath
          return False


def checkRegistry(guessPath):
    if "win" not in sys.platform:
      return False

    print "verify path..."
    if not verifyPath(guessPath):
        print "  *Could not setup registry!"
        return False
    print "setup registry..."
    try:
        if setupRegistry(guessPath):
          print "  *Registry initialized!"
        else:
          print "  *Registry not initialized!"
    except:
        print "  *Requesting elevated privledges..."
        pythonPath = getPythonPath()
        os.system(os.path.join("..\\","winlib", "Elevate64.exe") + " -wait %spython checkRegistry.py"%pythonPath)


if __name__=="__main__":
    if "--clear" in sys.argv:
        try:
            clearContRegistry()
        except:
            pythonPath = getPythonPath()
            os.system(os.path.join("..\\","winlib", "Elevate64.exe") + " -wait %spython checkRegistry.py --clear"%pythonPath)
    else:
        checkRegistry("..\\")
