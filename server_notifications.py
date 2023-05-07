import time
import logging
import traceback

import toml
import psutil
from datetime import datetime
from slack_messages import slack_notification


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


def slack_alert_on_memory_usage(time_step=0, active=True, period=30, threshold=90):
    if active and ((time_step % period) == 0):
        # get memory usage
        memory_high_usage = False
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


def slack_alert_on_disk_usage(time_step=0, active=True, period=30, threshold=90):
    if active and ((time_step % period) == 0):
        # get disk usage
        disk_high_usage = False
        disk_home_high_usage = False
        disk_usage = psutil.disk_usage(path="/").percent
        logging.info(f"Disk usage in '/' is {disk_usage}%")
        if disk_usage > threshold and not disk_high_usage:
            logging.warning("Disk usage is high in '/'")
            slack_notification("Disk usage is high in '/'")
            disk_high_usage = True
        elif disk_usage < threshold and disk_high_usage:
            disk_high_usage = False
            slack_notification("Disk usage is back to normal")
            logging.info("Disk usage is back to normal")

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


def slack_server_status_update(time_step=0, active=True, at_time='7:30'):
    if not active:
        return
    now_t = datetime.now().replace(second=0, microsecond=0)  
    update_t = datetime.strptime(at_time, '%H:%M')
    # check if the times are the same
    if (now_t.hour == update_t.hour) and ((now_t.minute <= update_t.minute + 1) and ((now_t.minute >= update_t.minute))):
        disk_usage_slash = psutil.disk_usage(path="/").percent
        disk_usage_slash_home = psutil.disk_usage(path="/home").percent
        memory_usage = psutil.virtual_memory().percent
        cpu_usage = psutil.cpu_percent(interval=1, percpu=False)
        slack_notification(f"Good Morning ☕. \nI Have some stats to report: \nCPU: {cpu_usage}% \nMemory: {memory_usage}% \nDisk \\: {disk_usage_slash}%\n Disk \\home: {disk_usage_slash_home}%")
        time.sleep(125)


if __name__ == "__main__":
    # read config file
    with open('config.toml') as f:
        config = toml.load(f)
    # setup loggings
    define_logging(config['logging']['file_path'])
    logging.info("Starting server notifications")
    logging.info(f"Config: \n{config}")
    
    # define notifications functions the keys should be similar to the keys in the config file
    notifications_func_dict = {
        'cpu': slack_alert_on_cpu_usage,
        'memory': slack_alert_on_memory_usage,
        'disk': slack_alert_on_disk_usage,
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

