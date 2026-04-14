from ..Core.Server.EventHandler.ServerEventHandler import AutoRegisterServer
from ..Core.Server.ModServerBase import ModServerBase

@AutoRegisterServer("physics_server")
class Server(ModServerBase):
    def __init__(self, namespace, systemName):
        super(Server, self).__init__(namespace, systemName)

    