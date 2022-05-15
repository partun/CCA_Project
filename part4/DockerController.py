import docker
from time import sleep
from threading import Thread


class DockerController:
    def __init__(self):
        self._client = docker.from_env()

        self._running = None

    def pause_running(self):
        if self._running is not None:
            self._running.pause()

    def unpause_running(self):
        if self._running is not None:
            self._running.unpause()

    def update_cpu_set(self, cpu_set: str):
        if self._running is not None:
            self._running.update(cpuset_cpus=cpu_set)

    @staticmethod
    def wait_on_container_and_cal(container, callback):
        def waiter():
            return_core = container.wait()
            print(return_core)
            callback()
        Thread(target=waiter).start()

    def start_parsec_dedup(self):
        self._running = self._client.containers.run(
            name='parsec_dedup',
            image='anakli/parsec:dedup-native-reduced',
            restart_policy={'NAME': 'no'},
            command="./bin/parsecmgmt -a run -p dedup -i native -n 2",
            detach=True,
            auto_remove=True,
            cpuset_cpus='0,2'
        )

    def start_parsec_fft(self):
        self._client.containers.run(
            name='parsec_fft',
            image='anakli/parsec:splash2x-fft-native-reduced',
            restart_policy={'NAME': 'no'},
            command="./bin/parsecmgmt -a run -p splash2x.fft -i native -n 1"
        )


def test():
    d = DockerController()

    print(d._client.containers.list())

    d.start_parsec_dedup()

    d.wait_on_container_and_cal(d._running, lambda: print('done'))

    sleep(100)


if __name__ == '__main__':
    test()
