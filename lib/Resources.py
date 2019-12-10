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
    def before_get_object(self, view_kwargs):
        print('before_get_object',view_kwargs)
        if view_kwargs.get('virtual_machine_id') is not None:
            print('replace id here')
            #~ try:
                #~ computer = self.session.query(Computer).filter_by(id=view_kwargs['computer_id']).one()
            #~ except NoResultFound:
                #~ raise ObjectNotFound({'parameter': 'computer_id'},
                                     #~ "Computer: {} not found".format(view_kwargs['computer_id']))
            #~ else:
                #~ if computer.person is not None:
                    #~ view_kwargs['id'] = computer.person.id
                #~ else:
                    #~ view_kwargs['id'] = None

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
