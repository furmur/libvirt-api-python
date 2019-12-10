#!/usr/bin/python3
# -*- coding: utf8 -*-

from marshmallow_jsonapi.flask import Schema, SchemaOpts, Relationship
from marshmallow_jsonapi import fields

#~ def dasherize(text):
    #~ return text.replace('_', '-')

class HypervisorsSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str()

    version = fields.Integer()
    libversion = fields.Integer()
    hostname = fields.Str()
    cpu_model = fields.Str()
    total_memory = fields.Integer()
    cpus = fields.Integer()
    mhz = fields.Integer()
    numa_nodes = fields.Integer()
    cpu_sockets = fields.Integer()
    cpu_cores = fields.Integer()
    cpu_threads = fields.Integer()
    free_memory = fields.Integer()

    class Meta:
        type_ = 'hypervisor'
        self_view = 'hypervisor_detail'
        self_view_kwargs = {'id': '<id>'}
        self_view_many = 'hypervisors_list'
        strict = True
        include_resource_linkage=True
        include_resource_relationship=True
        #~ inflect = dasherize

    virtual_machines = Relationship(
        attribute = 'virtual-machines',
        self_view='hypervisor_virtual_machines',
        self_view_kwargs={'id': '<id>'},
        related_view='virtual_machine_list',
        related_view_kwargs={'hypervisor_id': '<id>'},
        many=True,
        include_resource_linkage=True,
        include_resource_relationship=True,
        schema='VirtualMachinesSchema',
        type_='virtual-machines')

class VirtualMachinesSchema(Schema):
    id = fields.Str(dump_only=True)
    name = fields.Str()
    state = fields.Str()
    cpus = fields.Integer()
    maxMemory = fields.Integer()
    xml = fields.Str()

    #~ hypervizor_id = fields.Int()
    class Meta:
        type_ = 'virtual-machines'
        self_view = 'virtual_machine_detail'
        self_view_kwargs = {'id': '<id>'}
        self_view_many = 'virtual_machine_list'
        strict = True
        include_resource_linkage=True
        include_resource_relationship=True
        #~ inflect = dasherize

    hypervisor = Relationship(
        attribute='hypervisor',
        self_view='virtual_machine_hypervisor',
        self_view_kwargs={'id': '<id>'},
        related_view='hypervisor_detail',
        related_view_kwargs={'virtual_machine_id': '<id>'},
        include_resource_linkage=True,
        include_resource_relationship=True,
        schema='HypervisorsSchema',
        type_='hypervisor')
