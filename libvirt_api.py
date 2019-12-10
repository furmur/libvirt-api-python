#!/usr/bin/python3
# -*- coding: utf8 -*-

import os
import sys
import threading
import prctl
import asyncio
import libvirtaio
import libvirt
import websockets

try:
    from flask import Flask
    from flask_rest_jsonapi import Api
    from flask_socketio import SocketIO
    from flask_rest_jsonapi.data_layers.alchemy import SqlalchemyDataLayer
except:
    print("# apt install python3-flask python3-flask-socketio python3-libvirt python3-prctl")
    print("$ pip3 install flask_rest_jsonapi")
    raise

from lib.Resources import HypervisorsList, HypervisorDetail, HypervisorRelationship
from lib.Resources import VirtualMachineList, VirtualMachineDetail, VirtualMachineRelationship
from lib.LibVirt import LibVirtMonitorInstance
from lib.LibVirtData import libvirt_data

app = Flask(__name__)
app.config['SECRET_KEY'] = 'SGVsbG8sIHdvcmxkIQ=='
app.config['DEBUG'] = True

api = Api(app)
# ~ socketio = SocketIO(app)

api.route(HypervisorsList, 'hypervisors_list', '/hypervisors')
api.route(HypervisorDetail, 'hypervisor_detail', '/hypervisors/<int:id>','/virtual-machines/<string:virtual_machine_id>/hypervisor')
api.route(HypervisorRelationship, 'hypervisor_virtual_machines', '/hypervisors/<int:id>/relationships/virtual-machines')

api.route(VirtualMachineList, 'virtual_machine_list', '/virtual-machines', '/hypervisors/<int:id>/virtual-machines')
api.route(VirtualMachineDetail, 'virtual_machine_detail', '/virtual-machines/<string:id>')
api.route(VirtualMachineRelationship, 'virtual_machine_hypervisor', '/virtual-machines/<string:id>/relationships/hypervisor')

if __name__ == '__main__':

    monitor_tasks = []

    def libvirt_worker_loop(loop, start_websockets_server, hypervisors):
        def _err_handler(self, ctxt, err):
            print("Error from libvirt : %s", err[2])
        
        print("[{}] entering libvirt_worker_loop".format(threading.get_ident()))

        prctl.set_name('libvirt_loop')

        asyncio.set_event_loop(loop)
        libvirtaio.virEventRegisterAsyncIOImpl()
        libvirt.registerErrorHandler(_err_handler, '_virt_event')

        for id_, h in hypervisors.items():
            monitor_tasks.append(loop.create_task(h['monitor_instance'].watchdog_loop()))

        loop.run_until_complete(start_websockets_server)

        try:
            loop.run_until_complete(asyncio.gather(
                *monitor_tasks
            ))
        except asyncio.CancelledError:
            loop.stop()
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()

    async def cancel_libvirt_worker_loop(loop):
        print("[{}] cancel_libvirt_worker_loop".format(threading.get_ident())) 
        for t in monitor_tasks:
            t.cancel()


    connected_websockets = set()

    async def websockets_handler(websocket, path):
        connected_websockets.add(websocket)
        try:
            print('register websocket',websocket)
            while not websocket.closed:
                await asyncio.sleep(2)
        finally:
            print('unregister websocket',websocket)
            connected_websockets.remove(websocket)

    #init 
    loop = asyncio.new_event_loop()
    libvirt_data.configure(loop, 'cluster.yml',connected_websockets)

    start_websockets_server = websockets.serve(websockets_handler, "localhost", 8765, loop=loop)
    libvirt_worker = threading.Thread(target=libvirt_worker_loop, args=(loop,start_websockets_server,libvirt_data.hypervisors))
    libvirt_worker.start()

    #~ # Start flask application
    print("[{}] entering flask app loop".format(threading.get_ident()))
    app.run(debug=True,use_reloader=False,port=4567)
    # ~ socketio.run(app,debug = True,use_reloader=False,port=4567)

    libvirt_worker_future = asyncio.run_coroutine_threadsafe(cancel_libvirt_worker_loop(loop), loop)
    try:
        libvirt_worker_future.result()
    except:
        #suppress error about closing of the running loop
        pass
    finally:
        libvirt_worker.join()
