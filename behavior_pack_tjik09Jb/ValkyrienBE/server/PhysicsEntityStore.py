# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
# Embedded file name: ValkyrienBE/server/PhysicsEntityStore.py
"""
物理实体共享数据存储
所有服务端 Manager 共用此 Store 实例，提供统一的数据访问接口。
"""
from ValkyrienBE.common.data_models import PhysicsEntityData, CatchState
from ValkyrienBE.common.constants import SHIPYARD_BASE_X, SHIPYARD_BASE_Z, SHIPYARD_Y, SHIPYARD_SLOT_SIZE, SHIPYARD_GRID_WIDTH

class PhysicsEntityStore(object):
    """物理实体数据中心"""

    def __init__(self):
        self._entities = {}
        self._caught_entities = {}
        self._sucking_players = set()
        self._spraying_players = set()
        self._active_contacts = {}
        self._suck_entity_prev_pos = {}
        self._concrete_palettes = {}
        self._spray_entity_ids = set()
        self._pending_entities = []
        self._shipyard_counter = 0
        self._shipyard_slots = {}
        self._shipyard_free_slots = []
        self._fallback_blocks = {}
        return

    def add_entity(self, entity_id, data):
        """
        添加物理实体数据
        @param entity_id: str
        @param data: PhysicsEntityData
        """
        self._entities[entity_id] = data
        return

    def remove_entity(self, entity_id):
        """
        移除物理实体数据
        @param entity_id: str
        @return: PhysicsEntityData | None
        """
        self._suck_entity_prev_pos.pop(entity_id, None)
        self._spray_entity_ids.discard(entity_id)
        return self._entities.pop(entity_id, None)

    def get_entity(self, entity_id):
        """
        获取物理实体数据
        @return: PhysicsEntityData | None
        """
        return self._entities.get(entity_id)

    def has_entity(self, entity_id):
        """实体是否存在"""
        return entity_id in self._entities

    def get_all_entities(self):
        """获取所有物理实体 {entityId: PhysicsEntityData}"""
        return self._entities

    def get_entity_count(self):
        """获取物理实体数量"""
        return len(self._entities)

    def set_caught(self, player_id, catch_state):
        """
        设置玩家捉捕状态
        @param player_id: str
        @param catch_state: CatchState
        """
        self._caught_entities[player_id] = catch_state
        return

    def get_caught(self, player_id):
        """
        获取玩家捉捕状态
        @return: CatchState | None
        """
        return self._caught_entities.get(player_id)

    def remove_caught(self, player_id):
        """移除玩家捉捕状态"""
        return self._caught_entities.pop(player_id, None)

    def has_caught(self, player_id):
        """玩家是否在捉捕"""
        return player_id in self._caught_entities

    def get_all_caught(self):
        """获取所有捉捕状态"""
        return self._caught_entities

    def is_entity_caught(self, entity_id):
        """检查实体是否被任何玩家捉捕"""
        for catch_state in self._caught_entities.values():
            if catch_state.entity_id == entity_id:
                return True

        return False

    def get_catcher_of(self, entity_id):
        """获取捉捕指定实体的玩家ID"""
        for pid, catch_state in self._caught_entities.items():
            if catch_state.entity_id == entity_id:
                return pid

        return

    def add_sucking(self, player_id):
        self._sucking_players.add(player_id)
        return

    def remove_sucking(self, player_id):
        self._sucking_players.discard(player_id)
        return

    def get_sucking_players(self):
        return self._sucking_players

    def add_spraying(self, player_id):
        self._spraying_players.add(player_id)
        return

    def remove_spraying(self, player_id):
        self._spraying_players.discard(player_id)
        return

    def get_spraying_players(self):
        return self._spraying_players

    def set_contact(self, player_id, block_entity_id, normal):
        self._active_contacts[(player_id, block_entity_id)] = normal
        return

    def remove_contact(self, player_id, block_entity_id):
        self._active_contacts.pop((player_id, block_entity_id), None)
        return

    def get_all_contacts(self):
        return self._active_contacts

    def allocate_shipyard_slot(self, entity_id):
        """
        为实体分配一个 Shipyard 远端存储槽位
        @param entity_id: str 实体ID
        @return: (slot_index, (x, y, z))  槽位索引 及 远端放置原点坐标
        """
        if self._shipyard_free_slots:
            slot = self._shipyard_free_slots.pop()
        else:
            slot = self._shipyard_counter
            self._shipyard_counter += 1
        self._shipyard_slots[slot] = entity_id
        x = SHIPYARD_BASE_X + slot % SHIPYARD_GRID_WIDTH * SHIPYARD_SLOT_SIZE
        z = SHIPYARD_BASE_Z + slot // SHIPYARD_GRID_WIDTH * SHIPYARD_SLOT_SIZE
        y = SHIPYARD_Y
        return (slot, (x, y, z))

    def release_shipyard_slot(self, slot_index):
        """
        释放 Shipyard 槽位
        @param slot_index: int
        """
        self._shipyard_slots.pop(slot_index, None)
        if slot_index not in self._shipyard_free_slots:
            self._shipyard_free_slots.append(slot_index)
        return

    def get_shipyard_slot_pos(self, slot_index):
        """
        根据槽位索引计算远端坐标
        @return: (x, y, z)
        """
        x = SHIPYARD_BASE_X + slot_index % SHIPYARD_GRID_WIDTH * SHIPYARD_SLOT_SIZE
        z = SHIPYARD_BASE_Z + slot_index // SHIPYARD_GRID_WIDTH * SHIPYARD_SLOT_SIZE
        return (x, SHIPYARD_Y, z)

    def clear_all(self):
        """清空所有状态"""
        self._entities.clear()
        self._caught_entities.clear()
        self._sucking_players.clear()
        self._spraying_players.clear()
        self._active_contacts.clear()
        self._suck_entity_prev_pos.clear()
        self._concrete_palettes.clear()
        self._spray_entity_ids.clear()
        self._pending_entities = []
        self._shipyard_counter = 0
        self._shipyard_slots.clear()
        self._shipyard_free_slots = []
        self._fallback_blocks.clear()
        return

    def clear_player(self, player_id):
        """清理指定玩家的所有状态"""
        self._sucking_players.discard(player_id)
        self._spraying_players.discard(player_id)
        self._caught_entities.pop(player_id, None)
        self._fallback_blocks.pop(player_id, None)
        keys_to_remove = [k for k in self._active_contacts if k[0] == player_id]
        for k in keys_to_remove:
            del self._active_contacts[k]

        return

    def add_fallback_block(self, pid, info):
        """添加玩家的备用放置方块跟踪"""
        self._fallback_blocks[pid] = info
        return

    def get_fallback_block(self, pid):
        """获取玩家的备用放置方块信息"""
        return self._fallback_blocks.get(pid)

    def remove_fallback_block(self, pid):
        """移除玩家的备用放置方块"""
        return self._fallback_blocks.pop(pid, None)

    def get_all_fallback_blocks(self):
        """获取所有备用放置方块"""
        return self._fallback_blocks

    def enqueue_pending_entity(self, aabb_list, region_size=None, render_offset=None, collider_strategy=None):
        self._pending_entities.append({'aabbList': aabb_list, 
           'regionSize': region_size, 
           'renderOffset': render_offset, 
           'colliderStrategy': collider_strategy})
        return

    def pop_pending_entity(self):
        if not self._pending_entities:
            return None
        else:
            return self._pending_entities.pop(0)

