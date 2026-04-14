# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
# Embedded file name: ValkyrienBE/server/PlayerManager.py
"""
玩家管理器
负责：玩家加入/离开时的数据同步与清理
"""
import mod.server.extraServerApi as serverApi
from ValkyrienBE.common import events
CF = serverApi.GetEngineCompFactory()
LID = serverApi.GetLevelId()

class PlayerManager(object):
    """玩家管理器"""

    def __init__(self, system, store):
        """
        @param system: ValkyrienBEServerSystem 实例
        @param store: PhysicsEntityStore 实例
        """
        self._system = system
        self._store = store
        return

    def on_player_join(self, args):
        """
        玩家加入游戏 (AddServerPlayerEvent)
        渲染数据由客户端 OnLocalPlayerStopLoading 主动拉取，此处不再推送
        """
        return

    def on_player_leave(self, args):
        """
        玩家离开时清理其交互状态 (DelServerPlayerEvent)
        """
        player_id = args.get('id')
        if not player_id:
            return
        catch_state = self._store.get_caught(player_id)
        if catch_state:
            entity_id = catch_state.entity_id
            try:
                from ValkyrienBE.common.constants import PHYS_ENTITY_TYPE
                phys_comp = CF.CreatePhysx(entity_id)
                PxRigidBodyFlag = serverApi.GetMinecraftEnum().PxRigidBodyFlag
                phys_comp.SetRigidBodyFlag(PxRigidBodyFlag.eKINEMATIC, False)
            except:
                pass

        fb = self._store.get_fallback_block(player_id)
        if fb:
            block_info = CF.CreateBlockInfo(LID)
            fb_pos = fb['fallback_pos']
            block_info.SetBlockNew(fb_pos, {'name': 'minecraft:bedrock', 'aux': 0}, 0, fb['dim_id'], True)
            block_info.SetBlockNew((
             fb_pos[0], -63, fb_pos[2]), {'name': 'minecraft:bedrock', 'aux': 0}, 0, fb['dim_id'], True)
        self._store.clear_player(player_id)
        return

    def request_init_phys_blocks(self, args):
        """
        客户端主动请求初始化物理方块渲染数据 (C2S_INIT_PHYS_BLOCKS)
        一次性批量同步附近实体
        """
        pid = args.get('pid')
        entityIdList = args.get('entityIdList', [])
        if not pid:
            return
        block_list = []
        for entity_id in entityIdList:
            entity_data = self._store.get_entity(entity_id)
            if entity_data:
                block_list.append(entity_data.to_render_dict(entity_id))

        if block_list:
            self._system.NotifyToClient(pid, events.S2C_RENDER_BLOCK_BATCH, {'blocks': block_list})
        return

    def request_entity_render(self, args):
        """
        客户端请求单个物理实体渲染数据 (C2S_REQUEST_ENTITY_RENDER)
        当客户端 AddEntityClientEvent 发现物理实体无本地缓存时调用
        """
        pid = args.get('pid')
        entity_id = args.get('entityId')
        if not pid or not entity_id:
            return
        entity_data = self._store.get_entity(entity_id)
        if entity_data:
            render_data = entity_data.to_render_dict(entity_id)
            self._system.NotifyToClient(pid, events.S2C_RENDER_BLOCK, render_data)
        return

    def on_server_chat(self, args):
        """
        聊天消息处理 (ServerChatEvent)
        当玩家发送 '按钮重置' 时，通知客户端重置可拖动按钮位置
        """
        message = args.get('message', '')
        player_id = args.get('playerId')
        if message in ('按钮重置', '重置按钮', '按键重置', '重置按键'):
            args['cancel'] = True
            if player_id:
                self._system.NotifyToClient(player_id, events.S2C_RESET_BUTTONS, {})
                CF.CreateMsg(player_id).NotifyOneMessage(player_id, '已重置按钮位置')
        return

