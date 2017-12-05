from os import listdir
from os.path import isfile, join
import matplotlib.pyplot as plt
import numpy as np

'''
Pipeline: conv_layer_auto_schedule
 total time: 1286.391968 ms  samples: 1018  runs: 100  time/run: 12.863919 ms
 average threads used: 6.378192
 heap allocations: 100  peak heap usage: 2097152 bytes
  Func: conv:            12.487ms  (97%)   threads: 6.504  peak: 2097152  num: 100       avg: 2097152
  Func: ReLU:            0.376ms   (2%)    threads: 2.354
Pipeline: conv_layer_auto_schedule_old
 total time: 1147.012817 ms  samples: 851  runs: 100  time/run: 11.470128 ms
 average threads used: 6.056404
 heap allocations: 100  peak heap usage: 2097152 bytes
  Func: conv:            11.218ms  (97%)   threads: 6.142  peak: 2097152  num: 100       avg: 2097152
  Func: ReLU:            0.251ms   (2%)    threads: 2.666
Pipeline: conv_layer
 total time: 3114.065430 ms  samples: 2506  runs: 101  time/run: 30.832331 ms
 average threads used: 3.904629
 heap allocations: 101  peak heap usage: 2097152 bytes
  Func: conv:            30.504ms  (98%)   threads: 3.932  peak: 2097152  num: 101       avg: 2097152
  Func: ReLU:            0.328ms   (1%)    threads: 1.428
Manually-tuned time: 30.0362ms
Old auto-scheduler time: 10.4661ms
New auto-scheduler time: 11.8714ms
'''

'''
pipeline: conv_layer_auto_schedule; total time: 1111.060791; samples: 899; runs: 100; time/run: 11.110608; average threads used: 6.513905; heap allocations: 100; peak heap usage: 2097152
{func: conv, time: 10.827, percent: 97, threads: 6.648, peak: 2097152, num: 100, avg: 2097152}
{func: ReLU, time: 0.283, percent: 2, threads: 1.625}
pipeline: conv_layer_auto_schedule_old; total time: 1123.039429; samples: 876; runs: 100; time/run: 11.230394; average threads used: 6.493151; heap allocations: 100; peak heap usage: 2097152
{func: conv, time: 10.980, percent: 97, threads: 6.614, peak: 2097152, num: 100, avg: 2097152}
{func: ReLU, time: 0.249, percent: 2, threads: 1.772}
pipeline: conv_layer; total time: 3197.604492; samples: 2590; runs: 101; time/run: 31.659451; average threads used: 3.919691; heap allocations: 101; peak heap usage: 2097152
{func: conv, time: 31.189, percent: 98, threads: 3.945, peak: 2097152, num: 101, avg: 2097152}
{func: ReLU, time: 0.469, percent: 1, threads: 2.184}
Manually-tuned time: 30.5986ms
Old auto-scheduler time: 10.923ms
New auto-scheduler time: 10.5467ms
'''

def get_num_of_funcs(data):
	num = 0
	for l in data:
		if "func" in l: # It is a func
			num += 1
	return num

def parse_pipeline(line, runtime_benchmark, ftime_benchmark, fpeak_benchmark, favg_benchmark):
	if "pipeline" not in line:
		return
	data = line.split("; ")
	num_funcs = get_num_of_funcs(data);
	# Get the pipeline runtime data
	pipeline_data = data[:len(data)-num_funcs]
	pipeline_name = pipeline_data[0].split("pipeline: ")[1]
	pipeline_runtime = float(pipeline_data[4].split("time/run: ")[1])
	if "_auto_schedule_old" in pipeline_name:
		pipeline_name = "autosched1"
	elif "_auto_schedule" in pipeline_name:
		pipeline_name = "autosched2"
	else:
		pipeline_name = "manual"
	runtime_benchmark[pipeline_name] = pipeline_runtime
	# Parse the per-func data
	funcs_data = data[len(data)-num_funcs:]
	for func_data in funcs_data:
		func_data = func_data.split(", ")
		fname = func_data[0].split("{func: ")[1]
		ftime, fpeak, favg = 0, 0, 0
		for d in func_data:
			if "time" in d:
				ftime = float(d.split("time: ")[1].split("}")[0]) #ms
			elif "peak" in d:
				fpeak = int(d.split("peak: ")[1].split("}")[0]) #bytes
			elif "avg" in d:
				favg = int(d.split("avg: ")[1].split("}")[0]) #bytes
		if fname not in ftime_benchmark:
			ftime_benchmark[fname] = {}
		if fname not in fpeak_benchmark:
			fpeak_benchmark[fname] = {}
		if fname not in favg_benchmark:
			favg_benchmark[fname] = {}
		ftime_benchmark[fname][pipeline_name] = ftime
		fpeak_benchmark[fname][pipeline_name] = fpeak
		favg_benchmark[fname][pipeline_name] = favg
	return pipeline_name

def parse_benchmark(filename):
	f = open(benchmark_dir + filename, 'r')
	lines = f.read().split('\n')
	f.close()
	# Parse the benchmark data (new auto-sched, old auto-sched, and the manually scheduled version)
	runtime_benchmark, ftime_benchmark, fpeak_benchmark, favg_benchmark = {}, {}, {}, {}
	for line in lines:
		parse_pipeline(line, runtime_benchmark, ftime_benchmark, fpeak_benchmark, favg_benchmark)
	return runtime_benchmark, ftime_benchmark, fpeak_benchmark, favg_benchmark

def remove_all_zero(benchmarks):
	for k in [k for k, v in benchmarks.items() if ((v["manual"] == 0) and (v["autosched1"] == 0) and (v["autosched2"] == 0))]: del benchmarks[k]
	return benchmarks

def normalize_fbenchmarks(benchmarks):
	for fname in benchmarks:
		if "manual" not in benchmarks[fname]:
			benchmarks[fname]["manual"] = 0
		if "autosched1" not in benchmarks[fname]:
			benchmarks[fname]["autosched1"] = 0
		if "autosched2" not in benchmarks[fname]:
			benchmarks[fname]["autosched2"] = 0
	benchmarks = remove_all_zero(benchmarks)
	#for fname in benchmarks:
	#	print(benchmarks[fname])
	return benchmarks

def analyze_benchmarks(benchmark_files):
	runtime_benchmarks, ftime_benchmarks, fpeak_benchmarks, favg_benchmarks = {}, {}, {}, {}
	for filename in benchmark_files:
		test_name = filename.split(".txt")[0]
		runtime_benchmark, ftime_benchmark, fpeak_benchmark, favg_benchmark = parse_benchmark(filename)
		runtime_benchmarks[test_name] = runtime_benchmark
		ftime_benchmarks[test_name] = normalize_fbenchmarks(ftime_benchmark)
		fpeak_benchmarks[test_name] = normalize_fbenchmarks(fpeak_benchmark)
		favg_benchmarks[test_name] = normalize_fbenchmarks(favg_benchmark)
	return runtime_benchmarks, ftime_benchmarks, fpeak_benchmarks, favg_benchmarks

def plot_comparison(stats, ylabel, title):
	# stats = {'conv': {'autosched2': 12.727, 'autosched1': 12.841, 'manual': 32.748}, 'ReLU': {'autosched2': 0.337, 'autosched1': 0.293, 'manual': 0.342}}
	labels = [key for key in stats.keys()]
	manual = [x['manual'] for x in stats.values()]
	autosched1 = [x['autosched1'] for x in stats.values()]
	autosched2 = [x['autosched2'] for x in stats.values()]
	# Compute the speedup between autosched and autosched2 to manual
	autosched2 = [float(base)/float(val) if (val != 0) else 0.0 for base, val in zip(manual, autosched2)]
	autosched1 = [float(base)/float(val) if (val != 0) else 0.0 for base, val in zip(manual, autosched1)]
	manual = [float(base)/float(val) if (val != 0) else 0.0 for base, val in zip(manual, manual)]
	# Setting the positions and width for the bars
	pos = list(range(len(manual)))
	width = 0.25
	# Plotting the bars
	xwidth = max(4, int(len(labels)))
	ywidth = int(max(manual + autosched1 + autosched2) + 0.2*max([len(k) for k in labels]))
	fig, ax = plt.subplots(figsize=(xwidth, ywidth))
	#fig, ax = plt.subplots()
	# Create a bar for manual data
	plt.bar(pos, manual, width, alpha=0.5, color='#EE3224', label=labels[0])
	# Create a bar for autosched1 data
	plt.bar([p + width for p in pos], autosched1, width, alpha=0.5,
	        color='#F78F1E', label=labels[0])
	# Create a bar for autosched2 data
	plt.bar([p + width*2 for p in pos], autosched2, width, alpha=0.5,
	        color='#FFC222', label=labels[0])
	# Set the y axis label
	ax.set_ylabel(ylabel)
	# Set the chart's title
	ax.set_title(title)
	# Set the position of the x ticks
	ax.set_xticks([p + 1.5 * width for p in pos])
	# Set the labels for the x ticks
	ax.set_xticklabels(labels)
	# Setting the x-axis and y-axis limits
	plt.xlim(min(pos)-width, max(pos)+width*4)
	plt.ylim([0, max(manual + autosched1 + autosched2)] )
	plt.xlabel("...", labelpad=20)
	# Adding the legend and showing the plot
	plt.legend(['manual', 'autosched1', 'autosched2'], loc='upper left')
	plt.xticks(rotation=90)
	plt.tight_layout()
	#plt.gcf().subplots_adjust(bottom=0.25)
	plt.grid()
	plt.show()

# Write per-pipeline per-func benchmark to file
def write_fbenchmarks(filename, fbenchmarks):
	with open(filename, "w") as text_file:
    	#text_file.write("Purchase Amount: {0}".format(TotalAmount))

if __name__ == '__main__':
	benchmark_dir = "./apps/benchmark_data/"
	benchmark_files = [f for f in listdir(benchmark_dir) if isfile(join(benchmark_dir, f))]
	runtime_benchmarks, ftime_benchmarks, fpeak_benchmarks, favg_benchmarks = analyze_benchmarks(benchmark_files)
	# Generate the plot
	plot_comparison(runtime_benchmarks, "speed-up", "Runtime Comparison")
	for test_name in ftime_benchmarks:
		plot_comparison(ftime_benchmarks[test_name], "speed-up", "Runtime Comparison (" + test_name + ")")
	for test_name in fpeak_benchmarks:
		plot_comparison(fpeak_benchmarks[test_name], "peak", "Peak Memory Comparison (" + test_name + ")")
	for test_name in favg_benchmarks:
		plot_comparison(favg_benchmarks[test_name], "avg", "Avg Memory Comparison (" + test_name + ")")

	plot_comparison(ftime_benchmarks['lens_blur'], "speed-up", "Runtime Comparison (" + 'lens_blur' + ")")


