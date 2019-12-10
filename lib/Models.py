#!/usr/bin/python3
# -*- coding: utf8 -*-

import libvirt

virDomainStates = {
    libvirt.VIR_DOMAIN_NOSTATE: 'no state',
    libvirt.VIR_DOMAIN_RUNNING: 'running',
    libvirt.VIR_DOMAIN_BLOCKED: 'blocked on resource',
    libvirt.VIR_DOMAIN_PAUSED:  'paused',
    libvirt.VIR_DOMAIN_SHUTDOWN: 'being shut down',
    libvirt.VIR_DOMAIN_SHUTOFF: 'shut off',
    libvirt.VIR_DOMAIN_CRASHED: 'crashed',
    libvirt.VIR_DOMAIN_PMSUSPENDED: 'suspended by guest power management'
}

class Hypervisor():
    def __init__(self, id, name, c = None):
        self.id = id
        self.name = name
        if c is None:
            return
        self.version = c.getVersion()
        self.libversion = c.getLibVersion()
        self.hostname = c.getHostname()

        self.info = c.getInfo()
        for k,v in zip(["cpu_model","total_memory","cpus","mhz","numa_nodes","cpu_sockets","cpu_cores","cpu_threads"],self.info):
            setattr(self,k,v)
        self.total_memory = self.total_memory * 1024 * 1024
        self.free_memory = c.getFreeMemory()

        #~ for attr, value in self.__dict__.items():
            #~ print('Hypervisor',self.hostname, attr,':', value)

class VirtualMachine():
    def __init__(self, id, hv, d):
        self.id = id
        self.hypervisor = hv
        self.name = d.name()
        self.xml = d.XMLDesc()
        self.state = virDomainStates[d.state()[0]]
        self.memory = d.maxMemory() * 1024
        try:
            self.cpus = d.maxVcpus()
        except:
            self.cpus = 0

        #~ for attr, value in self.__dict__.items():
            #~ if attr == 'xml':
                #~ continue
            #~ print('VirtualMachine',self.id, attr,':', value)

