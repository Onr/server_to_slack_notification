import time
import logging
import threading

import psutil
from slack_messages import slack_notification


def define_logging():
    # print logs to console
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # print logs to file
    fh = logging.FileHandler("usage.log")
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)
    logging.getLogger().addHandler(fh) 


def start_function_in_thread(function, args):
    thread = threading.Thread(target=function, name=function.__name__, args=args)
    thread.start()


def slack_alert_on_cpu_usage(threshold=90, delay=5):
    # get cpu usage
    cpu_high_usage = False
    while True:
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
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        time.sleep(delay - 1)


def slack_alert_on_memory_usage(threshold=90, delay=30):
    # get memory usage
    memory_high_usage = False
    while True:
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
        time.sleep(delay - 1)


def slack_alert_on_disk_usage(threshold=90, delay=30):
    # get disk usage
    disk_high_usage = False
    disk_home_high_usage = False
    while True:
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

        # check disk usage in /home
        disk_usage_home = psutil.disk_usage(path="/home").percent
        logging.info(f"Disk usage in /home is {disk_usage_home}%")
        if disk_usage_home > threshold and not disk_home_high_usage:
            logging.warning("Disk usage in /home is high")
            slack_notification("Disk usage in /home is high")
            disk_home_high_usage = True
        elif disk_usage_home < threshold and disk_home_high_usage:
            disk_home_high_usage = False
            slack_notification("Disk usage in /home is back to normal")
            logging.info("Disk usage in /home is back to normal")

        time.sleep(delay - 1)
    

if __name__ == "__main__":
    define_logging()

    # run cpu notification in the background
    start_function_in_thread(function=slack_alert_on_cpu_usage, args=[90, 10])
    
    # run memory notification in the background
    start_function_in_thread(function=slack_alert_on_memory_usage, args=[90, 60])

    # run disk notification in the background
    start_function_in_thread(function=slack_alert_on_disk_usage, args=[90, 60])