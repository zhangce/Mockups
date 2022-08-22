
import subprocess

MODE = "lsf"

machines = {}
total_gpus = 0

if MODE == "lsf":

  proc = subprocess.Popen(["lsload -gpuload -w"], stdout=subprocess.PIPE, shell=True)
  (out, err) = proc.communicate()

  out = out.decode("utf-8")

  ct = 0
  machine_name = None
  for l in out.split('\n'):
    ct = ct + 1
    if ct == 1:
      continue
    fields = l.split()
    if len(fields) == 13:
      machine_name = fields[0]
      gpu_model = fields[2]

      machines[machine_name] = {}
      machines[machine_name]["gpu_model"] = gpu_model
      machines[machine_name]["n_gpu"] = 1

    elif len(fields) == 12:
      machines[machine_name]["n_gpu"] = machines[machine_name]["n_gpu"] + 1

  for machine_name in machines:
    proc = subprocess.Popen(["bhosts -l %s" % machine_name] , stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    out = out.decode("utf-8")

    ct = None
    for l in out.split('\n'):
      if "ngpus_excl_p" in l:
        ct = 0
        continue
      if ct == None:
        continue
      avail = l.split()[4]
      machines[machine_name]["avail"] = float(avail)
      total_gpus = total_gpus + float(avail)
      break

print ("Total GPUs", total_gpus)

for machine_name in machines:

  print(machine_name, machines[machine_name]["gpu_model"], machines[machine_name]["n_gpu"], machines[machine_name]["avail"])

import requests

res = requests.post('https://planetd.shift.ml/site_stats', json={
  "site_identifier": "ethz.ch", # "stanford.edu", # ethz.ch; osg-htc.org
  "total_perfs": total_gpus * 50,
  "num_gpu": total_gpus,
  "num_cpu": 0,
  "note": "string"
})



