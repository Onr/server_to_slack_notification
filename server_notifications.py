import time
import logging
import traceback
import subprocess

import toml
import psutil
from datetime import datetime
from slack_messages import slack_notification
from langchain.llms import OpenAI



def define_logging(file_path):
    # print logs to console
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # print logs to file
    fh = logging.FileHandler(file_path)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)
    logging.getLogger().addHandler(fh) 


def slack_alert_on_cpu_usage(time_step: int = 0, active: bool = True, period: int = 30, threshold: int = 90):
    if active and ((time_step % period) == 0):
        # get cpu usage
        cpu_high_usage = False
        cpu_usage = psutil.cpu_percent(interval=1, percpu=False)
        logging.info(f"CPU usage is {cpu_usage}%")
        if cpu_usage > threshold and not cpu_high_usage:
            logging.warning("CPU usage is high")
            slack_notification("CPU usage is high")
            cpu_high_usage = True
        elif cpu_usage < threshold and cpu_high_usage:
            cpu_high_usage = False
            slack_notification("CPU usage is back to normal")
            logging.info("CPU usage is back to normal")


memory_high_usage = False     # TODO fix so this will take affect
def slack_alert_on_memory_usage(time_step=0, active=True, period=30, threshold=90):
    global memory_high_usage

    if active and ((time_step % period) == 0):
        # get memory usage
        memory_usage = psutil.virtual_memory().percent
        logging.info(f"Memory usage is {memory_usage}%")
        if memory_usage > threshold and not memory_high_usage:
            logging.warning("Memory usage is high")
            slack_notification("Memory usage is high")
            memory_high_usage = True
        elif memory_usage < threshold and memory_high_usage:
            memory_high_usage = False
            slack_notification("Memory usage is back to normal")
            logging.info("Memory usage is back to normal")


disk_high_usage_list = [False] * 100     # TODO fix so this will take affect
# disk_locations = ['/', '/home']
def slack_alert_on_disk_usage(time_step=0, active=True, period=30, threshold=90, disk_locations=disk_high_usage_list):
    global disk_high_usage_list
    if active and ((time_step % period) == 0):
        # get disk usage
        for disk_ind in range(len(disk_locations)):
            disk_usage = psutil.disk_usage(path=disk_locations[disk_ind]).percent
            logging.info(f"Disk usage in {disk_locations[disk_ind]} is {disk_usage}%")
            if disk_usage > threshold and not disk_high_usage_list[disk_ind]:
                logging.warning(f"Disk usage is high in '{disk_locations[disk_ind]}'")
                slack_notification(f"Disk usage is high in '{disk_locations[disk_ind]}'")
                disk_high_usage_list[disk_ind] = True
            elif disk_usage < threshold and disk_high_usage_list[disk_ind]:
                disk_high_usage_list[disk_ind] = False
                slack_notification(f"Disk usage in '{disk_locations[disk_ind]}' is back to normal")
                logging.info(f"Disk usage in '{disk_locations[disk_ind]}' is back to normal")


def slack_alert_on_high_gpu_tmpature(time_step=0, active=True, period=30, threshold=90, disk_locations=disk_high_usage_list):
	if active and ((time_step % period) == 0):
		# Run the command and capture its output
		output = subprocess.check_output("nvidia-smi | grep C\  | grep W ", shell=True)
		# Print the output
		l_c = []
		for char in output.decode():
			l_c += [char]
		commad_out= "".join(l_c)
		for i, line in enumerate(commad_out.split("\n")):
			line_split = line.split("   ")
			if len(line_split) == 1:
				continue
			tmpature = int(line.split("   ")[1].split("C")[0])
			gpu_ind = i
			logging.info(f"Gpu {gpu_ind}: {tmpature}C")
			if tmpature > threshold:
				logging.warning(f"A GPU IS ON FIRE !!!! (Gpu {gpu_ind}: {tmpature}C)")
				slack_notification(f"A GPU IS ON FIRE !!!! (Gpu {gpu_ind}: {tmpature}C)")


def slack_server_status_update(time_step=0, active=True, at_time='7:30',
                               prompt=None):
    if not active:
        return
    now_t = datetime.now().replace(second=0, microsecond=0)  
    update_t = datetime.strptime(at_time, '%H:%M')
    # check if the times are the same
    if (now_t.hour == update_t.hour) and ((now_t.minute <= update_t.minute + 1) and ((now_t.minute >= update_t.minute))):

        disk_usage_s = []
        # Get list of disk partitions
        partitions = psutil.disk_partitions()
        # Iterate over partitions and report percentage, GB amount of free space, and GB amount of used space
        for partition in partitions:
            partition_usage = psutil.disk_usage(partition.mountpoint)
            if 'boot' in partition.mountpoint or 'snap' in partition.mountpoint:
                continue
            disk_usage_s += [f"   {partition.mountpoint}: {partition_usage.percent}% used space ({round(partition_usage.free / (1024 * 1024 * 1024), 2)} GB free / {round(partition_usage.used / (1024 * 1024 * 1024), 2)} GB used / {round(partition_usage.total / (1024 * 1024 * 1024), 2)} GB total)"]
        disk_usage_s = "\n".join(disk_usage_s)

        memory_usage = psutil.virtual_memory().percent
        cpu_usage = psutil.cpu_percent(interval=1, percpu=False)
        send_str = f"Good Morning ☕. \nI Have some stats to report: \nCPU: {cpu_usage}% \nMemory: {memory_usage}% \nDisks:\n"
        send_str += disk_usage_s
        if prompt is not None: 
            try:
                llm = OpenAI(temperature=0.9)
                prompt_str = f"{prompt}\n{send_str}"
                send_str = llm(prompt_str)
            except:
                logging.info(f"failed to use llm: \n{str(traceback.format_exc())}")

        slack_notification(send_str)
        time.sleep(125)


if __name__ == "__main__":
    # read config file
    with open('config.toml') as f:
        config = toml.load(f)
    # setup loggings
    define_logging(config['logging']['file_path'])
    logging.info("Starting server notifications")
    logging.info(f"Config: \n{config}")
    # define disk locations to track
    global disk_locations
    disk_locations = config['disk']['disk_locations']
    # define notifications functions the keys should be similar to the keys in the config file
    notifications_func_dict = {
        'cpu': slack_alert_on_cpu_usage,
        'memory': slack_alert_on_memory_usage,
        'disk': slack_alert_on_disk_usage,
        'status_update': slack_server_status_update,
        'gpu_tmp': slack_alert_on_high_gpu_tmpature,
    }
    time_step = 0
    try:
        while True:
            # Call notifications
            for key in notifications_func_dict.keys():
                notifications_func_dict[key](time_step, **config[key])

            # Check if config file changed
            with open('config.toml') as f:
                new_config = toml.load(f)
                if new_config != config:
                    config = new_config
                    logging.info(f"Config changed \nNew config: \n{config}")

            # Increment time step
            time_step = (time_step + 1) % (60*60*24*7)
            time.sleep(1)
    except Exception as e:
        logging.info(f"Logging exception: \n{str(traceback.format_exc())}")
        slack_notification(f"Logging Hera: Failed!: \nException: \n{str(traceback.format_exc())}")

