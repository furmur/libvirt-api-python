#!/usr/bin/python3
# -*- coding: utf8 -*-

from flask_rest_jsonapi.data_layers.alchemy import SqlalchemyDataLayer
from flask_rest_jsonapi import ResourceDetail, ResourceList, ResourceRelationship

from .Schemes import VirtualMachinesSchema, HypervisorsSchema
from .LibVirtData import LibVirtData, LibVirtDataLayer
from .Models import VirtualMachine, Hypervisor

class HypervisorsList(ResourceList):
    schema = HypervisorsSchema
    data_layer = {
        'class': LibVirtDataLayer,
        'model': Hypervisor
    }

class HypervisorDetail(ResourceDetail):
    schema = HypervisorsSchema
    data_layer = {
        'class': LibVirtDataLayer,
        'model': Hypervisor
    }

class HypervisorRelationship(ResourceRelationship):
    schema = HypervisorsSchema
    data_layer = {
        'class': LibVirtDataLayer,
        'model': Hypervisor
    }

class VirtualMachineList(ResourceList):
    schema = VirtualMachinesSchema
    data_layer = {
        'class': LibVirtDataLayer,
        'model': VirtualMachine
    }

class VirtualMachineDetail(ResourceDetail):
    schema = VirtualMachinesSchema
    data_layer = {
        'class': LibVirtDataLayer,
        'model': VirtualMachine
    }

class VirtualMachineRelationship(ResourceRelationship):
    schema = VirtualMachinesSchema
    data_layer = {
        'class': LibVirtDataLayer,
        'model': VirtualMachine
    }
