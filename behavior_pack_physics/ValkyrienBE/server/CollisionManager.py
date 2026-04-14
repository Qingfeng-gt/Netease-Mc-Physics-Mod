# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
# Embedded file name: ValkyrienBE/server/CollisionManager.py
"""
碰撞管理器
负责：物理碰撞事件监听与玩家推动物理方块的力学计算
"""
import math, mod.server.extraServerApi as serverApi
from ValkyrienBE.common.constants import PLAYER_MASS, MIN_PUSH, MASS_NORMALIZE
CF = serverApi.GetEngineCompFactory()
PxForceMode = serverApi.GetMinecraftEnum().PxForceMode

class CollisionManager(object):
    """碰撞管理器"""

    def __init__(self, system, store):
        """
        @param system: ValkyrienBEServerSystem 实例
        @param store: PhysicsEntityStore 实例
        """
        self._system = system
        self._store = store
        return

    def on_physx_touch(self, args):
        """
        物理碰撞事件处理 (PhysxTouchServerEvent)
        found 时记录接触对和法线, lost 时移除
        """
        if not self._system._can_push_physic_block:
            return
        else:
            found_list = args.get('found', [])
            for contact in found_list:
                entity_id0 = contact.get('entityId0')
                entity_id1 = contact.get('entityId1')
                identifier0 = contact.get('identifier0', '')
                identifier1 = contact.get('identifier1', '')
                normal = contact.get('normal')
                player_id = None
                block_entity_id = None
                push_normal = None
                if identifier0 == 'minecraft:player' and self._store.has_entity(entity_id1):
                    player_id = entity_id0
                    block_entity_id = entity_id1
                    if normal:
                        push_normal = (
                         -normal[0], -normal[1], -normal[2])
                elif identifier1 == 'minecraft:player' and self._store.has_entity(entity_id0):
                    player_id = entity_id1
                    block_entity_id = entity_id0
                    if normal:
                        push_normal = (
                         normal[0], normal[1], normal[2])
                if player_id and block_entity_id and push_normal:
                    self._store.set_contact(player_id, block_entity_id, push_normal)

            lost_list = args.get('lost', [])
            for contact in lost_list:
                entity_id0 = contact.get('entityId0')
                entity_id1 = contact.get('entityId1')
                identifier0 = contact.get('identifier0', '')
                identifier1 = contact.get('identifier1', '')
                player_id = None
                block_entity_id = None
                if identifier0 == 'minecraft:player' and self._store.has_entity(entity_id1):
                    player_id = entity_id0
                    block_entity_id = entity_id1
                elif identifier1 == 'minecraft:player' and self._store.has_entity(entity_id0):
                    player_id = entity_id1
                    block_entity_id = entity_id0
                if player_id and block_entity_id:
                    self._store.remove_contact(player_id, block_entity_id)

            return

    def update(self):
        """每帧对持续接触的玩家-方块对施加推力"""
        contacts = self._store.get_all_contacts()
        if not contacts:
            return
        else:
            remove_list = []
            for player_id, block_entity_id in list(contacts.keys()):
                if not self._store.has_entity(block_entity_id):
                    remove_list.append((player_id, block_entity_id))
                    continue
                if self._store.is_entity_caught(block_entity_id):
                    continue
                push_normal = contacts[(player_id, block_entity_id)]
                nx, ny, nz = push_normal
                motion_comp = CF.CreateActorMotion(player_id)
                motion = motion_comp.GetMotion()
                if motion:
                    pvx = motion[0] * 20.0
                    pvy = motion[1] * 20.0
                    pvz = motion[2] * 20.0
                else:
                    pvx = pvy = pvz = 0.0
                player_speed = math.sqrt(pvx * pvx + pvy * pvy + pvz * pvz)
                entity_data = self._store.get_entity(block_entity_id)
                entity_mass = entity_data.total_mass
                transfer_speed = player_speed * PLAYER_MASS
                force_mag = max(transfer_speed, MIN_PUSH) * (MASS_NORMALIZE - entity_mass)
                if player_speed > 0.5:
                    dot_prod = pvx * nx + pvy * ny + pvz * nz - player_speed
                    dot_prod = max(dot_prod, 0.0)
                    force_mag *= 0.3 + 0.7 * dot_prod
                phys_comp = CF.CreatePhysx(block_entity_id)
                phys_comp.AddForce((
                 nx * force_mag, ny * force_mag, nz * force_mag), PxForceMode.eVELOCITY_CHANGE)

            for key in remove_list:
                contacts.pop(key, None)

            return


