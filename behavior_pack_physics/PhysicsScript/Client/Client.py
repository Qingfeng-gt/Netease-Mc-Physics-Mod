from ..Core.Client.EventHandler.ClientEventHandler import  AutoRegisterClient
from ..Core.Client.Lib.ClientLib import QfClientApi
from ..Core.Client.ModClientBase import ModClientBase


@AutoRegisterClient("physics_client")
class Client(ModClientBase):
    def __init__(self, namespace, systemName):
        super(Client, self).__init__(namespace, systemName)

    def OnUiInitFinished(self, args):
        super(Client, self).OnUiInitFinished(args)

