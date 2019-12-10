#!/usr/bin/python3
# -*- coding: utf8 -*-

import threading 
import yaml
import sys

from flask import current_app
from flask_rest_jsonapi.data_layers.base import BaseDataLayer
from .Models import VirtualMachine, Hypervisor
from .LibVirt import LibVirtMonitorInstance

from flask_rest_jsonapi.exceptions import ObjectNotFound

class LibVirtData:
    def __init__(self):
        self.hypervisors = {}
        self.mutex = threading.Lock()

    def configure(self, loop, filename, socketio):
        with open(filename, 'r') as f:
            self.cfg = yaml.load(f)
            #~ print(self.cfg)

        for hv in self.cfg['hypervisors']:
            self.hypervisors[hv['id']] = {
                'monitor_instance': LibVirtMonitorInstance(hv['id'], hv['uri'], hv['name'], loop, self, socketio),
                'name': hv['name'],
                'uri': hv['uri'],
                'model': Hypervisor(hv['id'],hv['name']),
                'vms': []
            }

    def update_hv_info(self, hv_id, c):
        #fill hv info
        hv_data = self.hypervisors[hv_id]
        h = Hypervisor(hv_id,hv_data['name'],c)

        #fill vms info
        vms = dict()
        for d in c.listAllDomains():
            vm_id = d.UUIDString()
            try:
                vms[vm_id] = VirtualMachine(vm_id,h,d)
            except Exception as e:
                print('vm {} add exception: {}'.format(vm_id,e))
            except:
                print('vm {} add exception: {}'.format(vm_id,sys.exc_info()))


        #replace info
        with self.mutex:
            self.hypervisors[hv_id]['model'] = h
            self.hypervisors[hv_id]['vms'] = vms

    def get_hv_id_by_vm(self, vm_id):
        hv_id = None
        for hv_id_i, hv in self.hypervisors.items():
            if vm_id in hv['vms']:
                hv_id = hv_id_i
                break
        return hv_id

    def get_hv_object(self, hv_id):
        if hv_id not in self.hypervisors:
            raise ObjectNotFound('no hypervisor with id: ' + str(hv_id))
        o = None
        with self.mutex:
            o = self.hypervisors[hv_id]['model']
        return o

    def get_hv_collection(self, vm_id = None):
        # ~ print('get_hv_collection',vm_id)
        hv = []
        with self.mutex:
            for i, h in self.hypervisors.items():
                hv.append(h['model'])
        return hv

    def get_vm_object(self, vm_id):
        vm = None
        with self.mutex:
            for hv_id, hv in self.hypervisors.items():
                if vm_id in hv['vms']:
                    vm = hv['vms'][vm_id]
                    break
        if not vm:
            raise ObjectNotFound('no hypervisor with id: ' + vm_id)
        return vm

    def get_vm_collection(self, hv_id = None):
        vms = []
        with self.mutex:
            if hv_id:
                if hv_id not in self.hypervisors:
                    raise ObjectNotFound('no hypervisor with id: {} on vms collection get'.format(vm_id))
                hv = self.hypervisors[hv_id]
                for k,vm in hv['vms'].items():
                    vms.append(vm)
            else:
                for hv_id, hv in self.hypervisors.items():
                    for k,vm in hv['vms'].items():
                        vms.append(vm)
        return vms

    class LibVirtQuery():
        def __init__(self, get_object, get_collection):
            self.get_object = get_object
            self.get_collection = get_collection

    def query(self, model):
        if issubclass(model, VirtualMachine):
            return self.LibVirtQuery(self.get_vm_object, self.get_vm_collection)
        elif issubclass(model, Hypervisor):
            return self.LibVirtQuery(self.get_hv_object, self.get_hv_collection)
        else:
            raise Exception("Unsupported model {}".format(kwargs['model']))

    def get_related_query(self, relation_name):
        if relation_name=='virtual-machines':
            return self.LibVirtQuery(self.get_vm_object, self.get_vm_collection)
        else:
            raise Exception("Unknown relation name {}".format(relation_name))

if 'libvirt_data' not in globals():
    libvirt_data = LibVirtData()

class LibVirtDataLayer(BaseDataLayer):
    def __init__(self, kwargs):
        super(LibVirtDataLayer, self).__init__(kwargs)

        if not hasattr(self, 'model'):
            raise Exception("You must provide a model in data_layer_kwargs to use libvirt data layer in {}"
                            .format(self.__name__))

        #~ print('init data layer',kwargs['model'])
        self.query = libvirt_data.query(kwargs['model'])

    def get_object(self, view_kwargs, qs=None):
        """Retrieve an object

        :params dict view_kwargs: kwargs from the resource view
        :return DeclarativeMeta: an object
        """
        print('get_object', view_kwargs,qs,qs.__dict__)

        if view_kwargs.get('virtual_machine_id') is not None:
            #get hv id by vm id
            view_kwargs['id'] = libvirt_data.get_hv_id_by_vm(view_kwargs.get('virtual_machine_id'))
            print(view_kwargs['id'])

        url_field = getattr(self, 'url_field', 'id')
        filter_value = view_kwargs[url_field]

        return self.query.get_object(filter_value)

    def get_collection(self, qs, view_kwargs):
        """Retrieve a collection of objects

        :param QueryStringManager qs: a querystring manager to retrieve information from url
        :param dict view_kwargs: kwargs from the resource view
        :return tuple: the number of object and the list of objects
        """
        #~ if 'id' in view_kwargs else None
        # ~ if qs.filters:
            # ~ query = self.filter_query(query, qs.filters, self.model)

        # ~ if qs.sorting:
            # ~ query = self.sort_query(query, qs.sorting)

        collection = self.query.get_collection(view_kwargs['id'] if 'id' in view_kwargs else None)
        object_count = len(collection)

        # ~ if getattr(self, 'eagerload_includes', True):
            # ~ query = self.eagerload_includes(query, qs)

        collection = self.paginate_data(collection, qs.pagination)

        return object_count, collection

    def get_relationship(self, relationship_field, related_type_, related_id_field, view_kwargs):
        """Get information about a relationship

        :param str relationship_field: the model attribute used for relationship
        :param str related_type_: the related resource type
        :param str related_id_field: the identifier field of the related model
        :param dict view_kwargs: kwargs from the resource view
        :return tuple: the object and related object(s)
        """

        print(self,relationship_field, related_type_, related_id_field, view_kwargs)

        filter_value = view_kwargs[related_id_field]

        relation_query = libvirt_data.get_related_query(related_type_)
        obj = self.query.get_object(filter_value)

        collection = relation_query.get_collection(filter_value)
        #~ print(obj,collection)

        return obj, [obj.id for obj in collection]

    def paginate_data(self, collection, paginate_info):
        """Paginate query according to jsonapi 1.0

        :param dict collection: data collection
        :param dict paginate_info: pagination information
        :return dict collection: the paginated collection
        """
        if int(paginate_info.get('size', 1)) == 0:
            return collection

        page_size = int(paginate_info.get('size', 0)) or current_app.config['PAGE_SIZE']

        offset = 0
        if paginate_info.get('number'):
            offset = (int(paginate_info['number']) - 1) * page_size

        return collection[offset : (offset + page_size)]
