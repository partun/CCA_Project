import docker
from time import sleep
from threading import Thread
from math import floor, log2


class DockerController:
    def __init__(self):
        self._client = docker.from_env()

        self.execution_ord = [
            self.start_parsec_ferret,
            self.start_parsec_freqmine,
            self.start_parsec_canneal,
            self.start_parsec_blackscholes,
            self.start_parsec_fft,
            self.start_parsec_dedup
        ]

        self.max_cpus_per_workload = 3
        self.available_cpus = 3
        self.next_workload_index = 0 #why this start index?
        self.running_container = None

    @staticmethod
    def get_cpuset_str(end: int, start: int = 0) -> str:
        return ','.join(map(str, range(start, end)))

    @staticmethod
    def update_cpu_set(container, cpuset: str):
        container.update(cpuset_cpus=cpuset)

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

    def run_sequential(self) -> Thread:

        def wait_to_run_next_container(container=None):
            if container is not None:
                return_core = container.wait()
                print(f'job finished: {return_core}')

            if self.next_workload_index >= len(self.execution_ord):
                # done: executed all workloads
                return

            container = self.execution_ord[self.next_workload_index](
                threads=self.max_cpus_per_workload,
                cpuset=self.get_cpuset_str(self.available_cpus)
            )
            print(f'started {self.next_workload_index}')
            self.running_container = container
            self.next_workload_index += 1
            wait_to_run_next_container(container)

        thread = Thread(target=wait_to_run_next_container)
        thread.start()
        return thread

    def switch_core(self):
        cpuset = self.get_cpuset_str(self.available_cpus)
        self.update_cpu_set(self.running_container, cpuset)


def test():
    d = DockerController()
    # d.start_parsec_blackscholes(3, '0,1,2')

    d.run_sequential().join()


#if __name__ == '__main__':
#    test()
