
from platform import machine
import subprocess
import argparse
import logging
import re

import time

parser = argparse.ArgumentParser(prog='statistics.py')

# Type of a given cluster
#
parser.add_argument('mode',  choices={"slurm", "lsf", "condor"})

# Identifier of each site 
#
parser.add_argument('site', choices={'stanford.edu', 'ethz.ch', 'osg-htc.org', 'chtc.wisc.edu'})

# If Slurm cluster, we can filter by the prefixes of 
# a partition that can be used by Together
#
parser.add_argument('--slurm-partition-prefixes', nargs='+')

# On some clusters, it is not always possible to get all types of devices
# Put the LOCAL (i.e., key of `device_map`) names of these device types here
#
parser.add_argument('--available-device-types', nargs='+')

args = parser.parse_args()

# Collected Statistics are stored here
# machines = {
#    machine_name : {
#       gpu_model : X  # string that can be looked up in `device_map``
#       ngpu      : Y  # int, total number of GPUs
#       avail     : Z  # int, total number of GPUs available
#    }
# }
machines = {}

# Name of devices to its canonical name (that can be looked up in `devices`) 
#
device_map = {
    "titanxp" : "NVIDIA TITAN Xp",
    "titanrtx" : "NVIDIA TITAN RTX" ,
    "a100": "NVIDIA A100 PCIe",
    "a5000" : "NVIDIA RTX A5000"   ,
    "3090" : "NVIDIA GeForce RTX 3090"         ,
    "2080ti": "NVIDIA GeForce RTX 2080 Ti"        ,
    "titanx": "NVIDIA GeForce GTX TITAN X"       ,
    "titanv": "NVIDIA TITAN V" ,
    "NVIDIA A100-PCIE-40GB": "NVIDIA A100 PCIe",
    "NVIDIA A40": "NVIDIA A40 PCIe",
    "Tesla V100-SXM2-16GB": "NVIDIA Tesla V100 SXM2 16 GB",
    "Tesla P100-PCIE-16GB": "NVIDIA Tesla P100 PCIe 16 GB",
    "NVIDIA A100-SXM4-40GB": "NVIDIA A100 SXM4 40 GB",
    "NVIDIA Quadro RTX 6000": "NVIDIA Quadro RTX 6000",
    "NVIDIAGeForceGTX1080Ti": "NVIDIA GeForce GTX 1080 Ti",
    "NVIDIAGeForceGTX1080": "NVIDIA GeForce GTX 1080",
    "NVIDIAGeForceRTX2080Ti": "NVIDIA GeForce RTX 2080 Ti",
    "NVIDIAGeForceRTX3090": "NVIDIA GeForce RTX 3090",
    "NVIDIATITANRTX": "NVIDIA TITAN RTX",
    "QuadroRTX6000": "NVIDIA Quadro RTX 6000",
    "TeslaV100_SXM2_32GB": "NVIDIA Tesla V100 SXM2 32 GB",
    "NVIDIAA100_PCIE_40GB": "NVIDIA A100 PCIe",
    "NVIDIA RTX A5000": "NVIDIA RTX A5000",
    None: None
}

# Devices
# Device Canonical Name => (FP32 TFLOPS, TENSOR TFLOPS, MEMORY GB, BANDWIDTH GB/S, SOURCE)
#
devices = {
    "NVIDIA TITAN Xp" : (12.15, 12.15, 12, 547.6, "https://www.techpowerup.com/gpu-specs/titan-xp.c2948"),
    "NVIDIA TITAN RTX" : (16.31, 32.62, 24, 672, "https://www.techpowerup.com/gpu-specs/titan-rtx.c3311"),
    "NVIDIA RTX A5000" : (24.78, 222.2, 24, 768, "https://www.leadtek.com/eng/products/workstation_graphics(2)/NVIDIA_RTX_A5000(40914)/detail"),
    "NVIDIA GeForce RTX 3090": (35.58, 285, 24, 936, "https://wccftech.com/roundup/nvidia-geforce-rtx-3090-ti/"),
    "NVIDIA GeForce RTX 2080 Ti": (13.4, 114, 11, 616, "https://mightygadget.co.uk/nvidia-geforce-rtx-3080-vs-rtx-2080-ti/"),
    "NVIDIA GeForce GTX TITAN X": (6.691, 6.691, 12, 336.5, "https://www.nvidia.com/en-us/geforce/graphics-cards/geforce-gtx-titan-x/specifications/"),
    "NVIDIA TITAN V": (14.90, 29.80, 12, 651.3, "https://www.techpowerup.com/gpu-specs/titan-v.c3051"),
    "NVIDIA A100 PCIe": (19.49, 312, 40, 1555, "https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/a100/pdf/a100-80gb-datasheet-update-nvidia-us-1521051-r2-web.pdf"),
    "NVIDIA A100 SXM4 40 GB": (19.49, 312, 40, 1555, "https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/a100/pdf/a100-80gb-datasheet-update-nvidia-us-1521051-r2-web.pdf"),
    "NVIDIA A40 PCIe": (37.4, 149.7, 48, 696, "https://images.nvidia.com/content/Solutions/data-center/a40/nvidia-a40-datasheet.pdf"),
    "NVIDIA Tesla V100 SXM2 16 GB": (15.7, 125, 16, 900, "https://images.nvidia.com/content/technologies/volta/pdf/tesla-volta-v100-datasheet-letter-fnl-web.pdf"),
    "NVIDIA Tesla P100 PCIe 16 GB": (14, 112, 16, 900, "https://images.nvidia.com/content/technologies/volta/pdf/tesla-volta-v100-datasheet-letter-fnl-web.pdf" ),
    "NVIDIA Quadro RTX 6000": (16.3, 130.5, 24, 672, "https://www.nvidia.com/content/dam/en-zz/Solutions/design-visualization/quadro-product-literature/quadro-rtx-6000-us-nvidia-704093-r4-web.pdf"),
    "NVIDIA GeForce GTX 1080 Ti": (11.34, 11.34, 11, 484, "https://www.techpowerup.com/gpu-specs/geforce-gtx-1080-ti.c2877"),
    "NVIDIA GeForce GTX 1080": (8.873, 8.873, 8, 320, "https://www.techpowerup.com/gpu-specs/geforce-gtx-1080.c2839"),
    "NVIDIA Tesla V100 SXM2 32 GB": (15.67, 125, 32, 900, "https://images.nvidia.com/content/technologies/volta/pdf/tesla-volta-v100-datasheet-letter-fnl-web.pdf"),
    "NVIDIA RTX A5000": (27.8, 222, 24, 758, "https://pnypartners.com/wp-content/uploads/nvidia-rtx-a5000-datasheet.pdf"),
    None: (16.31, 32.62, 24, 672, "NVIDIA TITAN RTX") # if we cannot get GPU info, we assume it is an TITAN RTX
}


if args.mode == "slurm":

  logging.warning("Slurm Cluster; Site %s; Partitions %s", args.site, args.slurm_partition_prefixes)
  logging.warning("   filter device type: %s", args.available_device_types)

  proc = subprocess.Popen(["pestat -G"], stdout=subprocess.PIPE, shell=True)
  (out, err) = proc.communicate()
  out = out.decode("utf-8")

  for l in out.split("\n"):
    fields = l.split()

    # a content line should have at least 7 fields
    if not (len(fields) >= 7):
      continue
            
    hostname = fields[0]
    gres = fields[7]
    jobs = fields[8:]

    # filter by args.slurm_partition_prefixes
    if args.slurm_partition_prefixes is not None:
      valid = False

      for prefix in args.slurm_partition_prefixes:
        if hostname.startswith(prefix): valid = True
      
      if valid == False:
        continue

    # find GPUs
    m = re.search(r'^gpu:(.*?):([0-9]*)$', gres)
    if m:
      devicename = m.group(1)
      ngpus = int(m.group(2))

      if args.available_device_types is not None and devicename not in args.available_device_types:
        continue

      nalloc = 0
      for i in range(2, len(jobs), 3):
        m = re.search(r'^gpu.*?:([0-9]*)$', jobs[i])
        if m:
          nalloc = nalloc + int(m.group(1))
    
      logging.warning("%s %s %s %s", hostname, devicename, ngpus, ngpus - nalloc)

      if hostname not in machines:
        machines[hostname] = {}
        machines[hostname]["gpu_model"] = devicename
        machines[hostname]["n_gpu"] = ngpus
        machines[hostname]["avail"] = ngpus - nalloc

if args.mode == "condor":

  logging.warning("Condor Cluster; Site %s", args.site)
  logging.warning("   filter device type: %s", args.available_device_types)

  import htcondor
  coll = htcondor.Collector()
  ads = coll.query()

  for ad in ads:

    total_gpus = ad.get("TotalGPUs")
    if total_gpus is None: # if no GPUs
      continue

    detected_gpus = ad.get("DetectedGPUs")
    if detected_gpus is None or detected_gpus == 0: # if no detected GPUs
      continue
    detected_gpus = detected_gpus.split(", ")

    machine_name = ad.get("Name").__repr__()

    if machine_name not in machines:
      machines[machine_name] = {}
      machines[machine_name]["gpu_model"] = None
      machines[machine_name]["n_gpu"] = 0
      machines[machine_name]["avail"] = 0

    for gpu in detected_gpus:
      machines[machine_name]["n_gpu"] = machines[machine_name]["n_gpu"] + 1

      gpurepr = gpu.__repr__()
      gpuinfo = ad.get(gpurepr)
      if gpuinfo is None: continue
      devicename = gpuinfo.get("DeviceName")
      machines[machine_name]["gpu_model"] = devicename

    avail_gpus = ad.get("AvailableGPUs")
    if avail_gpus is None or avail_gpus == []:
      continue

    for gpu in avail_gpus:
      gpurepr = gpu.__repr__()
      gpuinfo = ad.get(gpurepr)

      if gpuinfo is None: continue
      
      if machines[machine_name]["gpu_model"] is None:
        machines[machine_name]["gpu_model"] = gpuinfo.get("DeviceName")

      if args.available_device_types is not None and machines[machine_name]["gpu_model"] not in args.available_device_types:
        continue

      machines[machine_name]["avail"] = machines[machine_name]["avail"] + 1

    logging.warning("%s %s %s %s", machine_name, machines[machine_name]["gpu_model"], machines[machine_name]["n_gpu"], machines[machine_name]["avail"])

if args.mode == "lsf":

  logging.warning("LSF Cluster; Site %s", args.site)
  logging.warning("   filter device type: %s", args.available_device_types)

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

    # first line with 13 fields, which contains machine name
    #
    if len(fields) == 13:
      machine_name = fields[0]
      gpu_model = fields[2]

      machines[machine_name] = {}
      machines[machine_name]["gpu_model"] = gpu_model
      machines[machine_name]["n_gpu"] = 1

    # following line does not have machine name, thus 12 columns
    # 
    elif len(fields) == 12:
      machines[machine_name]["n_gpu"] = machines[machine_name]["n_gpu"] + 1

  # for each machine, get its availability
  #
  for machine_name in machines:

    if args.available_device_types is not None and machines[machine_name]["gpu_model"] not in args.available_device_types:
      machines[machine_name]["avail"] = 0
      continue

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
      break

total_gpus = 0
avail_gpus = 0

total_fp16 = 0
avail_fp16 = 0


machines_available = {}

for machine_name in machines:
  device = machines[machine_name]["gpu_model"]
  if device not in device_map:
    logging.warning("UNKNOWN DEVICES %s", device)
    continue

  canonical_device = device_map[device]

  (fp32, fp16, mem, band, source) = devices[canonical_device]

  total_gpus = total_gpus + machines[machine_name]["n_gpu"]
  total_fp16 = total_fp16 + fp16 * machines[machine_name]["n_gpu"]

  # these are resources that we can confidentally use
  #
  if device is not None and machines[machine_name]["avail"] > 0 :
    avail_gpus = avail_gpus + machines[machine_name]["avail"]
    avail_fp16 = avail_fp16 + fp16 * machines[machine_name]["avail"]

    logging.warning("%s %s %s %s %s %s", machine_name, machines[machine_name]["n_gpu"], machines[machine_name]["avail"], fp32, fp16, device)

    machines_available[machine_name] = {}
    machines_available[machine_name]["gpu_model_local"] = device
    machines_available[machine_name]["gpu_model_global"] = canonical_device
    machines_available[machine_name]["gpu_property"] = {
      "fp32_tflops": fp32,
      "fp16_tflops": fp16,
      "memory": mem,
      "bandwidth": band 
    }
    machines_available[machine_name]["total_gpus"] = machines[machine_name]["n_gpu"]
    machines_available[machine_name]["avail_gpus"] = machines[machine_name]["avail"]

logging.warning("Total GPUs: %s", total_gpus)
logging.warning("Avail GPUs: %s", avail_gpus)
logging.warning("Total FP16: %s %s", total_fp16, "TFLOPS")
logging.warning("Avail FP16: %s %s", avail_fp16, "TFLOPS")


import requests
res = requests.post('https://planetd.shift.ml/site_stats', json={
  "timestamp": time.time(),
  "site_identifier": args.site,
  "scheduler_type": args.mode,
  "total_tflops": total_fp16,
  "avail_tflops": avail_fp16,
  "total_gpus": total_gpus,
  "avail_gpus": avail_gpus,
  "resources": machines_available,
  "note": "string"
})

print ({"timestamp": time.time(),
  "site_identifier": args.site,
  "scheduler_type": args.mode,
  "total_tflops": total_fp16,
  "avail_tflops": avail_fp16,
  "total_gpus": total_gpus,
  "avail_gpus": avail_gpus,
  "resources": machines_available,
  "note": "string"
})
