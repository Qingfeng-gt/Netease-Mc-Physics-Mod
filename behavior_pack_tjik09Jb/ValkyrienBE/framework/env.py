# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
# Embedded file name: ValkyrienBE/framework/env.py
"""
运行环境检测模块
env_type 由 wrapper.py 的 SystemHandler 在系统初始化时自动设置
"""
env_type = ''

def is_server():
    """当前是否运行在服务端"""
    return env_type == 'server'


def is_client():
    """当前是否运行在客户端"""
    return env_type == 'client'


