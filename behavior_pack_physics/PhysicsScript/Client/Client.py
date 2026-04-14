from ..Core.Client.EventHandler.ClientEventHandler import  AutoRegisterClient
from ..Core.Client.ModClientBase import ModClientBase

@AutoRegisterClient("physics_client")
class Client(ModClientBase):
    def __init__(self, namespace, systemName):
        super(Client, self).__init__(namespace, systemName)