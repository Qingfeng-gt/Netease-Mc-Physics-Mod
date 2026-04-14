# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
# Embedded file name: ValkyrienBE/framework/EventBus.py
"""
同端事件总线
用于同一端（服务端或客户端）内不同 Manager 之间的解耦通信。
注意：跨端通信请使用 NotifyToServer / NotifyToClient。
"""
import logging

class EventBus(object):
    """事件总线，支持优先级排序的发布-订阅模式"""

    def __init__(self):
        self._subscribers = {}
        return

    def subscribe(self, event_name, callback, priority=0):
        """
        订阅事件
        @param event_name: 事件名称
        @param callback: 回调函数
        @param priority: 优先级（数字越大越先执行）
        """
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append((priority, callback))
        self._subscribers[event_name].sort(key=(lambda x: -x[0]))
        return

    def unsubscribe(self, event_name, callback):
        """
        取消订阅事件
        @param event_name: 事件名称
        @param callback: 回调函数
        """
        if event_name not in self._subscribers:
            return
        self._subscribers[event_name] = [(p, cb) for p, cb in self._subscribers[event_name] if cb != callback]
        if not self._subscribers[event_name]:
            del self._subscribers[event_name]
        return

    def publish(self, event_name, *args, **kwargs):
        """
        发布事件，按优先级顺序调用所有订阅者
        @param event_name: 事件名称
        """
        if event_name not in self._subscribers:
            return
        for priority, callback in self._subscribers[event_name]:
            try:
                callback(*args, **kwargs)
            except Exception as ex:
                logging.error(('EventBus: 事件 {} 的回调 {} 执行出错: {}').format(event_name, getattr(callback, '__name__', str(callback)), str(ex)))

        return

    def clear(self):
        """清空所有订阅"""
        self._subscribers.clear()
        return

