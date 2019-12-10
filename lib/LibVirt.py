#!/usr/bin/python3
# -*- coding: utf8 -*-

import libvirt
import libvirtaio
import threading
import socket
import time
import sys
import datetime
import time
import json
import prctl
import asyncio

# If is not defined internal , -1 is stored.
DUMMY = -1

# Enumerate all event that can get.
# Comment out events that is not targeted in the callback.
event_filter_dic = {
    libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE:
    {
        libvirt.VIR_DOMAIN_EVENT_SUSPENDED:
        (
            libvirt.VIR_DOMAIN_EVENT_SUSPENDED_IOERROR,
            libvirt.VIR_DOMAIN_EVENT_SUSPENDED_WATCHDOG,
            libvirt.VIR_DOMAIN_EVENT_SUSPENDED_API_ERROR
        ),
        libvirt.VIR_DOMAIN_EVENT_STOPPED:
        (
            libvirt.VIR_DOMAIN_EVENT_STOPPED_SHUTDOWN,
            libvirt.VIR_DOMAIN_EVENT_STOPPED_DESTROYED,
            libvirt.VIR_DOMAIN_EVENT_STOPPED_FAILED,
        ),
        libvirt.VIR_DOMAIN_EVENT_SHUTDOWN:
        (
            libvirt.VIR_DOMAIN_EVENT_SHUTDOWN_FINISHED,
        )
    },
    libvirt.VIR_DOMAIN_EVENT_ID_REBOOT: {DUMMY: (DUMMY,)},
    libvirt.VIR_DOMAIN_EVENT_ID_RTC_CHANGE: {DUMMY: (DUMMY,)},
    libvirt.VIR_DOMAIN_EVENT_ID_WATCHDOG:
    {
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_NONE: (DUMMY,),
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_PAUSE: (DUMMY,),
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_RESET: (DUMMY,),
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_POWEROFF: (DUMMY,),
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_SHUTDOWN: (DUMMY,),
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_DEBUG: (DUMMY,)
    },
    libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR:
    {
        libvirt.VIR_DOMAIN_EVENT_IO_ERROR_NONE: (DUMMY,),
        libvirt.VIR_DOMAIN_EVENT_IO_ERROR_PAUSE: (DUMMY,),
        libvirt.VIR_DOMAIN_EVENT_IO_ERROR_REPORT: (DUMMY,)
    },
    libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR_REASON: {DUMMY: (DUMMY,)},
    libvirt.VIR_DOMAIN_EVENT_ID_CONTROL_ERROR: {DUMMY: (DUMMY,)}

}

eventID_dic = {
    libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE: 'LIFECYCLE',
    libvirt.VIR_DOMAIN_EVENT_ID_RTC_CHANGE: 'RTC_CHANGE',
    libvirt.VIR_DOMAIN_EVENT_ID_REBOOT: 'REBOOT',
    libvirt.VIR_DOMAIN_EVENT_ID_WATCHDOG: 'WATCHDOG',
    libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR: 'IO_ERROR',
    libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR_REASON: 'IO_ERROR_REASON',
    libvirt.VIR_DOMAIN_EVENT_ID_CONTROL_ERROR: 'CONTROL_ERROR'}

detail_dic = {
    libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE: {
        libvirt.VIR_DOMAIN_EVENT_SUSPENDED: {
            libvirt.VIR_DOMAIN_EVENT_SUSPENDED_IOERROR:
            'SUSPENDED_IOERROR',
            libvirt.VIR_DOMAIN_EVENT_SUSPENDED_WATCHDOG:
            'SUSPENDED_WATCHDOG',
            libvirt.VIR_DOMAIN_EVENT_SUSPENDED_API_ERROR:
            'SUSPENDED_API_ERROR'},
        libvirt.VIR_DOMAIN_EVENT_STOPPED: {
            libvirt.VIR_DOMAIN_EVENT_STOPPED_SHUTDOWN:
            'STOPPED_SHUTDOWN',
            libvirt.VIR_DOMAIN_EVENT_STOPPED_DESTROYED:
            'STOPPED_DESTROYED',
            libvirt.VIR_DOMAIN_EVENT_STOPPED_FAILED:
            'STOPPED_FAILED'},
        libvirt.VIR_DOMAIN_EVENT_SHUTDOWN: {
            libvirt.VIR_DOMAIN_EVENT_SHUTDOWN_FINISHED:
            'SHUTDOWN_FINISHED'}
    },
    libvirt.VIR_DOMAIN_EVENT_ID_REBOOT: {
        DUMMY: {
            DUMMY: 'UNKNOWN'}},
    libvirt.VIR_DOMAIN_EVENT_ID_RTC_CHANGE: {
        DUMMY: {
            DUMMY: 'UNKNOWN'}},
    libvirt.VIR_DOMAIN_EVENT_ID_WATCHDOG: {
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_NONE: {
            DUMMY: 'WATCHDOG_NONE'},
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_PAUSE: {
            DUMMY: 'WATCHDOG_PAUSE'},
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_RESET: {
            DUMMY: 'WATCHDOG_RESET'},
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_POWEROFF: {
            DUMMY: 'WATCHDOG_POWEROFF'},
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_SHUTDOWN: {
            DUMMY: 'WATCHDOG_SHUTDOWN'},
        libvirt.VIR_DOMAIN_EVENT_WATCHDOG_DEBUG: {
            DUMMY: 'WATCHDOG_DEBUG'}},
    libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR: {
        libvirt.VIR_DOMAIN_EVENT_IO_ERROR_NONE: {
            DUMMY: 'IO_ERROR_NONE'},
        libvirt.VIR_DOMAIN_EVENT_IO_ERROR_PAUSE: {
            DUMMY: 'IO_ERROR_PAUSE'},
        libvirt.VIR_DOMAIN_EVENT_IO_ERROR_REPORT: {
            DUMMY: 'IO_ERROR_REPORT'}},
    libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR_REASON: {
        DUMMY: {
            DUMMY: 'UNKNOWN'}},
    libvirt.VIR_DOMAIN_EVENT_ID_CONTROL_ERROR: {
        DUMMY: {
            DUMMY: 'UNKNOWN'}}
}

class Callback(object):
    """Class of callback processing."""

    def __init__(self, hypervisor_name):
        self.hypervisor_name = hypervisor_name

    def libvirt_event_callback(self, event_id, details, domain_uuid,
                               notice_type, hostname, current_time):
        """Callback method.
        Callback processing be executed as result of the
        libvirt event filter.
        :param event_id: Event ID notify to the callback function
        :param details: Event code notify to the callback function
        :param domain_uuid: Uuid notify to the callback function
        :param notice_type: Notice type notify to the callback function
        :param hostname: Server host name of the source an event occur
                         notify to the callback function
        :param current_time: Event occurred time notify to the callback
                            function
        """

        # Set the event to the dictionary.
        event = {
            'notification': {
                'hypervisor_name': self.hypervisor_name,
                'type': notice_type,
                'hostname': hostname,
                'generated_time': current_time,
                'payload': {
                    'event': event_id,
                    'instance_uuid': domain_uuid,
                    'vir_domain_event': details
                }
            }
        }
        print(json.dumps(event, sort_keys=True, indent=4))
        #TODO: broadcast to websockets


class EventFilter(object):
    """Class of filtering events."""

    def __init__(self,hypervisor_name):
        self.callback = Callback(hypervisor_name)
        self.hypervisor_name = hypervisor_name

    def vir_event_filter(self, eventID, eventType, detail, uuID):
        """Filter events from libvirt.
        :param eventID: EventID
        :param eventType: Event type
        :param detail: Event name
        :pram uuID: UUID
        """

        noticeType = 'TYPE_VM'
        hostname = socket.gethostname()
        currentTime = time.time()

        try:
            # ~ print('event_filter_dic',eventID,eventType)
            if detail in event_filter_dic[eventID][eventType]:
                # ~ print("Event Filter Matched.")
                eventID_val = eventID_dic[eventID]
                # ~ print('detail_val:',eventID,eventType,detail)
                detail_val =  detail_dic[eventID][eventType][detail]

                asyncio.get_running_loop().call_soon(self.callback.libvirt_event_callback, eventID_val, detail_val,uuID, noticeType,hostname, currentTime)

        except KeyError as e:
            print("virEventFilter KeyError",e)
        except IndexError as e:
            print("virEventFilter IndexError",e)
        except TypeError as e:
            print("virEventFilter TypeError",e)
        except NameError as e:
            print("NameError", e)
        except Exception:
            print("Unexpected error: %s" % sys.exc_info()[0])

class LibVirtMonitorInstance(object):
    def __init__(self, id_, uri, name, loop, data, *args, **kwargs):
        self.uri = uri
        self.id_ = id_
        self.data = data
        self.loop = loop
        self.name = name
        self.watchdog_timeout = 1
        self.event_loop_thread = None
        self.evf = EventFilter(self.name)
        self.vc = None
        self.callback_ids = []

        self.event_callback_handlers = {
            libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE:
                self._my_domain_event_callback,
            libvirt.VIR_DOMAIN_EVENT_ID_REBOOT:
                self._my_domain_event_reboot_callback,
            libvirt.VIR_DOMAIN_EVENT_ID_RTC_CHANGE:
                self._my_domain_event_rtc_change_callback,
            libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR:
                self._my_domain_event_io_error_callback,
            libvirt.VIR_DOMAIN_EVENT_ID_WATCHDOG:
                self._my_domain_event_watchdog_callback,
            libvirt.VIR_DOMAIN_EVENT_ID_GRAPHICS:
                self._my_domain_event_graphics_callback,
            libvirt.VIR_DOMAIN_EVENT_ID_DISK_CHANGE:
                self._my_domain_event_disk_change_callback,
            libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR_REASON:
                self._my_domain_event_io_error_reason_callback,
            libvirt.VIR_DOMAIN_EVENT_ID_CONTROL_ERROR:
                self._my_domain_event_generic_callback
        }

    def _my_domain_event_callback(self, conn, dom, event, detail, opaque):
        self.evf.vir_event_filter(libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE,
                                  event, detail, dom.UUIDString())

    def _my_domain_event_reboot_callback(self, conn, dom, opaque):
        self.evf.vir_event_filter(libvirt.VIR_DOMAIN_EVENT_ID_REBOOT,
                                  -1, -1, dom.UUIDString())

    def _my_domain_event_rtc_change_callback(self, conn, dom, utcoffset,
                                             opaque):
        self.evf.vir_event_filter(libvirt.VIR_DOMAIN_EVENT_ID_RTC_CHANGE,
                                  -1, -1, dom.UUIDString())

    def _my_domain_event_watchdog_callback(self, conn, dom, action, opaque):
        self.evf.vir_event_filter(libvirt.VIR_DOMAIN_EVENT_ID_WATCHDOG,
                                  action, -1, dom.UUIDString())

    def _my_domain_event_io_error_callback(self, conn, dom, srcpath,
                                           devalias, action, opaque):
        self.evf.vir_event_filter(libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR,
                                  action, -1, dom.UUIDString())

    def _my_domain_event_graphics_callback(self, conn, dom, phase, localAddr,
                                           remoteAddr, authScheme, subject,
                                           opaque):
        self.evf.vir_event_filter(libvirt.VIR_DOMAIN_EVENT_ID_GRAPHICS,
                                  -1, phase, dom.UUIDString())

    def _my_domain_event_disk_change_callback(self, conn, dom, oldSrcPath,
                                              newSrcPath, devAlias, reason,
                                              opaque):
        self.evf.vir_event_filter(libvirt.VIR_DOMAIN_EVENT_ID_DISK_CHANGE,
                                  -1, -1, dom.UUIDString())

    def _my_domain_event_io_error_reason_callback(self, conn, dom, srcPath,
                                                  devAlias, action, reason,
                                                  opaque):
        self.evf.vir_event_filter(libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR_REASON,
                                  -1, -1, dom.UUIDString())

    def _my_domain_event_generic_callback(self, conn, dom, opaque):
        self.evf.vir_event_filter(libvirt.VIR_DOMAIN_EVENT_ID_CONTROL_ERROR,
                                  -1, -1, dom.UUIDString())

    async def watchdog_loop(self):
        while True:
            try:
                await self.on_watchdog_timer()
            except libvirt.libvirtError as e:
                print('got on_watchdog_timer exception: ',e)
            except Exception as e:
                print('got on_watchdog_timer exception: ',e)
            await asyncio.sleep(self.watchdog_timeout)

    async def on_watchdog_timer(self):
        """connection watchdog timer within main asyncio loop
        """
        #~ print("on_watchdog_timer",self.name)
        if not self.vc or self.vc.isAlive() != 1:
            #connect/reconnect

            if self.vc:
                #cleanup previous connection
                for cid in self.callback_ids:
                    try:
                        self.vc.domainEventDeregisterAny(cid)
                    except Exception:
                        pass
                self.vc.close()
                del self.vc

            self.vc = libvirt.openReadOnly(self.uri)

            self.data.update_hv_info(self.id_, self.vc)

            for event, callback in self.event_callback_handlers.items():
                cid = self.vc.domainEventRegisterAny(None, event, callback, None)
                self.callback_ids.append(cid)

            # Connection monitoring.
            self.vc.setKeepAlive(5, 3)
        else:
            # ~ print('all is ok')
            pass
