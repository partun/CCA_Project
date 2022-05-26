import docker
from time import sleep, time
from threading import Thread, Lock
from math import floor, log2
from pprint import pprint
import argparse
from MemcachedController import MemcachedController


class DockerController:
    def __init__(self):
        self._client = docker.from_env()

        self._high_qps_mode = False
        self._mode_change_lock = Lock()
        self.stats = dict()

    def set_high_qps_mode(self):
        raise NotImplementedError()

    def set_low_qps_mode(self):
        raise NotImplementedError()

    def start_parsec_dedup(self, threads: int, cpuset: str, auto_remove: bool = True):
        return self._client.containers.run(
            name='parsec_dedup',
            image='anakli/parsec:dedup-native-reduced',
            restart_policy={'NAME': 'no'},
            command=f'./bin/parsecmgmt -a run -p dedup -i native -n {threads}',
            detach=True,
            auto_remove=auto_remove,
            cpuset_cpus=cpuset
        )

    def start_parsec_fft(self, threads: int, cpuset: str, auto_remove: bool = True):
        fft_threads = 2 ** floor(log2(threads))
        if threads != fft_threads:
            print(f'fft threads: {threads} -> {fft_threads}')
        return self._client.containers.run(
            name='parsec_fft',
            image='anakli/parsec:splash2x-fft-native-reduced',
            restart_policy={'NAME': 'no'},
            command=f'./bin/parsecmgmt -a run -p splash2x.fft -i native -n {fft_threads:d}',
            detach=True,
            auto_remove=auto_remove,
            cpuset_cpus=cpuset
        )

    def start_parsec_ferret(self, threads: int, cpuset: str, auto_remove: bool = True):
        return self._client.containers.run(
            name='parsec_ferret',
            image='anakli/parsec:ferret-native-reduced',
            restart_policy={'NAME': 'no'},
            command=f'./bin/parsecmgmt -a run -p ferret -i native -n {threads}',
            detach=True,
            auto_remove=auto_remove,
            cpuset_cpus=cpuset
        )

    def start_parsec_blackscholes(self, threads: int, cpuset: str, auto_remove: bool = True):
        return self._client.containers.run(
            name='parsec_blackscholes',
            image='anakli/parsec:blackscholes-native-reduced',
            restart_policy={'NAME': 'no'},
            command=f'./bin/parsecmgmt -a run -p blackscholes -i native -n {threads}',
            detach=True,
            auto_remove=auto_remove,
            cpuset_cpus=cpuset
        )

    def start_parsec_canneal(self, threads: int, cpuset: str, auto_remove: bool = True):
        return self._client.containers.run(
            name='parsec_canneal',
            image='anakli/parsec:canneal-native-reduced',
            restart_policy={'NAME': 'no'},
            command=f'./bin/parsecmgmt -a run -p canneal -i native -n {threads}',
            detach=True,
            auto_remove=auto_remove,
            cpuset_cpus=cpuset
        )

    def start_parsec_freqmine(self, threads: int, cpuset: str, auto_remove: bool = True):
        return self._client.containers.run(
            name='parsec_freqmine',
            image='anakli/parsec:freqmine-native-reduced',
            restart_policy={'NAME': 'no'},
            command=f'./bin/parsecmgmt -a run -p freqmine -i native -n {threads}',
            detach=True,
            auto_remove=auto_remove,
            cpuset_cpus=cpuset
        )


class SequentialDockerController(DockerController):
    def __init__(self):
        self.container = None
        self.high_qps_cpu_set = '0,1'
        self.low_qps_cpu_set = '0,1,2'

        self.execution_ord = [
            ('parsec_ferret', self.start_parsec_ferret),
            ('parsec_freqmine', self.start_parsec_freqmine),
            ('parsec_cannel', self.start_parsec_canneal),
            ('parsec_blackscholes', self.start_parsec_blackscholes),
            ('parsec_fft', self.start_parsec_fft),
            ('parsec_dedup', self.start_parsec_dedup)
        ]

        super().__init__()

    def set_high_qps_mode(self):
        with self._mode_change_lock:
            self._high_qps_mode = True
            self.container.update(cpuset_cpus=self.high_qps_cpu_set)

    def set_low_qps_mode(self):
        with self._mode_change_lock:
            self._high_qps_mode = False
            self.container.update(cpuset_cpus=self.low_qps_cpu_set)

    def run(self):
        self.stats['total'] = {'start': time()}
        for workload, start_func in self.execution_ord:
            with self._mode_change_lock:
                print(f'starting {workload}...')
                self.stats[workload] = {'start': time()}
                if self._high_qps_mode:
                    self.container = start_func(
                        threads=3, cpuset=self.high_qps_cpu_set)
                else:
                    self.container = start_func(
                        threads=3, cpuset=self.low_qps_cpu_set)

            return_core = self.container.wait()
            self.stats[workload]['end'] = time()
            self.stats[workload]['duration'] = self.stats[workload]['end'] - \
                self.stats[workload]['start']
            print(
                f'{workload} duration: {self.stats[workload]["duration"]:.2f}s finished: {return_core}')

        self.stats['total']['end'] = time()
        self.stats['total']['duration'] = self.stats['total']['end'] - \
            self.stats['total']['start']
        pprint(self.stats)


class SwitchingDockerController(DockerController):
    def __init__(self):
        self.exec_idx = 0
        self.high_qps_container = None
        self.low_qps_container = None
        self.finishing = False
        self.low_qps_tasks_remaining = False

        self.high_qps_cpu_set = '0,1'
        self.low_qps_cpu_set = '0,1,2'

        self.execution_ord = [
            # fft first because it can only run with 2 threads anyway so use it for high qps mode
            ('parsec_fft', self.start_parsec_fft),
            ('parsec_ferret', self.start_parsec_ferret),
            ('parsec_freqmine', self.start_parsec_freqmine),
            ('parsec_cannel', self.start_parsec_canneal),
            ('parsec_blackscholes', self.start_parsec_blackscholes),
            ('parsec_dedup', self.start_parsec_dedup)
        ]

        super().__init__()

    @staticmethod
    def pause(container):
        print(f'{time()}: pausing {container.name}')
        container.pause()

    @staticmethod
    def unpause(container):
        print(f'{time()}: unpausing {container.name}')
        container.unpause()

    def set_high_qps_mode(self):
        with self._mode_change_lock:
            if not self.finishing:
                if self.low_qps_tasks_remaining:
                    self.low_qps_container.update(
                        cpuset_cpus=self.high_qps_cpu_set)
                self.pause(self.low_qps_container)
                self.unpause(self.high_qps_container)
            self._high_qps_mode = True

    def set_low_qps_mode(self):
        with self._mode_change_lock:
            if not self.finishing:
                if self.low_qps_tasks_remaining:
                    self.low_qps_container.update(
                        cpuset_cpus=self.low_qps_cpu_set)
                self.pause(self.high_qps_container)
                self.unpause(self.low_qps_container)
            self._high_qps_mode = False

    def run(self):
        self.stats['total'] = {'start': time()}

        def low_qps_waiter():
            while True:
                with self._mode_change_lock:
                    if not self.exec_idx < len(self.execution_ord):
                        print('done lqps')
                        if self.finishing:
                            return
                        self.finishing = True
                        self.unpause(self.high_qps_container)
                        self._high_qps_mode = True
                        return

                    workload, start_func = self.execution_ord[self.exec_idx]
                    print(f'starting lqps {workload}...')
                    self.stats[workload] = {'start': time()}
                    self.low_qps_container = start_func(
                        threads=3, cpuset=self.low_qps_cpu_set)
                    self.exec_idx += 1

                return_core = self.low_qps_container.wait()
                self.stats[workload]['end'] = time()
                self.stats[workload]['duration'] = self.stats[workload]['end'] - \
                    self.stats[workload]['start']
                print(
                    f'{workload} duration: {self.stats[workload]["duration"]:.2f}s finished: {return_core}')

        def high_qps_waiter():
            while True:
                with self._mode_change_lock:
                    if not self.exec_idx < len(self.execution_ord):
                        print('done hqps')
                        if self.finishing:
                            return

                        self.finishing = True
                        self.low_qps_tasks_remaining = True
                        if self._high_qps_mode:
                            self.low_qps_container.update(
                                cpuset_cpus=self.high_qps_cpu_set)
                        self.unpause(self.low_qps_container)
                        return

                    workload, start_func = self.execution_ord[self.exec_idx]
                    print(f'starting hqps {workload}...')
                    self.stats[workload] = {'start': time()}
                    self.high_qps_container = start_func(
                        threads=2, cpuset=self.high_qps_cpu_set)
                    self.pause(self.high_qps_container)
                    self.exec_idx += 1

                return_core = self.high_qps_container.wait()
                self.stats[workload]['end'] = time()
                self.stats[workload]['duration'] = self.stats[workload]['end'] - \
                    self.stats[workload]['start']
                print(
                    f'{workload} duration: {self.stats[workload]["duration"]:.2f}s finished: {return_core}')

        thread = Thread(target=high_qps_waiter, daemon=True)
        thread.start()
        low_qps_waiter()
        thread.join()
        self.stats['total']['end'] = time()
        self.stats['total']['duration'] = self.stats['total']['end'] - \
            self.stats['total']['start']
        pprint(self.stats)


def test():
    # d = SequentialDockerController()
    d = SwitchingDockerController()
    # d.start_parsec_blackscholes(3, '0,1,2')

    d.run()


def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-p', '--pid', type=int, help='memcached process id')
    parser.add_argument('-m', "--mode", type=int,
                        default=0, help="select mode")
    parser.add_argument('-i', "--interval", type=float,
                        default=0.3, help="cpu usage sampling interval")
    parser.add_argument('-n', "--amt", type=int, default=2,
                        help="number of cpu usage samples")
    parser.add_argument('-u', "--high_qps_threshold",
                        type=float, default=95, help="")
    parser.add_argument('-l', "--low_qps_threshold",
                        type=float, default=140, help="")
    parser.add_argument('-t', "--min_duration",
                        type=float, default=4, help="")

    args = parser.parse_args()

    print(args)

    if args.mode == 0:
        controller = SequentialDockerController()
    elif args.mode == 1:
        controller = SwitchingDockerController()
    else:
        raise ValueError('invalid mode')

    mem_controller = MemcachedController(
        docker_controller=controller,
        cpu_sampling_interval=args.interval,
        cpu_sampling_amt=args.amt,
        high_qps_threshold=args.high_qps_threshold,
        low_qps_threshold=args.low_qps_threshold,
        memcached_pid=args.pid,
        min_high_qps_mode_duration=args.min_duration
    )
    mem_controller.run_in_thread()

    # sleep(5)

    controller.run()


if __name__ == '__main__':
    main()
