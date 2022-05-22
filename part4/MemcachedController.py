import psutil
import DockerController
from threading import Thread

class MemcachedController:
    def __init__(self, cpu_poll_interval:int, cpu_poll_amt:int,  threshhold_up:float, threshhold_down:float, memcached_pid:int):
        self.dc = DockerController()
        self.is_two_core = False
        self.cpu_poll_interval = cpu_poll_interval
        self.cpu_poll_amt = cpu_poll_amt
        self.threshhold_up = threshhold_up #threshold (cpu usage percentage) to switch up to 2 cores
        self.threshhold_down = threshhold_down #threshold (sum of cpu usage percentages) to switch down
        self.memcached_pid = memcached_pid
        self.process = psutil.Process(self.memcached_pid) #may throw NoSuchProcess error if pid does not exist

    def set_1core(self):
        #self.process.cpu_affinity([0])
        self.process.cpu_affinity([3])
        self.is_two_core = False
        self.dc.available_cpus = 3
        self.dc.switch_core()

    def set_2core(self):
        self.process.cpu_affinity([2,3])
        #self.process.cpu_affinity([0,1])
        self.is_two_core = True
        self.dc.available_cpus = 2
        self.dc.switch_core()
    
    def run_monitor(self) -> Thread:
        def run_controller(self):
            self.process.cpu_affinity([3]) #make sure memcached runs on core 0 if not already started with            
            #self.process.cpu_affinity([0]) #make sure memcached runs on core 0 if not already started with

            while True:
                usages = []
                #gather the avg cpu usages every cpu_poll_interval seconds cpu_poll_amt times
                for x in range(0,self.cpu_poll_amt):
                    q = psutil.cpu_percent(interval=self.cpu_poll_interval, percpu=True)
                    if self.is_two_core :
                        usages.append(q[2]+q[3])
                        #usages.append(q[0]+q[1])
                    else:
                        usages.append(q[3])
                        #usages.append(q[0])

                maxUsage = max(usages) #instead of replacing this with 'avg' we could just redo the part above and use a larger cpu_poll_interval and do a choice after every poll
                if (self.is_two_core) and (maxUsage < self.threshhold_down):    #if we are on 2 cores and the maxUsage drops below threshhold_down we switch to 1 core
                    self.set_1core(self)
                elif (not self.is_two_core) and (maxUsage > self.threshhold_up):#if we are on 1 core1 and the maxUsage goes above threshhold_up we switch to 2 cores
                    self.set_2core(self)

        thread = Thread(target=run_controller)
        thread.start()
        return thread

    def run(self):
        mcThread = self.run_monitor(self)
        self.dc.run_sequential().join()
        mcThread.join()