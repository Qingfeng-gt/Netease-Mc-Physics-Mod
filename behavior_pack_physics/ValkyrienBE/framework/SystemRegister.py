# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
# Embedded file name: ValkyrienBE/framework/SystemRegister.py
import uuid, mod.client.extraClientApi as clientApi, mod.server.extraServerApi as serverApi

def __get_clazz_info(clazz):
    if 'func_dict' not in clazz.__dict__:
        raise Exception('未标注@SystemHandler')
    func_dict = clazz.func_dict
    modName = func_dict['modName']
    systemName = func_dict['systemName']
    clazzPath = func_dict['path']
    random = func_dict['random']
    if random:
        modName = uuid.uuid4().hex
        systemName = uuid.uuid4().hex
    return (
     modName, systemName, clazzPath)


def register_client(clazz):
    a = __get_clazz_info(clazz)
    print a
    clientApi.RegisterSystem(*a)
    return


def register_server(clazz):
    a = __get_clazz_info(clazz)
    print a
    serverApi.RegisterSystem(*a)
    return


