# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
# Embedded file name: ValkyrienBE/modMain.py
from mod.common.mod import Mod
from ValkyrienBE.framework.SystemRegister import register_server, register_client
from ValkyrienBE.modConfig import ModName, ModVersion

@Mod.Binding(name=ModName, version=ModVersion)
class ValkyrienBE(object):

    def __init__(self):
        return

    @Mod.InitServer()
    def ValkyrienBEServerInit(self):
        from ValkyrienBE.ValkyrienBEServerSystem import ValkyrienBEServerSystem
        register_server(ValkyrienBEServerSystem)
        return

    @Mod.DestroyServer()
    def ValkyrienBEServerDestroy(self):
        return

    @Mod.InitClient()
    def ValkyrienBEClientInit(self):
        from ValkyrienBE.ValkyrienBEClientSystem import ValkyrienBEClientSystem
        register_client(ValkyrienBEClientSystem)
        return

    @Mod.DestroyClient()
    def ValkyrienBEClientDestroy(self):
        return


