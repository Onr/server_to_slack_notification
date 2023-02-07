import time
import logging

import toml
import psutil
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


def slack_alert_on_cpu_usage(time_step=0, active=True, period=30, threshold=90):
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

    

if __name__ == "__main__":
    # read config file
    with open('notification_config.toml') as f:
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
    }
    time_step = 0
    while True:
        # Call notifications
        for key in notifications_func_dict.keys():
           notifications_func_dict[key](time_step, **config[key])

        # Check if config file changed
        with open('notification_config.toml') as f:
            new_config = toml.load(f)
            if new_config != config:
                config = new_config
                logging.info(f"Config changed \nNew config: \n{config}")

        # Increment time step
        time_step = (time_step + 1) % (60*60*24*7)
        time.sleep(1)

