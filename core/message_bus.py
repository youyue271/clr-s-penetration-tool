# core/message_bus.py
import queue
import threading
import json
from datetime import datetime


class MessageBus:
    def __init__(self):
        self._channels = {}
        self._lock = threading.RLock()
        self._message_counter = 0
        self._setup_default_channels()
        # self._channel_caller = {}
        # self._channels_callee = {}

    def _setup_default_channels(self):
        # self.create_channel("scan_results", maxsize=1000)
        # self.create_channel("vuln_alerts", priority=True)
        # self.create_channel("llm_commands", persistent=True)
        self.create_channel("scan_target")
        self.create_channel("module_errors")
        self.create_channel("system_errors")

    def create_channel(self, name, maxsize=100, priority=False, persistent=False):
        with self._lock:
            if name not in self._channels:
                if priority:
                    self._channels[name] = PriorityChannel(maxsize, persistent)
                else:
                    self._channels[name] = Channel(maxsize, persistent)

    def publish(self, channel, message, priority=0):
        with self._lock:
            if channel not in self._channels:
                raise ValueError(f"Channel {channel} not exists")

            msg_obj = {
                "id": self._message_counter,
                "timestamp": datetime.now().isoformat(),
                "priority": priority,
                "data": message
            }
            self._channels[channel].put(msg_obj)
            self._message_counter += 1

    def subscribe(self, channel, timeout=5):
        with self._lock:
            if channel not in self._channels:
                self.create_channel(channel)

            try:
                return self._channels[channel].get(timeout=timeout)
            except queue.Empty:
                return None

    def get_module_input(self, module_name):
        """智能消息路由"""
        input_rules = {
            "port_scanner": ["targets", "scan_config"],
            "vuln_scanner": ["scan_results"],
            "llm_advisor": ["vuln_alerts", "scan_results"]
        }

        inputs = []
        for data_type in input_rules.get(module_name, []):
            while True:
                msg = self.subscribe(data_type)
                if msg:
                    inputs.append(msg['data'])
                else:
                    break
        return inputs


class Channel:
    def __init__(self, maxsize, persistent):
        self.queue = queue.Queue(maxsize=maxsize)
        self.persistent = persistent
        self._storage = [] if persistent else None

    def put(self, item):
        if self.persistent:
            self._storage.append(item)
        self.queue.put(item)

    def get(self, timeout=None):
        try:
            return self.queue.get(timeout=timeout)
        except queue.Empty:
            return None


class PriorityChannel(Channel):
    def __init__(self, maxsize, persistent):
        super().__init__(maxsize, persistent)
        self.queue = queue.PriorityQueue(maxsize=maxsize)

    def put(self, item):
        priority = item.get('priority', 0)
        super().put((-priority, item))  # 使用负数实现降序排列