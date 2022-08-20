
import subprocess

MODE = "lsf"

if MODE == "lsf":

  proc = subprocess.Popen(["lsload", "-gpuload", "-w"], stdout=subprocess.PIPE, shell=True)
  (out, err) = proc.communicate()
  
  print(out)
