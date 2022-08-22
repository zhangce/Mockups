
import subprocess

MODE = "condor"

machines = {}
total_gpus = 0

#devices = {}

# {u'titanxp': 1, u'titanrtx': 1, u'a5000': 1, u'3090': 1, u'titanx:2,gpu:titanxp': 1, u'titanx:1,gpu:2080ti': 1, u'titanx': 1, u'titanv': 1}


device_map = {
    "titanxp" : "NVIDIA TITAN Xp",
    "titanrtx" : "NVIDIA TITAN RTX" ,
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
    "NVIDIA Quadro RTX 6000": "NVIDIA Quadro RTX 6000"
}

# (FP32 TFLOPS, TENSOR TFLOPS, MEMORY GB, BANDWIDTH GB/S, SOURCE)
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
    "NVIDIA Quadro RTX 6000": (16.3, 130.5, 24, 672, "https://www.nvidia.com/content/dam/en-zz/Solutions/design-visualization/quadro-product-literature/quadro-rtx-6000-us-nvidia-704093-r4-web.pdf")
}

if MODE == "slurm":

    proc = subprocess.Popen(["pestat -G"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    out = out.decode("utf-8")

    for l in out.split("\n"):
        fields = l.split()

        if not (len(fields) >= 7):
            continue
            

        hostname = fields[0]
        gres = fields[7]
        jobs = fields[8:]

        # NLP Cluster
        if "jagupard" not in hostname:
            continue

        #print(hostname, gres, jobs)

        import re
        m = re.search(r'^gpu:(.*?):([0-9]*)$', gres)
        if m:
            devicename = m.group(1)
            ngpus = int(m.group(2))

            nalloc = 0
            for i in range(2, len(jobs), 3):
                m = re.search(r'^gpu.*?:([0-9]*)$', jobs[i])
                if m:
                    nalloc = nalloc + int(m.group(1))
            
            print(hostname, devicename, ngpus, nalloc)

            if hostname not in machines:
                machines[hostname] = {}
                machines[hostname]["gpu_model"] = devicename
                machines[hostname]["n_gpu"] = ngpus
                machines[hostname]["avail"] = ngpus - nalloc

            #devices[devicename] = 1


if MODE == "condor":
	import htcondor
	coll = htcondor.Collector()
	ads = coll.query()

	for ad in ads:
		avail_gpus = ad.get("AvailableGPUs")
		if avail_gpus is None or avail_gpus == []:
			continue

		machine_name = ad.get("Name").__repr__()
		for gpu in avail_gpus:
			gpurepr = gpu.__repr__()
			gpuinfo = ad.get(gpurepr)

			if gpuinfo is None: continue

			devicename = gpuinfo.get("DeviceName")
			total_gpus = total_gpus  + 1
			
			if machine_name not in machines:
				machines[machine_name] = {}
				machines[machine_name]["gpu_model"] = devicename
				machines[machine_name]["n_gpu"] = 0
				machines[machine_name]["avail"] = 0
			machines[machine_name]["n_gpu"] = machines[machine_name]["n_gpu"] + 1
			machines[machine_name]["avail"] = machines[machine_name]["avail"] + 1

			print(machine_name, devicename)

                        #devices[devicename] = 1
                        
#print("######")

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

      #devices[gpu_model] = 1

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

    device = machines[machine_name]["gpu_model"]
    if device not in device_map:
        print ("UNKNOWN DEVICES", device)
        continue

    (fp32, fp16, mem, band, source) = devices[device_map[device]]
    
    print(machine_name, machines[machine_name]["gpu_model"], machines[machine_name]["n_gpu"], machines[machine_name]["avail"], fp16)
  

print devices


"""
import requests

res = requests.post('https://planetd.shift.ml/site_stats', json={
    "site_identifier": "stanford.edu"   ,# "ethz.ch", # "osg-htc.org", # "stanford.edu", # ethz.ch; osg-htc.org
  "total_perfs": total_gpus * 50,
  "num_gpu": total_gpus,
  "num_cpu": 0,
  "note": "string"
})

print devices
"""
