#! /usr/bin/env python
import sys
import re
import os

def main(path, ofile):
  os.environ["PYTHONPATH"] += ":" + path
  from pcty.cont_classes import pexpect

  cmd = "python -c \"import pcty.ContinuityDaemon;pcty.ContinuityDaemon.main(0,1)\""

  of = open(ofile, 'w')

  child = pexpect.spawn(cmd)

  while 1:
    try:
      child.expect("\n")
      line = child.before
      print line
      of.write(line+"\n")
    except pexpect.TIMEOUT:
      pass
    except pexpect.EOF:
      print "Program terminated itself."
      break
    except KeyboardInterrupt:
      print "Program terminated by user."
      break
  #end while
#end def main

if __name__ == '__main__':
  if len(sys.argv) != 3:
    print "Usage:\n\tcontCapture.py [PATH_TO_DIR_CONTAINING_pcty] [OUTPUT_FILE]"
    print "e.g.:\n\tcontCatpure.py svn_dev/trunk output.txt"
    sys.exit(0)
  #end if

  main(sys.argv[1], sys.argv[2])
#end if
