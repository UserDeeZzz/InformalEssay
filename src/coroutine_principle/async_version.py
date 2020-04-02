#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@author: deez
@file: async_version.py
@time: 2020/3/27
"""

import socket
from selectors import DefaultSelector, EVENT_READ, EVENT_WRITE

selector = DefaultSelector()
# await语法的出现主要是区别生成器和协程的概念 不能都用yield混淆在一起

class Future:
    def __init__(self):
        self.callback = None
    # 原来是yield future 现在是await调用__await__返回yield self
    def __await__(self):
        yield self

class Task:
    def __init__(self, cor):
        self.cor = cor
        self.step()

    def step(self):
        try:
            f = self.cor.send(None)
        except StopIteration:
            return
        f.callback = self.step


async def gen(path):
    s = socket.socket()
    s.setblocking(False)
    try:
        s.connect(('192.168.160.100', 7777))
    except BlockingIOError:
        pass
    f = Future()
    selector.register(s.fileno(), EVENT_WRITE, f)
    await f
    selector.unregister(s.fileno())
    s.send(('GET %s HTTP/1.0\r\n\r\n' % path).encode())
    res = []
    while 1:
        f = Future()
        selector.register(s.fileno(), EVENT_READ, f)
        await f
        selector.unregister(s.fileno())
        chunk = s.recv(1024)
        if chunk:
            res.append(chunk)
        else:
            break
    print(b''.join(res).decode())


Task(gen(''))
Task(gen(''))
Task(gen(''))
Task(gen(''))


while 1:
    events = selector.select()
    for key, mask in events:
        future = key.data
        future.callback()

# 基于回调+生成器+事件监听
# socket描述符监听事件--->yield挂起--->事件发生--->调用future的callback
# future的callback在task示例化时为Task的step--->调用coroutine继续运行
# future的回调是task，task是向生成器send，生成器send会创建新的future