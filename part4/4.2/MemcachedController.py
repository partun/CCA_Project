import psutil
from threading import Thread
from time import time


class MemcachedController:
    def __init__(self, docker_controller, cpu_sampling_interval: float, cpu_sampling_amt: int,
                 high_qps_threshold, low_qps_threshold, memcached_pid: int,
                 min_high_qps_mode_duration
                 ):
        self.dc = docker_controller
        self.high_qps_mode = False

        self.last_mode_transition = 0
        self.min_high_qps_mode_duration = min_high_qps_mode_duration
        self.high_qps_threshold = high_qps_threshold
        self.low_qps_threshold = low_qps_threshold

        self.cpu_sampling_interval = cpu_sampling_interval
        self.cpu_sampling_amt = cpu_sampling_amt
        self.memcached_process = psutil.Process(memcached_pid)  # may throw NoSuchProcess error if pid does not exist
        self.memcached_process.cpu_affinity([3])  # make sure memcached runs on core 0 if not already started with

    def set_high_qps_mode(self, timestamp):
        self.high_qps_mode = True
        self.last_mode_transition = timestamp
        print(f'{timestamp}: high qps mode')
        self.memcached_process.cpu_affinity([2, 3])
        self.dc.set_high_qps_mode()

    def set_low_qps_mode(self, timestamp):
        self.high_qps_mode = False
        self.last_mode_transition = timestamp
        print(f'{timestamp}: low qps mode')
        self.memcached_process.cpu_affinity([3])
        self.dc.set_low_qps_mode()

    def run_in_thread(self) -> Thread:
        def run_controller():
            while True:
                agg_usage = 0
                # gather the avg cpu usages every cpu_poll_interval seconds cpu_poll_amt times
                for _ in range(self.cpu_sampling_amt):
                    q = psutil.cpu_percent(interval=self.cpu_sampling_interval, percpu=True)
                    usage = q[2] + q[3] if self.high_qps_mode else q[3]
                    if usage > agg_usage:
                        agg_usage = usage

                now = time()
                if not self.high_qps_mode and agg_usage > self.high_qps_threshold:
                    self.set_high_qps_mode(now)

                elif self.high_qps_mode and agg_usage < self.low_qps_threshold and \
                        now - self.last_mode_transition > self.min_high_qps_mode_duration:
                    self.set_low_qps_mode(now)

        self.thread = Thread(target=run_controller, daemon=True)
        self.thread.start()

    def wait(self):
        self.thread.join()
