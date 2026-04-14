# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
# Embedded file name: ValkyrienBE/server/PhysicsEntityManager.py
"""
物理实体生命周期管理
负责：创建/销毁物理实体、AABB 解析、调色板管理、持久化与恢复
Shipyard 远处存储架构：方块真实存放于远处 (X=100000)，通过 structure 指令搬运
"""
import math, time, mod.server.extraServerApi as serverApi
from mod.common.utils.mcmath import Quaternion, Vector3
from ValkyrienBE.common.constants import PHYS_ENTITY_TYPE, MAX_REGION_BLOCKS, DEFAULT_COLLIDER_STRATEGY, SHIPYARD_BASE_X, SHIPYARD_BASE_Z, SHIPYARD_Y, SHIPYARD_SLOT_SIZE, SHIPYARD_GRID_WIDTH, SHIPYARD_PADDING, SHIPYARD_STRUCT_PREFIX, PHYS_HOME_SIZE, PHYS_HOME_STRUCTURE, BALLOON_BLOCK_NAME, ENTITY_GRAVITY, BALLOON_MASS_PER_BLOCK, BALLOON_HEIGHT_DECAY_ENABLED, BALLOON_MIN_HEIGHT, BALLOON_MAX_HEIGHT, MASS_NORMALIZE, UNSUPPORTED_PHYSICAL_BLOCKS
from ValkyrienBE.common.data_models import PhysicsEntityData
from ValkyrienBE.common import events
from ValkyrienBE.common.block_mass import get_block_mass_info, DEFAULT_BLOCK_FRICTION, DEFAULT_BLOCK_ELASTICITY
from ValkyrienBE.util import *
CF = serverApi.GetEngineCompFactory()
LID = serverApi.GetLevelId()
PxEventMask = serverApi.GetMinecraftEnum().PxEventMask
PxRigidBodyFlag = serverApi.GetMinecraftEnum().PxRigidBodyFlag
PxForceMode = serverApi.GetMinecraftEnum().PxForceMode
_EVENT_MASK = PxEventMask.Server | PxEventMask.Found_Detail | PxEventMask.Lost | PxEventMask.Found
PRELOAD_POOL_SIZE = 20
PRELOAD_DIMENSION = 0

class PhysicsEntityManager(object):
    """物理实体管理器"""

    def __init__(self, system, store):
        """
        @param system: ValkyrienBEServerSystem 实例
        @param store: PhysicsEntityStore 实例
        """
        self._system = system
        self._store = store
        self._preloaded_pool = []
        self._preloading_count = 0
        self._pool_ready = False
        self._init_delay_ticks = -1
        self._slot_tick_entities = {}
        self._balloon_ready_set = set()
        self._refresh_timers = {}
        return

    def update(self):
        """每 tick 调用（由 ValkyrienBEServerSystem.Update 驱动），处理延迟初始化、备用方块同步和周期刷新"""
        if self._init_delay_ticks > 0:
            self._init_delay_ticks -= 1
        elif self._init_delay_ticks == 0:
            self._init_delay_ticks = -1
            self.init_preload_pool()
        self._update_fallback_blocks()
        self._update_balloon_forces()
        return

    def is_pool_ready(self):
        """预加载池是否已就绪（所有槽位区块加载完毕、基岩盒子放置完毕）"""
        return self._pool_ready

    def init_preload_pool(self):
        """
        初始化预加载池。
        预分配 Shipyard 槽位并异步加载区块、放置基岩盒子，
        使后续物理化操作可以直接使用已就绪的槽位。
        """
        self._pool_ready = False
        print ('[ValkyrienBE] Initializing preload pool, target: {}').format(PRELOAD_POOL_SIZE)
        self._replenish_pool()
        return

    def _replenish_pool(self):
        """补充预加载池，确保 pool + loading 达到 PRELOAD_POOL_SIZE"""
        needed = PRELOAD_POOL_SIZE - len(self._preloaded_pool) - self._preloading_count
        for _ in range(needed):
            self._preload_single_slot()

        return

    def _kill_slot_tick_entity(self, slot_index):
        """销毁指定槽位的区块加载 tick 实体"""
        tick_eid = self._slot_tick_entities.pop(slot_index, None)
        if tick_eid:
            self._system.DestroyEntity(tick_eid)
        return

    def _preload_single_slot(self):
        """分配一个槽位并异步加载区块 + 放置基岩盒子"""
        slot_index, slot_pos = self._store.allocate_shipyard_slot('__preloading__')
        sp_x, sp_y, sp_z = slot_pos
        area_key = ('vbe_area_{}').format(slot_index)
        self._preloading_count += 1
        slot_info = {'slot_index': slot_index, 
           'slot_pos': (
                      sp_x, sp_y, sp_z), 
           'area_key': area_key, 
           'dimension_id': PRELOAD_DIMENSION}
        chunk_comp = CF.CreateChunkSource(LID)
        callback = lambda data, _si=slot_info: self._on_preload_chunks_loaded(data, _si)
        chunk_comp.DoTaskOnChunkAsync(PRELOAD_DIMENSION, (
         sp_x, 0, sp_z), (
         sp_x + PHYS_HOME_SIZE, 0, sp_z + PHYS_HOME_SIZE), callback)
        return

    def _on_preload_chunks_loaded(self, data, slot_info):
        """预加载区块加载完成回调：设置常加载区域 + 放置基岩盒子"""
        self._preloading_count -= 1
        slot_index = slot_info['slot_index']
        current_owner = self._store._shipyard_slots.get(slot_index)
        if current_owner is not None and current_owner != '__preloading__':
            print ('[ValkyrienBE] Preload slot {} already occupied by entity, skipping').format(slot_index)
            self._replenish_pool()
            return
        else:
            if data.get('code') != 1:
                print ('[ValkyrienBE] preload slot {} chunk loading failed').format(slot_index)
                self._store.release_shipyard_slot(slot_index)
                self._replenish_pool()
                return
            sp_x, sp_y, sp_z = slot_info['slot_pos']
            area_key = slot_info['area_key']
            dim_id = slot_info['dimension_id']
            chunk_comp = CF.CreateChunkSource(LID)
            game_comp = CF.CreateGame(LID)
            chunk_comp.SetAddArea(area_key, dim_id, (
             sp_x - SHIPYARD_PADDING, 0, sp_z - SHIPYARD_PADDING), (
             sp_x + SHIPYARD_PADDING, 0, sp_z + SHIPYARD_PADDING))
            tick_eid = self._system.CreateEngineEntityByTypeStr('physstimu:xiaobo_phys_tick', (sp_x, -60, sp_z), (0,
                                                                                                                  0), dim_id)
            if tick_eid:
                self._slot_tick_entities[slot_index] = tick_eid
            game_comp.PlaceStructure(None, (sp_x, sp_y, sp_z), PHYS_HOME_STRUCTURE, dim_id, 0, animationMode=0, animationTime=0, inculdeEntity=False, removeBlock=False, mirrorMode=0, integrity=100, seed=-1)
            self._preloaded_pool.append(slot_info)
            print ('[ValkyrienBE] Preloaded slot {} ready (pool: {}/{})').format(slot_index, len(self._preloaded_pool), PRELOAD_POOL_SIZE)
            self._save_pool_to_world()
            if not self._pool_ready and len(self._preloaded_pool) >= PRELOAD_POOL_SIZE:
                self._pool_ready = True
                print ('[ValkyrienBE] Preload pool fully ready! ({}/{})').format(len(self._preloaded_pool), PRELOAD_POOL_SIZE)
            return

    def _pop_preloaded_slot(self, dimension_id):
        """
        从预加载池中取出一个匹配维度的就绪槽位。
        取出后自动触发补充。
        @return: slot_info dict 或 None
        """
        for i, slot in enumerate(self._preloaded_pool):
            if slot['dimension_id'] == dimension_id:
                self._preloaded_pool.pop(i)
                self._save_pool_to_world()
                self._replenish_pool()
                return slot

        return

    def _cleanup_preloaded_pool(self):
        """清理所有预加载池中的槽位（释放常加载区域和槽位索引）"""
        chunk_comp = CF.CreateChunkSource(LID)
        cmd_comp = CF.CreateCommand(LID)
        for slot_info in self._preloaded_pool:
            chunk_comp.DeleteArea(slot_info['area_key'])
            sp_x, sp_y, sp_z = slot_info['slot_pos']
            cmd_comp.SetCommand(('/fill {} {} {} {} {} {} air').format(sp_x, sp_y, sp_z, sp_x + PHYS_HOME_SIZE - 1, sp_y + PHYS_HOME_SIZE - 1, sp_z + PHYS_HOME_SIZE - 1))
            self._store.release_shipyard_slot(slot_info['slot_index'])
            self._kill_slot_tick_entity(slot_info['slot_index'])

        self._preloaded_pool = []
        self._preloading_count = 0
        self._pool_ready = False
        self._save_pool_to_world()
        return

    def _save_pool_to_world(self):
        """将预加载池状态保存到世界 ExtraData，用于世界重载时快速恢复"""
        pool_data = {'pool': [{'slot_index': (s['slot_index']), 'slot_pos': (list(s['slot_pos'])), 'area_key': (s['area_key']), 'dimension_id': (s['dimension_id'])} for s in self._preloaded_pool], 
           'counter': (self._store._shipyard_counter)}
        extra_comp = CF.CreateExtraData(LID)
        extra_comp.SetExtraData('vbe_preload_pool', pool_data, True)
        return

    def _load_pool_from_world(self):
        """从世界 ExtraData 读取预加载池状态"""
        extra_comp = CF.CreateExtraData(LID)
        return extra_comp.GetExtraData('vbe_preload_pool')

    def _restore_pool_from_world(self, saved_data):
        """
        从世界 ExtraData 恢复预加载池。
        直接恢复已分配的槽位，无需等待实体加载，避免 5 秒延迟。
        """
        pool_items = saved_data.get('pool', [])
        counter = saved_data.get('counter', 0)
        if counter > self._store._shipyard_counter:
            self._store._shipyard_counter = counter
        if not pool_items:
            self._init_delay_ticks = 100
            print '[ValkyrienBE] No saved pool data, falling back to delayed init'
            return
        self._pool_ready = False
        print ('[ValkyrienBE] Restoring preload pool from world data ({} slots)').format(len(pool_items))
        for item in pool_items:
            slot_info = {'slot_index': (item['slot_index']), 
               'slot_pos': (tuple(item['slot_pos'])), 
               'area_key': (item['area_key']), 
               'dimension_id': (item['dimension_id'])}
            self._store._shipyard_slots[slot_info['slot_index']] = '__preloading__'
            self._preloading_count += 1
            sp_x, sp_y, sp_z = slot_info['slot_pos']
            chunk_comp = CF.CreateChunkSource(LID)
            callback = lambda data, _si=slot_info: self._on_restore_pool_chunks_loaded(data, _si)
            chunk_comp.DoTaskOnChunkAsync(slot_info['dimension_id'], (
             sp_x, 0, sp_z), (
             sp_x + PHYS_HOME_SIZE, 0, sp_z + PHYS_HOME_SIZE), callback)

        return

    def _on_restore_pool_chunks_loaded(self, data, slot_info):
        """世界重载时恢复预加载槽位的区块加载回调"""
        self._preloading_count -= 1
        slot_index = slot_info['slot_index']
        current_owner = self._store._shipyard_slots.get(slot_index)
        if current_owner is not None and current_owner != '__preloading__':
            print ('[ValkyrienBE] Restore: slot {} already occupied by entity, skipping').format(slot_index)
            self._replenish_pool()
            return
        else:
            if data.get('code') != 1:
                print ('[ValkyrienBE] Restore: slot {} chunk loading failed').format(slot_index)
                self._store.release_shipyard_slot(slot_index)
                self._replenish_pool()
                return
            sp_x, sp_y, sp_z = slot_info['slot_pos']
            area_key = slot_info['area_key']
            dim_id = slot_info['dimension_id']
            chunk_comp = CF.CreateChunkSource(LID)
            chunk_comp.SetAddArea(area_key, dim_id, (
             sp_x - SHIPYARD_PADDING, 0, sp_z - SHIPYARD_PADDING), (
             sp_x + SHIPYARD_PADDING, 0, sp_z + SHIPYARD_PADDING))
            tick_eid = self._system.CreateEngineEntityByTypeStr('physstimu:xiaobo_phys_tick', (sp_x, -60, sp_z), (0,
                                                                                                                  0), dim_id)
            if tick_eid:
                self._slot_tick_entities[slot_index] = tick_eid
            self._preloaded_pool.append(slot_info)
            print ('[ValkyrienBE] Restored pool slot {} (pool: {}/{})').format(slot_index, len(self._preloaded_pool), PRELOAD_POOL_SIZE)
            if not self._pool_ready and len(self._preloaded_pool) >= PRELOAD_POOL_SIZE:
                self._pool_ready = True
                print ('[ValkyrienBE] Preload pool restored and ready! ({}/{})').format(len(self._preloaded_pool), PRELOAD_POOL_SIZE)
            self._replenish_pool()
            return

    def _parse_block_aabb(self, pos, dimension_id):
        """
        获取方块碰撞 AABB
        @return: (aabbMin, aabbMax) | None
        """
        block_info_comp = CF.CreateBlockInfo(LID)
        aabb_dict = block_info_comp.GetBlockCollision(pos, dimension_id)
        if not aabb_dict:
            return None
        else:
            a_min = aabb_dict.get('min')
            a_max = aabb_dict.get('max')
            dx = abs(a_max[0] - a_min[0])
            dy = abs(a_max[1] - a_min[1])
            dz = abs(a_max[2] - a_min[2])
            if dx < 0.001 and dy < 0.001 and dz < 0.001:
                return None
            return (
             tuple(a_min), tuple(a_max))

    def _calc_box_geometry(self, a_min, a_max, entity_spawn_pos):
        """
        根据世界坐标 AABB 和实体生成位置计算 AddBoxGeometry 参数
        @return: (localCenter, halfExtents)
        """
        half_x = a_max[0] - a_min[0] - 2.0
        half_y = a_max[1] - a_min[1] - 2.0
        half_z = a_max[2] - a_min[2] - 2.0
        center_x = a_min[0] + a_max[0] - 2.0 - entity_spawn_pos[0]
        center_y = a_min[1] + a_max[1] - 2.0 - entity_spawn_pos[1]
        center_z = a_min[2] + a_max[2] - 2.0 - entity_spawn_pos[2]
        return ((center_x, center_y, center_z), (half_x, half_y, half_z))

    def _is_supported_physical_block(self, block_name):
        """方块是否支持物理化。"""
        return block_name not in UNSUPPORTED_PHYSICAL_BLOCKS

    def _find_unsupported_palette_blocks(self, palette_data):
        """返回调色板中的不支持物理化方块列表。"""
        unsupported = []
        common = palette_data.get('common', {}) if palette_data else {}
        for key in common:
            block_name = key[0] if isinstance(key, (tuple, list)) else str(key)
            if block_name in UNSUPPORTED_PHYSICAL_BLOCKS and block_name not in unsupported:
                unsupported.append(block_name)

        return unsupported

    def _cleanup_failed_shipyard_slot(self, slot_index, slot_pos, area_key, dimension_id, is_preloaded):
        """创建失败时回收 Shipyard 槽位，避免预加载池状态损坏。"""
        sp_x, sp_y, sp_z = slot_pos
        cmd_comp = CF.CreateCommand(LID)
        cmd_comp.SetCommand(('/fill {} {} {} {} {} {} air').format(sp_x, sp_y, sp_z, sp_x + PHYS_HOME_SIZE - 1, sp_y + PHYS_HOME_SIZE - 1, sp_z + PHYS_HOME_SIZE - 1))
        if is_preloaded:
            game_comp = CF.CreateGame(LID)
            game_comp.PlaceStructure(None, (sp_x, sp_y, sp_z), PHYS_HOME_STRUCTURE, dimension_id, 0, animationMode=0, animationTime=0, inculdeEntity=False, removeBlock=False, mirrorMode=0, integrity=100, seed=-1)
            self._store._shipyard_slots[slot_index] = '__preloading__'
            self._preloaded_pool.append({'slot_index': slot_index, 
               'slot_pos': (
                          sp_x, sp_y, sp_z), 
               'area_key': area_key, 
               'dimension_id': dimension_id})
            self._save_pool_to_world()
            return
        else:
            chunk_comp = CF.CreateChunkSource(LID)
            chunk_comp.DeleteArea(area_key)
            self._store.release_shipyard_slot(slot_index)
            self._kill_slot_tick_entity(slot_index)
            return

    def _notify_player_tip(self, pid, color, message):
        """向指定玩家发送 tip。"""
        if not pid:
            return
        CF.CreateGame(pid).SetOneTipMessage(pid, serverApi.GenerateColor(color) + message)
        return

    def _is_bedrock_item(self, item_dict):
        """当前手持物品是否为基岩。"""
        if not item_dict:
            return False
        item_name = item_dict.get('newItemName') or item_dict.get('itemName') or ''
        return item_name == 'minecraft:bedrock'

    def _calculate_mass_and_centroid(self, volume, common):
        """
        计算方块结构的质量加权质心 (Mass-Weighted Center of Mass)。
        同时构建索引→方块名映射表，供后续 AABB 创建时查询摩擦力。
        
        索引遍历顺序为 (0,0,0) -> (0,0,1) -> (1,0,0)...
        变化频率：Z (最快) > X (中) > Y (最慢)
        
        Args:
            volume: tuple (x_size, y_size, z_size)
            common: dict，键为 (block_name, aux) 元组，值为索引列表
            
        Returns:
            tuple ((avg_x, avg_y, avg_z), total_mass, block_name_map, balloon_count):
                - 质心坐标 (局部坐标)
                - 总质量 (kg)
                - block_name_map: dict {(local_x, local_y, local_z): block_name}
                - balloon_count: int 气球方块数量
        """
        x_len, y_len, z_len = volume
        stride_x = z_len
        stride_y = x_len * z_len
        sum_mx = 0.0
        sum_my = 0.0
        sum_mz = 0.0
        total_mass = 0.0
        sum_x = 0.0
        sum_y = 0.0
        sum_z = 0.0
        count = 0
        balloon_count = 0
        block_name_map = {}
        for block_key, block_indices in common.items():
            block_name = block_key[0] if isinstance(block_key, (tuple, list)) else str(block_key)
            mass, _, _ = get_block_mass_info(block_name)
            is_balloon = block_name == BALLOON_BLOCK_NAME
            for idx in block_indices:
                y = idx // stride_y
                rem = idx % stride_y
                x = rem // stride_x
                z = rem % stride_x
                block_name_map[(x, y, z)] = block_name
                sum_x += x
                sum_y += y
                sum_z += z
                count += 1
                if is_balloon:
                    balloon_count += 1
                if mass > 0:
                    sum_mx += mass * x
                    sum_my += mass * y
                    sum_mz += mass * z
                    total_mass += mass

        if total_mass > 0:
            avg_x = sum_mx - total_mass
            avg_y = sum_my - total_mass
            avg_z = sum_mz - total_mass
        elif count > 0:
            avg_x = sum_x - count
            avg_y = sum_y - count
            avg_z = sum_z - count
        else:
            avg_x = avg_y = avg_z = 0.0
        return ((avg_x, avg_y, avg_z), total_mass, block_name_map, balloon_count)

    def save_entity_extra_data(self, entity_id):
        """保存物理实体数据到实体 ExtraData"""
        entity_data = self._store.get_entity(entity_id)
        if not entity_data:
            return
        extra_comp = CF.CreateExtraData(entity_id)
        extra_comp.SetExtraData('phys_data', entity_data.to_save_dict(), True)
        return

    def preload_entities_from_world(self):
        """
        LoadServerAddonScriptsAfter 回调
        遍历所有维度的已加载实体，预读取物理实体的 ExtraData 到 Store。
        后续 AddEntityServerEvent 可直接使用预加载数据创建碰撞箱。
        """
        saved_pool = self._load_pool_from_world()
        if saved_pool and saved_pool.get('pool'):
            self._restore_pool_from_world(saved_pool)
        else:
            self._init_delay_ticks = 150
            print '[ValkyrienBE] Preload pool scheduled to init in 5 seconds (waiting for entity restore)'
        return

    def reload_entity_from_extra_data(self, entity_id, phys_comp):
        """兜底：从 ExtraData 恢复物理数据和碰撞盒（支持 userData）"""
        extra_comp = CF.CreateExtraData(entity_id)
        saved_data = extra_comp.GetExtraData('phys_data')
        if saved_data:
            entity_data = PhysicsEntityData.from_save_dict(saved_data)
            self._store.add_entity(entity_id, entity_data)
            self._schedule_balloon_ready(entity_id)
            for item in entity_data.aabb_list:
                if len(item) >= 6:
                    local_center, half_extents, sf, df, r, ud = item
                else:
                    local_center, half_extents, sf, df, r = item
                    ud = None
                phys_comp.AddBoxGeometry(local_center, half_extents[0], half_extents[1], half_extents[2], sf, df, r, _EVENT_MASK, userData=ud)

            if entity_data.shipyard_area_key and entity_data.shipyard_pos:
                sx, sz = entity_data.shipyard_pos[0], entity_data.shipyard_pos[2]
                chunk_comp = CF.CreateChunkSource(LID)
                chunk_comp.SetAddArea(entity_data.shipyard_area_key, entity_data.dimension_id, (
                 sx - SHIPYARD_PADDING, 0, sz - SHIPYARD_PADDING), (
                 sx + SHIPYARD_PADDING, 0, sz + SHIPYARD_PADDING))
            if entity_data.slot_index >= 0:
                self._store._shipyard_slots[entity_data.slot_index] = entity_id
                if self._store._shipyard_counter <= entity_data.slot_index:
                    self._store._shipyard_counter = entity_data.slot_index + 1
        else:
            phys_comp.AddBoxGeometry((0, 0.5, 0), 0.5, 0.5, 0.5, DEFAULT_BLOCK_FRICTION, DEFAULT_BLOCK_FRICTION, DEFAULT_BLOCK_ELASTICITY, _EVENT_MASK)
        return

    def physicalize_block(self, args):
        """
        物理化单方块（Shipyard 架构）
        优先使用预加载池中的就绪槽位（同步），否则走异步 DoTaskOnChunkAsync。
        @param args: {blockPos, pid}
        """
        block_pos = args['blockPos']
        pid = args['pid']
        if not self._pool_ready:
            CF.CreateGame(pid).SetOneTipMessage(pid, serverApi.GenerateColor('RED') + '系统正在初始化中, 请稍后再试...')
            return
        else:
            bx, by, bz = block_pos
            dimension_id = CF.CreateDimension(pid).GetEntityDimensionId()
            block_dict = CF.CreateBlockInfo(LID).GetBlockNew((bx, by, bz), dimension_id)
            block_name = block_dict['name']
            if not self._is_supported_physical_block(block_name):
                CF.CreateGame(pid).SetOneTipMessage(pid, serverApi.GenerateColor('RED') + '该方块暂不支持物理化')
                return
            aabb = self._parse_block_aabb((bx, by, bz), dimension_id)
            if aabb is None:
                CF.CreateGame(pid).SetOneTipMessage(pid, serverApi.GenerateColor('RED') + '该方块无碰撞箱, 无法物理化')
                return
            preloaded = self._pop_preloaded_slot(dimension_id)
            if preloaded:
                slot_index = preloaded['slot_index']
                sp_x, sp_y, sp_z = preloaded['slot_pos']
                area_key = preloaded['area_key']
            else:
                slot_index, slot_pos = self._store.allocate_shipyard_slot('')
                sp_x, sp_y, sp_z = slot_pos
                area_key = ('vbe_area_{}').format(slot_index)
            struct_name = ('{}:ship_{}').format(SHIPYARD_STRUCT_PREFIX, slot_index)
            cmd_comp = CF.CreateCommand(LID)
            cmd_comp.SetCommand(('/structure save {} {} {} {} {} {} {} memory').format(struct_name, bx, by, bz, bx, by, bz))
            shipyard_pos = (
             sp_x + PHYS_HOME_SIZE // 2,
             sp_y + PHYS_HOME_SIZE // 2,
             sp_z + PHYS_HOME_SIZE // 2)
            timer_args = {'sp_x': sp_x, 
               'sp_y': sp_y, 'sp_z': sp_z, 'bx': bx, 
               'by': by, 'bz': bz, 'struct_name': struct_name, 
               'dimension_id': dimension_id, 
               'block_name': block_name, 
               'block_aux': (block_dict['aux']), 
               'aabb': aabb, 
               'pid': pid, 
               'shipyard_pos': shipyard_pos, 
               'slot_index': slot_index, 
               'area_key': area_key, 
               'preloaded': (preloaded is not None)}
            if preloaded:
                self._on_physicalize_block_chunks_loaded({'code': 1}, timer_args)
            else:
                chunk_comp = CF.CreateChunkSource(LID)
                callback = lambda data: self._on_physicalize_block_chunks_loaded(data, timer_args)
                chunk_comp.DoTaskOnChunkAsync(dimension_id, (
                 sp_x, 0, sp_z), (
                 sp_x + PHYS_HOME_SIZE, 0, sp_z + PHYS_HOME_SIZE), callback)
            return

    def _on_physicalize_block_chunks_loaded(self, data, args):
        """DoTaskOnChunkAsync 回调（或预加载同步调用）：执行 Shipyard 操作"""
        if data.get('code') != 1:
            print '[ValkyrienBE] physicalize_block: chunk loading failed'
            self._store.release_shipyard_slot(args['slot_index'])
            return
        else:
            sp_x = args['sp_x']
            sp_y = args['sp_y']
            sp_z = args['sp_z']
            bx = args['bx']
            by = args['by']
            bz = args['bz']
            struct_name = args['struct_name']
            dimension_id = args['dimension_id']
            block_name = args['block_name']
            block_aux = args['block_aux']
            aabb = args['aabb']
            pid = args['pid']
            shipyard_pos = args['shipyard_pos']
            slot_index = args['slot_index']
            area_key = args['area_key']
            is_preloaded = args.get('preloaded', False)
            sx, sy, sz = shipyard_pos
            game_comp = CF.CreateGame(LID)
            chunk_comp = CF.CreateChunkSource(LID)
            if not is_preloaded:
                chunk_comp.SetAddArea(area_key, dimension_id, (
                 sp_x - SHIPYARD_PADDING, 0, sp_z - SHIPYARD_PADDING), (
                 sp_x + SHIPYARD_PADDING, 0, sp_z + SHIPYARD_PADDING))
                tick_eid = self._system.CreateEngineEntityByTypeStr('physstimu:xiaobo_phys_tick', (sp_x, -60, sp_z), (0,
                                                                                                                      0), dimension_id)
                if tick_eid:
                    self._slot_tick_entities[slot_index] = tick_eid
                game_comp.PlaceStructure(None, (sp_x, sp_y, sp_z), PHYS_HOME_STRUCTURE, dimension_id, 0, animationMode=0, animationTime=0, inculdeEntity=False, removeBlock=False, mirrorMode=0, integrity=100, seed=-1)
            game_comp.PlaceStructure(None, (sx, sy, sz), struct_name, dimension_id, 0, animationMode=0, animationTime=0, inculdeEntity=False, removeBlock=False, mirrorMode=0, integrity=100, seed=-1)
            cmd_comp = CF.CreateCommand(LID)
            cmd_comp.SetCommand(('/setblock {} {} {} air').format(bx, by, bz))
            palette = CF.CreateBlock(pid).GetBlockPaletteBetweenPos(dimension_id, (sx, sy, sz), (sx, sy, sz))
            if palette is None:
                CF.CreateGame(pid).SetOneTipMessage(pid, serverApi.GenerateColor('RED') + '暂不支持此方块物理化')
                self._cleanup_failed_shipyard_slot(slot_index, (sp_x, sp_y, sp_z), area_key, dimension_id, is_preloaded)
                return
            palette_data = palette.SerializeBlockPalette()
            unsupported_blocks = self._find_unsupported_palette_blocks(palette_data)
            if unsupported_blocks:
                CF.CreateGame(pid).SetOneTipMessage(pid, serverApi.GenerateColor('RED') + '该方块暂不支持物理化')
                self._cleanup_failed_shipyard_slot(slot_index, (sp_x, sp_y, sp_z), area_key, dimension_id, is_preloaded)
                return
            palette_name = block_name + ':' + str(block_aux)
            mass, friction, elasticity = get_block_mass_info(block_name)
            entity_spawn_pos = (
             bx + 0.5, by + 0.5, bz + 0.5)
            a_min, a_max = aabb
            local_center, half_extents = self._calc_box_geometry(a_min, a_max, entity_spawn_pos)
            mass_int = int(round(mass))
            user_data = ('{}&0,0,0').format(mass_int)
            aabb_entry = (local_center, half_extents, friction, friction, elasticity, user_data)
            render_offset = (0, -0.5, 0)
            self._store.enqueue_pending_entity([
             aabb_entry], region_size=None, render_offset=render_offset, collider_strategy=DEFAULT_COLLIDER_STRATEGY)
            entity_id = None
            while not entity_id:
                entity_id = self._system.CreateEngineEntityByTypeStr(PHYS_ENTITY_TYPE, entity_spawn_pos, (0,
                                                                                                          0), dimension_id)

            self._store._shipyard_slots[slot_index] = entity_id
            entity_data = PhysicsEntityData(palette_data=palette_data, dimension_id=dimension_id, palette_offset=(0,
                                                                                                                  0,
                                                                                                                  0), aabb_list=[
             aabb_entry], palette_name=palette_name, is_region=False, region_size=None, render_offset=render_offset, collider_strategy=DEFAULT_COLLIDER_STRATEGY, total_mass=mass, shipyard_pos=shipyard_pos, structure_name=struct_name, original_min_pos=(
             bx, by, bz), original_max_pos=(
             bx, by, bz), shipyard_area_key=area_key, slot_index=slot_index)
            self._store.add_entity(entity_id, entity_data)
            self.save_entity_extra_data(entity_id)
            self._schedule_balloon_ready(entity_id)
            render_data = entity_data.to_render_dict(entity_id, pid)
            self._system.BroadcastToAllClient(events.S2C_RENDER_BLOCK, render_data)
            return

    def physicalize_region(self, args):
        """
        批量物理化区域内方块（Shipyard 架构）
        优先使用预加载池中的就绪槽位（同步），否则走异步 DoTaskOnChunkAsync。
        @param args: {fromPos, toPos, pid}
        """
        from_pos = args['fromPos']
        to_pos = args['toPos']
        pid = args['pid']
        if not self._pool_ready:
            CF.CreateGame(pid).SetOneTipMessage(pid, serverApi.GenerateColor('RED') + '系统正在初始化中, 请稍后再试...')
            return
        else:
            dimension_id = CF.CreateDimension(pid).GetEntityDimensionId()
            min_x = min(int(from_pos[0]), int(to_pos[0]))
            min_y = min(int(from_pos[1]), int(to_pos[1]))
            min_z = min(int(from_pos[2]), int(to_pos[2]))
            max_x = max(int(from_pos[0]), int(to_pos[0]))
            max_y = max(int(from_pos[1]), int(to_pos[1]))
            max_z = max(int(from_pos[2]), int(to_pos[2]))
            size_x = max_x - min_x + 1
            size_y = max_y - min_y + 1
            size_z = max_z - min_z + 1
            total_blocks = size_x * size_y * size_z
            if total_blocks > MAX_REGION_BLOCKS:
                CF.CreateGame(pid).SetOneTipMessage(pid, serverApi.GenerateColor('RED') + ('选区过大(最多{}个方块), 当前: {}').format(MAX_REGION_BLOCKS, total_blocks))
                return
            preloaded = self._pop_preloaded_slot(dimension_id)
            if preloaded:
                slot_index = preloaded['slot_index']
                sp_x, sp_y, sp_z = preloaded['slot_pos']
                area_key = preloaded['area_key']
            else:
                slot_index, slot_pos = self._store.allocate_shipyard_slot('')
                sp_x, sp_y, sp_z = slot_pos
                area_key = ('vbe_area_{}').format(slot_index)
            struct_name = ('{}:ship_{}').format(SHIPYARD_STRUCT_PREFIX, slot_index)
            cmd_comp = CF.CreateCommand(LID)
            cmd_comp.SetCommand(('/structure save {} {} {} {} {} {} {} memory').format(struct_name, min_x, min_y, min_z, max_x, max_y, max_z), pid)
            half_home = PHYS_HOME_SIZE // 2
            shipyard_pos = (sp_x + half_home - size_x // 2,
             sp_y + half_home - size_y // 2,
             sp_z + half_home - size_z // 2)
            timer_args = {'sp_x': sp_x, 
               'sp_y': sp_y, 'sp_z': sp_z, 'struct_name': struct_name, 
               'dimension_id': dimension_id, 
               'min_x': min_x, 
               'min_y': min_y, 'min_z': min_z, 'max_x': max_x, 
               'max_y': max_y, 'max_z': max_z, 'size_x': size_x, 
               'size_y': size_y, 'size_z': size_z, 'pid': pid, 
               'total_blocks': total_blocks, 'shipyard_pos': shipyard_pos, 
               'slot_index': slot_index, 'area_key': area_key, 'preloaded': (preloaded is not None)}
            if preloaded:
                self._on_physicalize_region_chunks_loaded({'code': 1}, timer_args)
            else:
                chunk_comp = CF.CreateChunkSource(LID)
                callback = lambda data: self._on_physicalize_region_chunks_loaded(data, timer_args)
                chunk_comp.DoTaskOnChunkAsync(dimension_id, (
                 sp_x, 0, sp_z), (
                 sp_x + PHYS_HOME_SIZE, 0, sp_z + PHYS_HOME_SIZE), callback)
            return

    def _on_physicalize_region_chunks_loaded(self, data, args):
        """DoTaskOnChunkAsync 回调（或预加载同步调用）：执行 Shipyard 区域物理化"""
        if data.get('code') != 1:
            print '[ValkyrienBE] physicalize_region: chunk loading failed'
            self._store.release_shipyard_slot(args['slot_index'])
            return
        else:
            sp_x = args['sp_x']
            sp_y = args['sp_y']
            sp_z = args['sp_z']
            struct_name = args['struct_name']
            dimension_id = args['dimension_id']
            min_x = args['min_x']
            min_y = args['min_y']
            min_z = args['min_z']
            max_x = args['max_x']
            max_y = args['max_y']
            max_z = args['max_z']
            size_x = args['size_x']
            size_y = args['size_y']
            size_z = args['size_z']
            pid = args['pid']
            total_blocks = args['total_blocks']
            shipyard_pos = args['shipyard_pos']
            slot_index = args['slot_index']
            area_key = args['area_key']
            is_preloaded = args.get('preloaded', False)
            sx, sy, sz = shipyard_pos
            game_comp = CF.CreateGame(LID)
            chunk_comp = CF.CreateChunkSource(LID)
            cmd_comp = CF.CreateCommand(LID)
            if not is_preloaded:
                chunk_comp.SetAddArea(area_key, dimension_id, (
                 sp_x - SHIPYARD_PADDING, 0, sp_z - SHIPYARD_PADDING), (
                 sp_x + SHIPYARD_PADDING, 0, sp_z + SHIPYARD_PADDING))
                tick_eid = self._system.CreateEngineEntityByTypeStr('physstimu:xiaobo_phys_tick', (sp_x, -60, sp_z), (0,
                                                                                                                      0), dimension_id)
                if tick_eid:
                    self._slot_tick_entities[slot_index] = tick_eid
                game_comp.PlaceStructure(None, (sp_x, sp_y, sp_z), PHYS_HOME_STRUCTURE, dimension_id, 0, animationMode=0, animationTime=0, inculdeEntity=False, removeBlock=False, mirrorMode=0, integrity=100, seed=-1)
            game_comp.PlaceStructure(None, (sx, sy, sz), struct_name, dimension_id, 0, animationMode=0, animationTime=0, inculdeEntity=False, removeBlock=False, mirrorMode=0, integrity=100, seed=-1)
            ship_max = (
             sx + size_x - 1, sy + size_y - 1, sz + size_z - 1)
            palette = CF.CreateBlock(pid).GetBlockPaletteBetweenPos(dimension_id, (sx, sy, sz), ship_max, False)
            if palette is None:
                CF.CreateGame(pid).SetOneTipMessage(pid, serverApi.GenerateColor('RED') + '该区域暂不支持物理化')
                self._cleanup_failed_shipyard_slot(slot_index, (sp_x, sp_y, sp_z), area_key, dimension_id, is_preloaded)
                return
            palette_data = palette.SerializeBlockPalette()
            unsupported_blocks = self._find_unsupported_palette_blocks(palette_data)
            if unsupported_blocks:
                CF.CreateGame(pid).SetOneTipMessage(pid, serverApi.GenerateColor('RED') + '选区包含基岩, 无法物理化')
                self._cleanup_failed_shipyard_slot(slot_index, (sp_x, sp_y, sp_z), area_key, dimension_id, is_preloaded)
                return
            volume = palette_data['volume']
            volume_correct = (volume[1], volume[2], volume[0])
            common = palette_data['common']
            centroid, total_mass, block_name_map, balloon_count = self._calculate_mass_and_centroid(volume_correct, common)
            spawn_pos = (
             min_x + centroid[0] + 0.5, min_y + centroid[1] + 0.5, min_z + centroid[2] + 0.5)
            aabb_list = []
            for lx in range(size_x):
                for ly in range(size_y):
                    for lz in range(size_z):
                        wx = sx + lx
                        wy = sy + ly
                        wz = sz + lz
                        aabb = self._parse_block_aabb((wx, wy, wz), dimension_id)
                        if aabb is None:
                            continue
                        b_name = block_name_map.get((lx, ly, lz), '')
                        b_mass, friction, elasticity = get_block_mass_info(b_name)
                        a_min, a_max = aabb
                        orig_min = (
                         min_x + lx + (a_min[0] - wx),
                         min_y + ly + (a_min[1] - wy),
                         min_z + lz + (a_min[2] - wz))
                        orig_max = (min_x + lx + (a_max[0] - wx),
                         min_y + ly + (a_max[1] - wy),
                         min_z + lz + (a_max[2] - wz))
                        local_center, half_extents = self._calc_box_geometry(orig_min, orig_max, spawn_pos)
                        mass_int = int(round(b_mass))
                        user_data = ('{}&{},{},{}').format(mass_int, lx, ly, lz)
                        aabb_list.append((local_center, half_extents, friction, friction, elasticity, user_data))

            if not aabb_list:
                CF.CreateGame(pid).SetOneTipMessage(pid, serverApi.GenerateColor('RED') + '该区域内无有效碰撞方块, 无法物理化')
                self._store.release_shipyard_slot(slot_index)
                chunk_comp.DeleteArea(area_key)
                return
            cmd_comp.SetCommand(('/fill {} {} {} {} {} {} air').format(min_x, min_y, min_z, max_x, max_y, max_z))
            palette_offset = (
             min_x - spawn_pos[0], min_y - spawn_pos[1], min_z - spawn_pos[2])
            render_offset = (-centroid[0], -(centroid[1] + 0.5), -centroid[2])
            self._store.enqueue_pending_entity(aabb_list, region_size=(
             size_x, size_y, size_z), render_offset=render_offset, collider_strategy=DEFAULT_COLLIDER_STRATEGY)
            entity_id = None
            while not entity_id:
                entity_id = self._system.CreateEngineEntityByTypeStr(PHYS_ENTITY_TYPE, spawn_pos, (0,
                                                                                                   0), dimension_id)

            self._store._shipyard_slots[slot_index] = entity_id
            palette_name = ('region_{}_{}_{}_{}_{}_{}').format(min_x, min_y, min_z, max_x, max_y, max_z)
            entity_data = PhysicsEntityData(palette_data=palette_data, dimension_id=dimension_id, palette_offset=palette_offset, aabb_list=aabb_list, palette_name=palette_name, is_region=True, region_size=(
             size_x, size_y, size_z), render_offset=render_offset, collider_strategy=DEFAULT_COLLIDER_STRATEGY, total_mass=total_mass, shipyard_pos=shipyard_pos, structure_name=struct_name, original_min_pos=(
             min_x, min_y, min_z), original_max_pos=(
             max_x, max_y, max_z), shipyard_area_key=area_key, slot_index=slot_index, balloon_count=balloon_count)
            self._store.add_entity(entity_id, entity_data)
            self.save_entity_extra_data(entity_id)
            self._schedule_balloon_ready(entity_id)
            render_data = entity_data.to_render_dict(entity_id, pid)
            self._system.BroadcastToAllClient(events.S2C_RENDER_BLOCK, render_data)
            CF.CreateGame(pid).SetOneTipMessage(pid, serverApi.GenerateColor('GREEN') + ('已物理化 {} 个碰撞方块 (共{}格, 总质量{:.0f}kg)').format(len(aabb_list), total_blocks, total_mass))
            return

    def remove_physic_block(self, args):
        """
        去除物理化方块，使用调色板还原方块到世界
        @param args: {entityId, pid(可选)}
        """
        entity_id = args['entityId']
        pid = args.get('pid')
        if entity_id in self._store._spray_entity_ids:
            if pid:
                CF.CreateGame(pid).SetOneTipMessage(pid, serverApi.GenerateColor('RED') + '喷射方块不可操作')
            return
        catcher_pid = self._store.get_catcher_of(entity_id)
        if catcher_pid:
            phys_comp = CF.CreatePhysx(entity_id)
            phys_comp.SetRigidBodyFlag(PxRigidBodyFlag.eKINEMATIC, False)
            self._store.remove_caught(catcher_pid)
            self._system.NotifyToClient(catcher_pid, events.S2C_ON_RELEASE_BLOCK, {'entityId': entity_id})
        entity_data = self._store.get_entity(entity_id)
        if not entity_data:
            self._system.DestroyEntity(entity_id)
            return
        self._restore_blocks(entity_id, entity_data)
        self._store.remove_entity(entity_id)
        self._balloon_ready_set.discard(entity_id)
        extra_comp = CF.CreateExtraData(entity_id)
        extra_comp.CleanExtraData('phys_data')
        self._system.DestroyEntity(entity_id)
        self._replenish_pool()
        return

    def delete_all(self, args):
        """一键删除所有物理化方块（不还原）"""
        if not self._pool_ready:
            CF.CreateGame(LID).SetNotifyMsg('系统正在初始化中, 请稍后再试...', serverApi.GenerateColor('RED'))
            return
        for pid, catch_state in list(self._store.get_all_caught().items()):
            entity_id = catch_state.entity_id
            try:
                phys_comp = CF.CreatePhysx(entity_id)
                phys_comp.SetRigidBodyFlag(PxRigidBodyFlag.eKINEMATIC, False)
            except:
                pass

            self._system.NotifyToClient(pid, events.S2C_ON_RELEASE_BLOCK, {'entityId': entity_id})

        self._store._caught_entities.clear()
        for pid in list(self._store.get_sucking_players()):
            self._system.NotifyToClient(pid, events.S2C_ON_SPRAY_STATE_CHANGED, {'state': False})

        self._store._sucking_players.clear()
        for pid in list(self._store.get_spraying_players()):
            self._system.NotifyToClient(pid, events.S2C_ON_SPRAY_STATE_CHANGED, {'state': False})

        self._store._spraying_players.clear()
        chunk_comp = CF.CreateChunkSource(LID)
        cmd_comp = CF.CreateCommand(LID)
        for entity_id, edata in list(self._store.get_all_entities().items()):
            if edata.shipyard_area_key:
                chunk_comp.DeleteArea(edata.shipyard_area_key)
            if edata.shipyard_pos and edata.region_size:
                sx, sy, sz = edata.shipyard_pos
                rs = edata.region_size
                cmd_comp.SetCommand(('/fill {} {} {} {} {} {} air').format(sx, sy, sz, sx + rs[0] - 1, sy + rs[1] - 1, sz + rs[2] - 1))
            elif edata.shipyard_pos:
                sx, sy, sz = edata.shipyard_pos
                cmd_comp.SetCommand(('/setblock {} {} {} air').format(sx, sy, sz))
            if edata.slot_index >= 0:
                self._store.release_shipyard_slot(edata.slot_index)

        for entity_id, edata in list(self._store.get_all_entities().items()):
            if edata.slot_index >= 0:
                self._kill_slot_tick_entity(edata.slot_index)

        self._cleanup_preloaded_pool()
        count = self._store.get_entity_count()
        for entity_id in list(self._store.get_all_entities().keys()):
            extra_comp = CF.CreateExtraData(entity_id)
            extra_comp.CleanExtraData('phys_data')
            self._system.DestroyEntity(entity_id)

        self._store._entities.clear()
        self._store._suck_entity_prev_pos.clear()
        self._store._spray_entity_ids.clear()
        self._store._active_contacts.clear()
        self._system.BroadcastToAllClient(events.S2C_ON_ALL_DELETED, {'count': count})
        self.init_preload_pool()
        return

    def on_player_attack_entity(self, args):
        """
        PlayerAttackEntityEvent 回调
        如果被攻击的是物理实体，取消攻击伤害，并将 entityId 通知攻击者客户端，
        由客户端根据当前 phys_state 发送对应的 C2S 事件。
        喷射方块不可操作，攻击时仅提示。
        """
        victim_id = args.get('victimId')
        player_id = args.get('playerId')
        if not victim_id:
            return
        if self._store.has_entity(victim_id):
            args['cancel'] = True
            if victim_id in self._store._spray_entity_ids:
                if player_id:
                    CF.CreateGame(player_id).SetOneTipMessage(player_id, serverApi.GenerateColor('RED') + '喷射方块不可操作')
                return
            if player_id:
                self._system.NotifyToClient(player_id, events.S2C_CONFIRM_STATE, {'entityId': victim_id})
        return

    def _raycast_to_shipyard_block(self, pid, dimension_id):
        """
        通用射线检测：Physx Raycast 找到物理实体后，变换到 Shipyard 空间，
        用 getEntitiesOrBlockFromRay 精确定位方块（含无碰撞箱但有 clip 的方块），
        再用 GetBlockClip 计算交互面。
        @return: dict {hit_entity_id, remote_pos, facing, hit_pos, entity_data} 或 None
        """
        pos_comp = CF.CreatePos(pid)
        rot_comp = CF.CreateRot(pid)
        player_pos = pos_comp.GetPos()
        player_rot = rot_comp.GetRot()
        if not player_pos or not player_rot:
            return
        direction = serverApi.GetDirFromRot(player_rot)
        phys_comp = CF.CreatePhysx(LID)
        results = phys_comp.Raycast(dimension_id, player_pos, direction, 50, 1)
        if not results:
            return
        else:
            hit = results[0]
            hit_entity_id = hit.get('entityId')
            phys_hit_pos = hit.get('pos', (0, 0, 0))
            if not hit_entity_id or not self._store.has_entity(hit_entity_id):
                return
            entity_data = self._store.get_entity(hit_entity_id)
            if not entity_data or not entity_data.shipyard_pos:
                return
            entity_pos = CF.CreatePos(hit_entity_id).GetPos()
            if not entity_pos:
                return
            entity_phys = CF.CreatePhysx(hit_entity_id)
            q_tuple = entity_phys.GetQuaternion()
            if q_tuple:
                q_inv = Quaternion.Inverse(Quaternion(q_tuple))
            else:
                q_inv = None
            sx, sy, sz = entity_data.shipyard_pos
            po = entity_data.palette_offset
            local_to_shipyard = (sx - po[0], sy - po[1], sz - po[2])
            rel_px = player_pos[0] - entity_pos[0]
            rel_py = player_pos[1] - entity_pos[1]
            rel_pz = player_pos[2] - entity_pos[2]
            if q_inv:
                local_p = q_inv * Vector3(rel_px, rel_py, rel_pz)
                local_d = q_inv * Vector3(direction[0], direction[1], direction[2])
                ship_origin = (local_p[0] + local_to_shipyard[0],
                 local_p[1] + local_to_shipyard[1],
                 local_p[2] + local_to_shipyard[2])
                ship_dir = (local_d[0], local_d[1], local_d[2])
            else:
                ship_origin = (
                 rel_px + local_to_shipyard[0],
                 rel_py + local_to_shipyard[1],
                 rel_pz + local_to_shipyard[2])
                ship_dir = direction
            d_len = math.sqrt(ship_dir[0] ** 2 + ship_dir[1] ** 2 + ship_dir[2] ** 2)
            if d_len > 1e-06:
                ship_dir = (
                 ship_dir[0] - d_len, ship_dir[1] - d_len, ship_dir[2] - d_len)
            ray_filter = serverApi.GetMinecraftEnum().RayFilterType.OnlyBlocks
            ray_results = serverApi.getEntitiesOrBlockFromRay(dimension_id, ship_origin, ship_dir, 100, False, ray_filter)
            if not ray_results:
                return
            rs = entity_data.region_size if entity_data.region_size else (1, 1, 1)
            remote_pos = None
            ship_hit_pos = None
            for ray_hit in ray_results:
                if ray_hit.get('type') != 'Block':
                    continue
                bpos = ray_hit.get('pos')
                if not bpos:
                    continue
                bx, by, bz = bpos
                if sx <= bx < sx + rs[0] and sy <= by < sy + rs[1] and sz <= bz < sz + rs[2]:
                    remote_pos = (
                     bx, by, bz)
                    ship_hit_pos = ray_hit.get('hitPos', bpos)
                    break

            if remote_pos is None:
                return
            facing = self._calc_facing_from_clip(remote_pos, ship_hit_pos, dimension_id)
            return {'hit_entity_id': hit_entity_id, 
               'remote_pos': remote_pos, 
               'facing': facing, 
               'hit_pos': phys_hit_pos, 
               'entity_data': entity_data}

    def _calc_facing_from_clip(self, block_pos, hit_pos, dimension_id):
        """
        根据 GetBlockClip 返回的 AABB 和命中点计算交互面
        @param block_pos: tuple(int,int,int) 方块整数坐标
        @param hit_pos: tuple(float,float,float) 射线命中精确坐标
        @param dimension_id: int
        @return: int Facing (Down=0,Up=1,North=2,South=3,West=4,East=5)
        """
        block_info = CF.CreateBlockInfo(LID)
        clip = block_info.GetBlockClip(block_pos, dimension_id)
        if clip:
            a_min = clip.get('min', (block_pos[0], block_pos[1], block_pos[2]))
            a_max = clip.get('max', (block_pos[0] + 1, block_pos[1] + 1, block_pos[2] + 1))
        else:
            a_min = (
             block_pos[0], block_pos[1], block_pos[2])
            a_max = (block_pos[0] + 1, block_pos[1] + 1, block_pos[2] + 1)
        hx, hy, hz = hit_pos
        dists = [
         (
          abs(hy - a_min[1]), 0),
         (
          abs(hy - a_max[1]), 1),
         (
          abs(hz - a_min[2]), 2),
         (
          abs(hz - a_max[2]), 3),
         (
          abs(hx - a_min[0]), 4),
         (
          abs(hx - a_max[0]), 5)]
        dists.sort(key=(lambda x: x[0]))
        return dists[0][1]

    def _normal_to_facing(self, normal):
        """
        将法线向量映射到 Facing 枚举
        @param normal: (nx, ny, nz) 局部空间法线
        @return: int  Facing 枚举值 (Down=0,Up=1,North=2,South=3,West=4,East=5)
        """
        nx, ny, nz = normal
        ax, ay, az = abs(nx), abs(ny), abs(nz)
        if ay >= ax and ay >= az:
            if ny > 0:
                return 1
            return 0
        if az >= ax and az >= ay:
            if nz > 0:
                return 3
            return 2
        if nx > 0:
            return 5
        return 4

    def refresh_entity(self, entity_id, notify_pid=None):
        """
        刷新物理实体：确保 Shipyard 区块已加载后，重新读取方块，重建碰撞体和渲染。
        保留实体位置/旋转/速度以平滑过渡。
        @param entity_id: str
        """
        entity_data = self._store.get_entity(entity_id)
        if not entity_data or not entity_data.shipyard_pos:
            return
        dim_id = entity_data.dimension_id
        sx, sy, sz = entity_data.shipyard_pos
        rs = entity_data.region_size if entity_data.region_size else (1, 1, 1)
        chunk_comp = CF.CreateChunkSource(LID)
        callback = lambda data: self._on_refresh_chunks_loaded(data, entity_id, notify_pid)
        chunk_comp.DoTaskOnChunkAsync(dim_id, (
         sx, 0, sz), (
         sx + rs[0], 0, sz + rs[2]), callback)
        return

    def _on_refresh_chunks_loaded(self, data, entity_id, notify_pid=None):
        """DoTaskOnChunkAsync 回调：区块加载完成后启动刷新循环"""
        if data.get('code') != 1:
            print ('[ValkyrienBE] refresh_entity: chunk loading failed for entity {}').format(entity_id)
            return
        self._start_refresh_cycle(entity_id, notify_pid)
        return

    def _start_refresh_cycle(self, entity_id, notify_pid=None):
        """启动刷新循环：立即执行一次刷新，再每秒刷新一次共3次（如果同一实体已有刷新循环则先取消）"""
        existing = self._refresh_timers.get(entity_id)
        if existing:
            CF.CreateGame(LID).CancelTimer(existing['timer'])
            del self._refresh_timers[entity_id]
        new_entity_id = self._refresh_entity_impl(entity_id, notify_pid)
        if new_entity_id:
            entity_id = new_entity_id
        timer = CF.CreateGame(LID).AddRepeatedTimer(0.2, self._on_repeated_refresh, entity_id)
        if timer:
            self._refresh_timers[entity_id] = {'timer': timer, 'count': 0, 
               'notify_pid': notify_pid}
        return

    def _on_repeated_refresh(self, entity_id):
        """AddRepeatedTimer 回调：每秒执行一次刷新，满3次后自动取消"""
        info = self._refresh_timers.get(entity_id)
        if not info:
            return
        notify_pid = info.get('notify_pid')
        new_entity_id = self._refresh_entity_impl(entity_id, notify_pid)
        if new_entity_id and new_entity_id != entity_id:
            CF.CreateGame(LID).CancelTimer(info['timer'])
            del self._refresh_timers[entity_id]
            self._start_refresh_cycle(new_entity_id, notify_pid)
            return
        if not self._store.has_entity(entity_id):
            CF.CreateGame(LID).CancelTimer(info['timer'])
            del self._refresh_timers[entity_id]
            return
        info['count'] += 1
        if info['count'] >= 15:
            CF.CreateGame(LID).CancelTimer(info['timer'])
            del self._refresh_timers[entity_id]
        return

    def _refresh_entity_impl(self, entity_id, notify_pid=None):
        """
        刷新物理实体的实际逻辑（假设 Shipyard 区块已加载）
        @param entity_id: str
        """
        entity_data = self._store.get_entity(entity_id)
        if not entity_data or not entity_data.shipyard_pos:
            return
        dim_id = entity_data.dimension_id
        sx, sy, sz = entity_data.shipyard_pos
        slot_index = entity_data.slot_index
        area_key = ('vbe_area_{}').format(slot_index)
        area_comp = CF.CreateChunkSource(LID)
        all_area_keys = area_comp.GetAllAreaKeys()
        if area_key not in all_area_keys:
            area_comp.SetAddArea(area_key, dim_id, (
             sx - SHIPYARD_PADDING, 0, sz - SHIPYARD_PADDING), (
             sx + SHIPYARD_PADDING, 0, sz + SHIPYARD_PADDING))
        pos_comp = CF.CreatePos(entity_id)
        current_pos = pos_comp.GetPos()
        phys_comp = CF.CreatePhysx(entity_id)
        current_quat = phys_comp.GetQuaternion()
        if entity_data.region_size:
            rs = entity_data.region_size
            ship_max = (sx + rs[0] - 1, sy + rs[1] - 1, sz + rs[2] - 1)
        else:
            ship_max = (
             sx, sy, sz)
            rs = (1, 1, 1)
        read_min, read_max = self._get_shipyard_palette_range(entity_data, expand=1)
        palette_expanded = CF.CreateBlock(LID).GetBlockPaletteBetweenPos(dim_id, read_min, read_max, False)
        if palette_expanded is None:
            print '[ValkyrienBE] refresh_entity: failed to read Shipyard palette'
            return
        else:
            expanded_data = palette_expanded.SerializeBlockPalette()
            av = expanded_data.get('volume', (0, 0, 0))
            av_correct = (av[1], av[2], av[0])
            ax_len, ay_len, az_len = av_correct
            stride_x = az_len
            stride_y = ax_len * az_len
            min_lx, min_ly, min_lz = ax_len, ay_len, az_len
            max_lx, max_ly, max_lz = (-1, -1, -1)
            for block_key, block_indices in expanded_data.get('common', {}).items():
                bname = block_key[0] if isinstance(block_key, (tuple, list)) else str(block_key)
                if bname == 'minecraft:air' or not self._is_supported_physical_block(bname):
                    continue
                for idx in block_indices:
                    y = idx // stride_y
                    rem = idx % stride_y
                    x = rem // stride_x
                    z = rem % stride_x
                    min_lx = min(min_lx, x)
                    min_ly = min(min_ly, y)
                    min_lz = min(min_lz, z)
                    max_lx = max(max_lx, x)
                    max_ly = max(max_ly, y)
                    max_lz = max(max_lz, z)

            if max_lx >= 0:
                new_sx = read_min[0] + min_lx
                new_sy = read_min[1] + min_ly
                new_sz = read_min[2] + min_lz
                new_ex = read_min[0] + max_lx
                new_ey = read_min[1] + max_ly
                new_ez = read_min[2] + max_lz
                new_rs = (new_ex - new_sx + 1, new_ey - new_sy + 1, new_ez - new_sz + 1)
                if (
                 new_sx, new_sy, new_sz) != (sx, sy, sz) or new_rs != tuple(rs):
                    lo_x = new_sx - sx
                    lo_y = new_sy - sy
                    lo_z = new_sz - sz
                    entity_data.shipyard_pos = (new_sx, new_sy, new_sz)
                    if entity_data.original_min_pos:
                        ox, oy, oz = entity_data.original_min_pos
                        entity_data.original_min_pos = (ox + lo_x, oy + lo_y, oz + lo_z)
                    if entity_data.original_min_pos:
                        nmx, nmy, nmz = entity_data.original_min_pos
                        entity_data.original_max_pos = (
                         nmx + new_rs[0] - 1, nmy + new_rs[1] - 1, nmz + new_rs[2] - 1)
                    old_ro = entity_data.render_offset or (0, -0.5, 0)
                    entity_data.render_offset = (old_ro[0] + lo_x, old_ro[1] + lo_y, old_ro[2] + lo_z)
                    entity_data.region_size = new_rs
                    entity_data.is_region = True
                    sx, sy, sz = new_sx, new_sy, new_sz
                    rs = new_rs
                    ship_max = (sx + rs[0] - 1, sy + rs[1] - 1, sz + rs[2] - 1)
            struct_name = entity_data.structure_name
            if struct_name:
                cmd_comp = CF.CreateCommand(LID)
                cmd_comp.SetCommand(('/structure save {} {} {} {} {} {} {} memory').format(struct_name, sx, sy, sz, ship_max[0], ship_max[1], ship_max[2]))
            palette = CF.CreateBlock(LID).GetBlockPaletteBetweenPos(dim_id, (sx, sy, sz), ship_max, False)
            if palette is None:
                print '[ValkyrienBE] refresh_entity: failed to read Shipyard palette'
                return
            palette_data = palette.SerializeBlockPalette()
            unsupported_blocks = self._find_unsupported_palette_blocks(palette_data)
            if unsupported_blocks:
                print ('[ValkyrienBE] refresh_entity: unsupported blocks found for entity {} -> {}').format(entity_id, (',').join(unsupported_blocks))
                self._notify_player_tip(notify_pid, 'RED', '方块过长，碰到基岩盒子，已取消刷新')
                return
            volume = palette_data['volume']
            volume_correct = (volume[1], volume[2], volume[0])
            common = palette_data['common']
            old_palette = entity_data.palette_data
            if old_palette:
                old_sigs = self._extract_block_signatures(old_palette)
                new_sigs = self._extract_block_signatures(palette_data)
                compare_result = self._compare_block_signatures(old_sigs, new_sigs)
                change_type = compare_result[0]
                if change_type == 'unchanged':
                    print 'unchanged'
                    return
                if change_type == 'only_aux_changed':
                    print 'only_aux_changed'
                    self._light_refresh_entity(entity_id, entity_data, palette_data, palette, current_quat)
                    return
            centroid, total_mass, block_name_map, balloon_count = self._calculate_mass_and_centroid(volume_correct, common)
            size_x, size_y, size_z = rs
            orig_min = entity_data.original_min_pos if entity_data.original_min_pos else (0,
                                                                                          0,
                                                                                          0)
            old_render = entity_data.render_offset if entity_data.render_offset else (0,
                                                                                      -0.5,
                                                                                      0)
            old_cx = -old_render[0]
            old_cy = -old_render[1] - 0.5
            old_cz = -old_render[2]
            delta_cx = centroid[0] - old_cx
            delta_cy = centroid[1] - old_cy
            delta_cz = centroid[2] - old_cz
            spawn_pos_local = (
             orig_min[0] + centroid[0] + 0.5,
             orig_min[1] + centroid[1] + 0.5,
             orig_min[2] + centroid[2] + 0.5)
            if current_quat:
                q = Quaternion(current_quat)
                world_delta = q * Vector3(delta_cx, delta_cy, delta_cz)
                dx, dy, dz = world_delta[0], world_delta[1], world_delta[2]
            else:
                dx, dy, dz = delta_cx, delta_cy, delta_cz
            if current_pos:
                spawn_pos_world = (
                 current_pos[0] + dx, current_pos[1] + dy, current_pos[2] + dz)
            else:
                spawn_pos_world = spawn_pos_local
            aabb_list = []
            for lx in range(size_x):
                for ly in range(size_y):
                    for lz in range(size_z):
                        wx = sx + lx
                        wy = sy + ly
                        wz = sz + lz
                        aabb = self._parse_block_aabb((wx, wy, wz), dim_id)
                        if aabb is None:
                            continue
                        b_name = block_name_map.get((lx, ly, lz), '')
                        b_mass, friction, elasticity = get_block_mass_info(b_name)
                        a_min, a_max = aabb
                        orig_a_min = (
                         orig_min[0] + lx + (a_min[0] - wx),
                         orig_min[1] + ly + (a_min[1] - wy),
                         orig_min[2] + lz + (a_min[2] - wz))
                        orig_a_max = (orig_min[0] + lx + (a_max[0] - wx),
                         orig_min[1] + ly + (a_max[1] - wy),
                         orig_min[2] + lz + (a_max[2] - wz))
                        local_center, half_extents = self._calc_box_geometry(orig_a_min, orig_a_max, spawn_pos_local)
                        mass_int = int(round(b_mass))
                        user_data = ('{}&{},{},{}').format(mass_int, lx, ly, lz)
                        aabb_list.append((local_center, half_extents, friction, friction, elasticity, user_data))

            if not aabb_list:
                print '[ValkyrienBE] refresh_entity: no valid blocks, destroying entity'
                self._store.remove_entity(entity_id)
                self._balloon_ready_set.discard(entity_id)
                extra_comp = CF.CreateExtraData(entity_id)
                extra_comp.CleanExtraData('phys_data')
                self._system.DestroyEntity(entity_id)
                if entity_data.shipyard_area_key:
                    chunk_comp = CF.CreateChunkSource(LID)
                    chunk_comp.DeleteArea(entity_data.shipyard_area_key)
                if entity_data.slot_index >= 0:
                    self._store.release_shipyard_slot(entity_data.slot_index)
                self._system.BroadcastToAllClient(events.S2C_ON_ALL_DELETED, {'count': 1})
                return
            palette_offset = (
             orig_min[0] - spawn_pos_local[0],
             orig_min[1] - spawn_pos_local[1],
             orig_min[2] - spawn_pos_local[2])
            render_offset = (-centroid[0], -(centroid[1] + 0.5), -centroid[2])
            self._store.remove_entity(entity_id)
            self._balloon_ready_set.discard(entity_id)
            extra_comp = CF.CreateExtraData(entity_id)
            extra_comp.CleanExtraData('phys_data')
            self._system.DestroyEntity(entity_id)
            self._store.enqueue_pending_entity(aabb_list, region_size=(size_x, size_y, size_z) if entity_data.is_region else None, render_offset=render_offset, collider_strategy=entity_data.collider_strategy or DEFAULT_COLLIDER_STRATEGY)
            new_entity_id = None
            while not new_entity_id:
                new_entity_id = self._system.CreateEngineEntityByTypeStr(PHYS_ENTITY_TYPE, spawn_pos_world, (0,
                                                                                                             0), dim_id)

            CF.CreateGame(LID).AddTimer(0, self._resume_quat, {'entityId': new_entity_id, 'quaternion': current_quat, 'spawn_pos_world': spawn_pos_world})
            slot_index = entity_data.slot_index
            self._store._shipyard_slots[slot_index] = new_entity_id
            safe_id = str(new_entity_id).replace('-', '')[-8:]
            new_palette_name = ('ship_{}_{}').format(slot_index, safe_id)
            new_data = PhysicsEntityData(palette_data=palette_data, dimension_id=dim_id, palette_offset=palette_offset, aabb_list=aabb_list, palette_name=new_palette_name, is_region=entity_data.is_region, region_size=(size_x, size_y, size_z) if entity_data.is_region else None, render_offset=render_offset, collider_strategy=entity_data.collider_strategy, total_mass=total_mass, shipyard_pos=entity_data.shipyard_pos, structure_name=entity_data.structure_name, original_min_pos=entity_data.original_min_pos, original_max_pos=entity_data.original_max_pos, shipyard_area_key=entity_data.shipyard_area_key, slot_index=slot_index, balloon_count=balloon_count)
            self._store.add_entity(new_entity_id, new_data)
            self.save_entity_extra_data(new_entity_id)
            self._schedule_balloon_ready(new_entity_id)
            render_data = new_data.to_render_dict(new_entity_id)
            if current_quat:
                render_data['quaternion'] = current_quat
            self._system.BroadcastToAllClient(events.S2C_RENDER_BLOCK, render_data)
            return new_entity_id

    def _resume_quat(self, args):
        entity_id = args['entityId']
        quaternion = args['quaternion']
        spawn_pos_world = args['spawn_pos_world']
        new_phys = CF.CreatePhysx(entity_id)
        if quaternion:
            new_phys.SetGlobalPose(spawn_pos_world, quaternion)
        return

    def place_block_on_entity(self, args):
        """
        放置方块到物理实体上
        通过 Raycast + Shipyard 空间射线检测定位方块 → 模拟放置 → 刷新
        @param args: {pid}
        """
        pid = args['pid']
        if not self._pool_ready:
            CF.CreateGame(pid).SetOneTipMessage(pid, serverApi.GenerateColor('RED') + '系统正在初始化中, 请稍后再试...')
            return
        dimension_id = CF.CreateDimension(pid).GetEntityDimensionId()
        ray_result = self._raycast_to_shipyard_block(pid, dimension_id)
        if not ray_result:
            return
        hit_entity_id = ray_result['hit_entity_id']
        remote_pos = ray_result['remote_pos']
        facing = ray_result['facing']
        hit_pos = ray_result['hit_pos']
        entity_data = ray_result['entity_data']
        item_dict = CF.CreateItem(pid).GetPlayerItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, 0)
        if self._is_bedrock_item(item_dict):
            self._notify_player_tip(pid, 'RED', '手持基岩时不能与物理实体交互放置')
            return
        shipyard_args = {'pid': pid, 
           'hit_entity_id': hit_entity_id, 
           'item_dict': item_dict, 
           'remote_pos': remote_pos, 
           'facing': facing, 
           'hit_pos': hit_pos, 
           'dimension_id': dimension_id}
        sx, sy, sz = entity_data.shipyard_pos
        rs = entity_data.region_size if entity_data.region_size else (1, 1, 1)
        chunk_comp = CF.CreateChunkSource(LID)
        callback = lambda data: self._on_place_chunks_loaded(data, shipyard_args)
        chunk_comp.DoTaskOnChunkAsync(dimension_id, (
         sx, 0, sz), (
         sx + rs[0], 0, sz + rs[2]), callback)
        return

    def _extract_block_signatures(self, palette_data):
        """
        从调色板数据中提取所有方块的签名
        palette_data 格式:
            volume: (sizeX, sizeY, sizeZ)  -- 区域尺寸
            common: {(block_name, aux): [flat_index, ...], ...}  -- 方块分布
        @return: dict {flat_index: (block_name, aux), ...}
        """
        sigs = {}
        common = palette_data.get('common', {})
        for key, indices in common.items():
            block_name = key[0]
            aux = key[1]
            for idx in indices:
                sigs[idx] = (
                 block_name, aux)

        return sigs

    def _compare_block_signatures(self, old_sigs, new_sigs):
        """
        比较两个块签名集合，判断变化类型
        @param old_sigs: dict {flat_index: (block_name, aux), ...}
        @param new_sigs: dict {flat_index: (block_name, aux), ...}
        @return: tuple ('unchanged'|'only_aux_changed'|'block_changed', None, None)
        """
        if old_sigs == new_sigs:
            return ('unchanged', None, None)
        else:
            old_positions = set(old_sigs.keys())
            new_positions = set(new_sigs.keys())
            if old_positions != new_positions:
                return ('block_changed', None, None)
            only_aux_diff = True
            for pos in old_positions:
                old_id, old_aux = old_sigs[pos]
                new_id, new_aux = new_sigs[pos]
                if old_id != new_id:
                    only_aux_diff = False
                    break

            if only_aux_diff:
                return ('only_aux_changed', None, None)
            return ('block_changed', None, None)
            return

    def _light_refresh_entity(self, entity_id, entity_data, palette_data, palette_obj, current_quat):
        """
        轻量刷新：方块种类和位置未变时，仅更新客户端调色板渲染，不销毁/重建实体。
        保持 entity_id、碰撞体、物理状态完全不变。
        @param entity_id: str
        @param entity_data: PhysicsEntityData
        @param palette_data: dict 新的调色板序列化数据
        @param palette_obj: 调色板对象（引擎返回）
        @param current_quat: 当前四元数
        """
        entity_data.palette_data = palette_data
        safe_id = str(entity_id).replace('-', '')[-8:]
        ts = str(int(time.time() * 1000))[-6:]
        new_palette_name = ('ship_{}_{}_{}').format(entity_data.slot_index, safe_id, ts)
        entity_data.palette_name = new_palette_name
        self._store.add_entity(entity_id, entity_data)
        self.save_entity_extra_data(entity_id)
        render_data = entity_data.to_render_dict(entity_id)
        render_data['lightRefresh'] = True
        if current_quat:
            render_data['quaternion'] = current_quat
        self._system.BroadcastToAllClient(events.S2C_RENDER_BLOCK, render_data)
        print ('[ValkyrienBE] Light refresh for entity {} (palette unchanged, render only)').format(entity_id)
        return

    def _compare_palettes(self, before, after):
        """
        对比两个序列化调色板的 common 字段，判断方块是否有变化。
        @return: True 表示有变化，False 表示无变化
        """
        bc = before.get('common', {})
        ac = after.get('common', {})
        if set(str(k) for k in bc.keys()) != set(str(k) for k in ac.keys()):
            return True
        for key in bc:
            b_indices = sorted(bc[key])
            a_indices = sorted(ac.get(key, []))
            if b_indices != a_indices:
                return True

        return False

    def _get_shipyard_palette_range(self, entity_data, expand=0):
        """
        计算 Shipyard 调色板读取范围
        @param entity_data: PhysicsEntityData
        @param expand: 各方向扩展的方块数（放置时需+1以捕获边缘外新方块）
        @return: (min_pos, max_pos) 两个 tuple
        """
        sx, sy, sz = entity_data.shipyard_pos
        rs = entity_data.region_size if entity_data.region_size else (1, 1, 1)
        read_min = (sx - expand, sy - expand, sz - expand)
        read_max = (sx + rs[0] - 1 + expand, sy + rs[1] - 1 + expand, sz + rs[2] - 1 + expand)
        return (read_min, read_max)

    def _save_and_move_shipyard_entities(self, entity_data, hit_pos, dimension_id, remote_pos=None):
        """
        获取 Shipyard 区域中 remote_pos 附近（半径5格）的掉落物实体 NBT，
        计算相对位置后在真实目标位置（hit_pos）生成对应掉落物，
        然后清除 Shipyard 残留实体。
        @param entity_data: PhysicsEntityData
        @param hit_pos: tuple 世界空间命中位置
        @param dimension_id: int
        @param remote_pos: tuple Shipyard 中被操作方块的坐标（可选，默认取 Shipyard 中心）
        """
        sx, sy, sz = entity_data.shipyard_pos
        rs = entity_data.region_size if entity_data.region_size else (1, 1, 1)
        all_entities = CF.CreateGame(LID).GetEntitiesInSquareArea(None, (remote_pos[0] - 5 + 0.5, remote_pos[1] - 5 + 0.5, remote_pos[2] - 5 + 0.5), (remote_pos[0] + 5 + 0.5, remote_pos[1] + 5 + 0.5, remote_pos[2] + 5 + 0.5), dimension_id)
        if all_entities:
            for eid in all_entities:
                entity_nbt = CF.CreateEntityDefinitions(eid).GetEntityNBTTags()
                if entity_nbt and entity_nbt['identifier']['__value__'] != 'minecraft:player':
                    ex, ey, ez = CF.CreatePos(eid).GetPos()
                    rel_x = ex - remote_pos[0]
                    rel_y = ey - remote_pos[1]
                    rel_z = ez - remote_pos[2]
                    new_x = hit_pos[0] + rel_x
                    new_y = hit_pos[1] + rel_y
                    new_z = hit_pos[2] + rel_z
                    self._system.CreateEngineEntityByNBT(entity_nbt, (new_x, new_y, new_z), None, dimension_id)

        cmd_comp = CF.CreateCommand(LID)
        cmd_comp.SetCommand(('/kill @e[x={},y={},z={},dx={},dy={},dz={},type=!player]').format(sx, sy, sz, rs[0], rs[1], rs[2]))
        return

    def _on_place_chunks_loaded(self, data, args):
        """DoTaskOnChunkAsync 回调：区块加载完成后执行放置操作
        新逻辑：
        1. 操作前获取调色板快照
        2. EntityUseItemToPos 模拟放置
        3. 操作后获取调色板快照
        4. 对比：有变化→扩展区域+刷新；无变化→走 fallback -64
        5. 无论是否变化，structure save 实体 + place 搬运掉落物
        """
        if data.get('code') != 1:
            print '[ValkyrienBE] place_block_on_entity: chunk loading failed'
            return
        else:
            hit_entity_id = args['hit_entity_id']
            entity_data = self._store.get_entity(hit_entity_id)
            if not entity_data or not entity_data.shipyard_pos:
                return
            pid = args['pid']
            item_dict = args['item_dict']
            if self._is_bedrock_item(item_dict):
                self._notify_player_tip(pid, 'RED', '手持基岩时不能与物理实体交互放置')
                return
            remote_pos = args['remote_pos']
            facing = args['facing']
            hit_pos = args['hit_pos']
            dimension_id = args['dimension_id']
            sx, sy, sz = entity_data.shipyard_pos
            slot_index = entity_data.slot_index
            area_key = ('vbe_area_{}').format(slot_index)
            area_comp = CF.CreateChunkSource(LID)
            all_area_keys = area_comp.GetAllAreaKeys()
            if area_key not in all_area_keys:
                area_comp.SetAddArea(area_key, dimension_id, (
                 sx - SHIPYARD_PADDING, 0, sz - SHIPYARD_PADDING), (
                 sx + SHIPYARD_PADDING, 0, sz + SHIPYARD_PADDING))
            read_min, read_max = self._get_shipyard_palette_range(entity_data, expand=1)
            palette_before = CF.CreateBlock(LID).GetBlockPaletteBetweenPos(dimension_id, read_min, read_max, False)
            before_data = palette_before.SerializeBlockPalette() if palette_before else None
            game_comp = CF.CreateGame(LID)
            game_comp.EntityUseItemToPos(pid, item_dict, remote_pos, facing)
            palette_after = CF.CreateBlock(LID).GetBlockPaletteBetweenPos(dimension_id, read_min, read_max, False)
            after_data = palette_after.SerializeBlockPalette() if palette_after else None
            has_change = False
            if before_data and after_data:
                has_change = self._compare_palettes(before_data, after_data)
            if has_change:
                rs = entity_data.region_size if entity_data.region_size else (1, 1,
                                                                              1)
                av = after_data.get('volume', (0, 0, 0))
                av_correct = (av[1], av[2], av[0])
                ax_len, ay_len, az_len = av_correct
                stride_x = az_len
                stride_y = ax_len * az_len
                min_lx, min_ly, min_lz = ax_len, ay_len, az_len
                max_lx, max_ly, max_lz = (-1, -1, -1)
                for block_key, block_indices in after_data.get('common', {}).items():
                    bname = block_key[0] if isinstance(block_key, (tuple, list)) else str(block_key)
                    if bname == 'minecraft:air':
                        continue
                    for idx in block_indices:
                        y = idx // stride_y
                        rem = idx % stride_y
                        x = rem // stride_x
                        z = rem % stride_x
                        min_lx = min(min_lx, x)
                        min_ly = min(min_ly, y)
                        min_lz = min(min_lz, z)
                        max_lx = max(max_lx, x)
                        max_ly = max(max_ly, y)
                        max_lz = max(max_lz, z)

                if max_lx >= 0:
                    new_sx = read_min[0] + min_lx
                    new_sy = read_min[1] + min_ly
                    new_sz = read_min[2] + min_lz
                    new_ex = read_min[0] + max_lx
                    new_ey = read_min[1] + max_ly
                    new_ez = read_min[2] + max_lz
                    new_rs = (new_ex - new_sx + 1, new_ey - new_sy + 1, new_ez - new_sz + 1)
                    if (
                     new_sx, new_sy, new_sz) != (sx, sy, sz) or new_rs != rs:
                        lo_x = new_sx - sx
                        lo_y = new_sy - sy
                        lo_z = new_sz - sz
                        entity_data.shipyard_pos = (new_sx, new_sy, new_sz)
                        if entity_data.original_min_pos:
                            ox, oy, oz = entity_data.original_min_pos
                            entity_data.original_min_pos = (ox + lo_x, oy + lo_y, oz + lo_z)
                        if entity_data.original_min_pos:
                            nmx, nmy, nmz = entity_data.original_min_pos
                            entity_data.original_max_pos = (
                             nmx + new_rs[0] - 1, nmy + new_rs[1] - 1, nmz + new_rs[2] - 1)
                        old_ro = entity_data.render_offset or (0, -0.5, 0)
                        entity_data.render_offset = (old_ro[0] + lo_x, old_ro[1] + lo_y, old_ro[2] + lo_z)
                        entity_data.region_size = new_rs
                        entity_data.is_region = True
                block_name = item_dict.get('newItemName', '')
                self._system.BroadcastToAllClient(events.S2C_PLAY_SOUND_PARTICLE, {'action': 'place', 
                   'block_name': block_name, 
                   'pos': hit_pos, 
                   'pid': pid})
                CF.CreateGame(LID).AddTimer(0, self._start_refresh_cycle, hit_entity_id, pid)
            else:
                player_pos = CF.CreatePos(pid).GetPos()
                if player_pos:
                    fb_x = int(math.floor(player_pos[0]))
                    fb_z = int(math.floor(player_pos[2]))
                    existing_fb = self._store.get_fallback_block(pid)
                    if existing_fb:
                        old_pos = existing_fb['fallback_pos']
                        if old_pos[0] != fb_x or old_pos[2] != fb_z:
                            self.cleanup_player_fallbacks(pid)
                    fallback_block_pos = (
                     fb_x, -64, fb_z)
                    block_info = CF.CreateBlockInfo(LID)
                    ship_block = block_info.GetBlockNew(remote_pos, dimension_id)
                    block_info.SetBlockNew((fb_x, -63, fb_z), {'name': 'minecraft:air', 'aux': 0}, 0, dimension_id, True)
                    block_info.SetBlockNew((fb_x, -64, fb_z), {'name': (ship_block['name']), 'aux': (ship_block['aux'])}, 0, dimension_id, True)
                    nbt = block_info.GetBlockEntityData(dimension_id, remote_pos)
                    if nbt:
                        block_info.SetBlockEntityData(dimension_id, fallback_block_pos, nbt)
                    before_interact_range = CF.CreatePlayer(pid).GetPlayerInteracteRange()
                    CF.CreatePlayer(pid).SetPlayerInteracteRange(400)
                    self._store.add_fallback_block(pid, {'fallback_pos': fallback_block_pos, 
                       'shipyard_pos': remote_pos, 
                       'dim_id': dimension_id, 
                       'entity_id': hit_entity_id})
                    self._system.NotifyToClient(pid, events.S2C_FALLBACK_BLOCK_READY, {'fallback_block_pos': fallback_block_pos, 
                       'pid': pid, 
                       'before_interact_range': before_interact_range, 
                       'facing': facing, 
                       'hit_entity_id': hit_entity_id, 
                       'dim_id': dimension_id, 
                       'remote_pos': remote_pos, 
                       'hit_pos': hit_pos, 
                       'item_name': (item_dict.get('newItemName', '') if item_dict else '')})
                    return
            new_entity_data = None
            for eid, edata in self._store.get_all_entities().items():
                if edata.slot_index == slot_index:
                    new_entity_data = edata
                    break

            if new_entity_data:
                self._save_and_move_shipyard_entities(new_entity_data, hit_pos, dimension_id, remote_pos)
            return

    def on_fallback_confirm(self, args):
        """
        客户端确认 fallback 方块已放置成功的 C2S 回调。
        执行 PlayerUseItemToPos → 恢复交互距离 → 对比调色板 → 按需刷新 → 搬运实体
        """
        pid = args.get('pid')
        timeout = args.get('timeout', False)
        fallback_block_pos = args.get('fallback_block_pos')
        before_interact_range = args.get('before_interact_range', 6)
        facing = args.get('facing', 1)
        hit_entity_id = args.get('hit_entity_id')
        dimension_id = args.get('dim_id', 0)
        remote_pos = args.get('remote_pos')
        hit_pos = args.get('hit_pos')
        item_name = args.get('item_name', '')
        if timeout:
            self.cleanup_player_fallbacks(pid)
            CF.CreatePlayer(pid).SetPlayerInteracteRange(before_interact_range)
            return
        item_dict = CF.CreateItem(pid).GetPlayerItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, 0)
        if self._is_bedrock_item(item_dict):
            self.cleanup_player_fallbacks(pid)
            CF.CreatePlayer(pid).SetPlayerInteracteRange(before_interact_range)
            self._notify_player_tip(pid, 'RED', '手持基岩时不能与物理实体交互放置')
            return
        entity_data = self._store.get_entity(hit_entity_id)
        CF.CreateBlockInfo(pid).PlayerUseItemToPos(fallback_block_pos, 2, 0, facing)
        CF.CreatePlayer(pid).SetPlayerInteracteRange(before_interact_range)
        if not entity_data or not entity_data.shipyard_pos:
            self.cleanup_player_fallbacks(pid)
            return
        sx, sy, sz = entity_data.shipyard_pos
        slot_index = entity_data.slot_index
        read_min, read_max = self._get_shipyard_palette_range(entity_data, expand=1)
        CF.CreateGame(LID).AddTimer(0, self._on_fallback_post_check, {'pid': pid, 
           'hit_entity_id': hit_entity_id, 
           'dimension_id': dimension_id, 
           'hit_pos': hit_pos, 
           'remote_pos': remote_pos, 
           'item_name': item_name, 
           'slot_index': slot_index, 
           'read_min': read_min, 
           'read_max': read_max})
        return

    def _on_fallback_post_check(self, args):
        """fallback 后的延迟检查：对比调色板 + 刷新 + 搬运实体"""
        pid = args['pid']
        hit_entity_id = args['hit_entity_id']
        dimension_id = args['dimension_id']
        hit_pos = args['hit_pos']
        remote_pos = args.get('remote_pos')
        item_name = args['item_name']
        slot_index = args['slot_index']
        read_min = args['read_min']
        read_max = args['read_max']
        entity_data = self._store.get_entity(hit_entity_id)
        if not entity_data or not entity_data.shipyard_pos:
            self.cleanup_player_fallbacks(pid)
            return
        else:
            palette_now = CF.CreateBlock(LID).GetBlockPaletteBetweenPos(dimension_id, tuple(read_min), tuple(read_max), False)
            self._system.BroadcastToAllClient(events.S2C_PLAY_SOUND_PARTICLE, {'action': 'place', 
               'block_name': item_name, 
               'pos': hit_pos, 
               'pid': pid})
            new_entity_data = None
            for eid, edata in self._store.get_all_entities().items():
                if edata.slot_index == slot_index:
                    new_entity_data = edata
                    break

            if new_entity_data:
                self._save_and_move_shipyard_entities(new_entity_data, hit_pos, dimension_id, remote_pos)
            return

    def destroy_block_on_entity(self, args):
        """
        破坏物理实体上的方块
        通过 Raycast + Shipyard 空间射线检测定位方块 → 破坏 → 刷新
        @param args: {pid}
        """
        pid = args['pid']
        if not self._pool_ready:
            CF.CreateGame(pid).SetOneTipMessage(pid, serverApi.GenerateColor('RED') + '系统正在初始化中, 请稍后再试...')
            return
        dimension_id = CF.CreateDimension(pid).GetEntityDimensionId()
        ray_result = self._raycast_to_shipyard_block(pid, dimension_id)
        if not ray_result:
            return
        hit_entity_id = ray_result['hit_entity_id']
        remote_pos = ray_result['remote_pos']
        hit_pos = ray_result['hit_pos']
        entity_data = ray_result['entity_data']
        shipyard_args = {'pid': pid, 
           'hit_entity_id': hit_entity_id, 
           'remote_pos': remote_pos, 
           'hit_pos': hit_pos, 
           'dimension_id': dimension_id}
        sx, sy, sz = entity_data.shipyard_pos
        rs = entity_data.region_size if entity_data.region_size else (1, 1, 1)
        chunk_comp = CF.CreateChunkSource(LID)
        callback = lambda data: self._on_destroy_chunks_loaded(data, shipyard_args)
        chunk_comp.DoTaskOnChunkAsync(dimension_id, (
         sx, 0, sz), (
         sx + rs[0], 0, sz + rs[2]), callback)
        return

    def _on_destroy_chunks_loaded(self, data, args):
        """DoTaskOnChunkAsync 回调：区块加载完成后执行破坏操作
        新逻辑：
        1. 操作前获取调色板快照
        2. 执行 PlayerDestoryBlock
        3. 操作后获取调色板快照
        4. 对比：有变化→刷新；无变化→仅播放声音
        5. 无论是否变化，structure save 实体 + place 搬运掉落物
        """
        if data.get('code') != 1:
            print '[ValkyrienBE] destroy_block_on_entity: chunk loading failed'
            return
        else:
            hit_entity_id = args['hit_entity_id']
            entity_data = self._store.get_entity(hit_entity_id)
            if not entity_data or not entity_data.shipyard_pos:
                return
            pid = args['pid']
            remote_pos = args['remote_pos']
            hit_pos = args['hit_pos']
            dimension_id = args['dimension_id']
            sx, sy, sz = entity_data.shipyard_pos
            slot_index = entity_data.slot_index
            area_key = ('vbe_area_{}').format(slot_index)
            area_comp = CF.CreateChunkSource(LID)
            all_area_keys = area_comp.GetAllAreaKeys()
            if area_key not in all_area_keys:
                area_comp.SetAddArea(area_key, dimension_id, (
                 sx - SHIPYARD_PADDING, 0, sz - SHIPYARD_PADDING), (
                 sx + SHIPYARD_PADDING, 0, sz + SHIPYARD_PADDING))
            block_dict = CF.CreateBlockInfo(LID).GetBlockNew(remote_pos, dimension_id)
            block_name = block_dict.get('name', '') if block_dict else ''
            block_aux = block_dict.get('aux', 0) if block_dict else 0
            read_min, read_max = self._get_shipyard_palette_range(entity_data, expand=0)
            palette_before = CF.CreateBlock(LID).GetBlockPaletteBetweenPos(dimension_id, read_min, read_max, False)
            before_data = palette_before.SerializeBlockPalette() if palette_before else None
            block_info_comp = CF.CreateBlockInfo(pid)
            block_info_comp.PlayerDestoryBlock(remote_pos, 1, True)
            palette_after = CF.CreateBlock(LID).GetBlockPaletteBetweenPos(dimension_id, read_min, read_max, False)
            after_data = palette_after.SerializeBlockPalette() if palette_after else None
            has_change = False
            if before_data and after_data:
                has_change = self._compare_palettes(before_data, after_data)
            self._system.BroadcastToAllClient(events.S2C_PLAY_SOUND_PARTICLE, {'action': 'destroy', 
               'block_name': block_name, 
               'block_aux': block_aux, 
               'pos': hit_pos, 
               'pid': pid})
            if has_change:
                self._start_refresh_cycle(hit_entity_id, pid)
            new_entity_data = None
            for eid, edata in self._store.get_all_entities().items():
                if edata.slot_index == slot_index:
                    new_entity_data = edata
                    break

            if new_entity_data:
                self._save_and_move_shipyard_entities(new_entity_data, hit_pos, dimension_id, remote_pos)
            return

    def on_entity_added(self, args):
        """
        AddEntityServerEvent 回调
        为自定义物理方块实体添加物理特性（支持 userData）
        """
        entity_id = args.get('id')
        engine_type = args.get('engineTypeStr', '')
        if engine_type != PHYS_ENTITY_TYPE:
            return
        else:
            rot_comp = CF.CreateRot(entity_id)
            rot_comp.SetRot((0, 0))
            phys_comp = CF.CreatePhysx(entity_id)
            phys_comp.CreatePxActor()
            pending = self._store.pop_pending_entity()
            if pending is not None:
                aabb_list = pending.get('aabbList', [])
                for item in aabb_list:
                    if len(item) >= 6:
                        local_center, half_extents, sf, df, r, ud = item
                    else:
                        local_center, half_extents, sf, df, r = item
                        ud = None
                    phys_comp.AddBoxGeometry(local_center, half_extents[0], half_extents[1], half_extents[2], sf, df, r, _EVENT_MASK, userData=ud)

            elif self._store.has_entity(entity_id):
                entity_data = self._store.get_entity(entity_id)
                for item in entity_data.aabb_list:
                    if len(item) >= 6:
                        local_center, half_extents, sf, df, r, ud = item
                    else:
                        local_center, half_extents, sf, df, r = item
                        ud = None
                    phys_comp.AddBoxGeometry(local_center, half_extents[0], half_extents[1], half_extents[2], sf, df, r, _EVENT_MASK, userData=ud)

            else:
                self.reload_entity_from_extra_data(entity_id, phys_comp)
            ai_comp = CF.CreateControlAi(entity_id)
            ai_comp.SetBlockControlAi(False)
            return

    def _mark_balloon_ready(self, args):
        """AddTimer 回调：将实体加入气球浮力就绪集合（创建后下一帧生效）"""
        entity_id = args.get('entityId')
        if entity_id and self._store.has_entity(entity_id):
            self._balloon_ready_set.add(entity_id)
        return

    def _schedule_balloon_ready(self, entity_id):
        """在下一帧将实体标记为气球浮力就绪"""
        CF.CreateGame(LID).AddTimer(1, self._mark_balloon_ready, {'entityId': entity_id})
        return

    def _update_balloon_forces(self):
        """
        每 tick 对含气球方块的物理实体施加浮力，抵消重力。
        仅处理已在 _balloon_ready_set 中的实体（创建后下一帧才加入），
        避免在实体创建当帧调用 AddForce 导致接口失效。
        实体默认重力因子 ENTITY_GRAVITY = -0.08（每帧向下速度变化量）。
        每个气球承载 BALLOON_MASS_PER_BLOCK kg 的质量。
        浮力 = |ENTITY_GRAVITY| * balloon_count * BALLOON_MASS_PER_BLOCK / total_mass
        当 balloon_count * BALLOON_MASS_PER_BLOCK == total_mass 时，浮力恰好抵消重力，实体悬浮。
        可选高度衰减：高度越高，浮力越小。
        """
        if not self._balloon_ready_set:
            return
        self._balloon_ready_set = self._balloon_ready_set & set(self._store.get_all_entities().keys())
        for entity_id in list(self._balloon_ready_set):
            entity_data = self._store.get_entity(entity_id)
            if not entity_data or entity_data.balloon_count <= 0:
                continue
            total_mass = entity_data.total_mass
            if total_mass <= 0:
                continue
            supported_mass = entity_data.balloon_count * BALLOON_MASS_PER_BLOCK
            lift_ratio = supported_mass - total_mass
            force_y = abs(ENTITY_GRAVITY) * 1
            if BALLOON_HEIGHT_DECAY_ENABLED:
                pos_comp = CF.CreatePos(entity_id)
                pos = pos_comp.GetPos()
                if pos:
                    y = pos[1]
                    if y >= BALLOON_MAX_HEIGHT:
                        continue
                    elif y > BALLOON_MIN_HEIGHT:
                        decay = 1.0 - (y - BALLOON_MIN_HEIGHT - (BALLOON_MAX_HEIGHT - BALLOON_MIN_HEIGHT))
                        force_y *= decay
            phys_comp = CF.CreatePhysx(entity_id)
            if phys_comp:
                phys_comp.AddForce((0.0, 10, 0.0), PxForceMode.eACCELERATION)

        return

    def _update_fallback_blocks(self):
        """
        每 tick 同步备用方块 NBT 数据到 Shipyard 位置。
        当 EntityUseItemToPos 在 Shipyard 未能成功放置方块时，
        会在玩家脚下 y=-64 创建代理方块，此处将代理方块的 NBT 复制到 Shipyard。
        同时监测玩家整数 XZ 坐标是否变化，变化时清理备用方块。
        """
        block_info = CF.CreateBlockInfo(LID)
        for pid, fb in list(self._store.get_all_fallback_blocks().items()):
            player_pos = CF.CreatePos(pid).GetPos()
            if player_pos:
                cur_x = int(math.floor(player_pos[0]))
                cur_z = int(math.floor(player_pos[2]))
                fb_pos = fb['fallback_pos']
                if fb_pos[0] != cur_x or fb_pos[2] != cur_z:
                    self.cleanup_player_fallbacks(pid)
                    continue
            fb_pos = fb['fallback_pos']
            ship_pos = fb['shipyard_pos']
            dim_id = fb['dim_id']
            nbt = block_info.GetBlockEntityData(dim_id, fb_pos)
            if nbt:
                block_info.SetBlockEntityData(dim_id, ship_pos, nbt)

        return

    def cleanup_player_fallbacks(self, pid):
        """
        清理指定玩家的备用方块：还原为基岩并移除跟踪。
        在玩家退出游戏或退出交互模式时调用。
        同时还原 -63 层（之前放置的空气）为基岩。
        """
        fb = self._store.get_fallback_block(pid)
        if fb:
            block_info = CF.CreateBlockInfo(LID)
            fb_pos = fb['fallback_pos']
            block_info.SetBlockNew(fb_pos, {'name': 'minecraft:bedrock', 'aux': 0}, 0, fb['dim_id'], True)
            block_info.SetBlockNew((
             fb_pos[0], -63, fb_pos[2]), {'name': 'minecraft:bedrock', 'aux': 0}, 0, fb['dim_id'], True)
            self._store.remove_fallback_block(pid)
        return

    def restore_blocks(self):
        """Destroy 时调用：遍历所有物理实体，将方块还原到世界"""
        for entity_id, entity_data in list(self._store.get_all_entities().items()):
            self._restore_blocks(entity_id, entity_data)

        return

    @staticmethod
    def _snap_floor(val):
        """Floor 取整，当值接近整数时吸附到最近整数，避免浮点漂移导致偏移一格"""
        r = round(val)
        if abs(val - r) < 0.2:
            return int(r)
        return int(math.floor(val))

    def _restore_blocks(self, entity_id, entity_data):
        """
        根据实体当前位姿，使用 structure 指令还原方块到世界
        1. 从 Shipyard 重新保存 structure 到内存（确保包含最新修改）
        2. 使用 PlaceStructure 放置到还原位置（含旋转）
        3. 如有 Shipyard：清空远处方块、释放常加载和槽位
        若无 structure 则回退到调色板还原。
        """
        current_pos = CF.CreatePos(entity_id).GetPos()
        if not current_pos:
            return
        else:
            dim_id = entity_data.dimension_id
            offset = entity_data.palette_offset
            phys_comp = CF.CreatePhysx(entity_id)
            q_tuple = phys_comp.GetQuaternion()
            if q_tuple:
                q = Quaternion(q_tuple)
                euler = q.EulerAngles()
                y_rot = euler[1]
            else:
                y_rot = 0.0
            snapped_y_rot = int(round(y_rot - 90.0)) * 90
            snapped_y_rot = snapped_y_rot % 360
            if snapped_y_rot != 0:
                rot_q = Quaternion.Euler(0, snapped_y_rot, 0)
                rotated_offset = rot_q * Vector3(offset[0], offset[1], offset[2])
                offset_x = rotated_offset[0]
                offset_y = rotated_offset[1]
                offset_z = rotated_offset[2]
            else:
                offset_x, offset_y, offset_z = offset
            restore_x = self._snap_floor(current_pos[0] + offset_x)
            restore_y = self._snap_floor(current_pos[1] + offset_y)
            restore_z = self._snap_floor(current_pos[2] + offset_z)
            restore_pos = (restore_x, restore_y, restore_z)
            struct_name = entity_data.structure_name
            if struct_name and entity_data.shipyard_pos:
                sx, sy, sz = entity_data.shipyard_pos
                if entity_data.region_size:
                    rs = entity_data.region_size
                    sx2, sy2, sz2 = sx + rs[0] - 1, sy + rs[1] - 1, sz + rs[2] - 1
                else:
                    sx2, sy2, sz2 = sx, sy, sz
                cmd_comp = CF.CreateCommand(LID)
                cmd_comp.SetCommand(('/structure save {} {} {} {} {} {} {} memory').format(struct_name, sx, sy, sz, sx2, sy2, sz2))
                rotation_idx = snapped_y_rot // 90 % 4
                game_comp = CF.CreateGame(LID)
                game_comp.PlaceStructure(None, restore_pos, struct_name, dim_id, rotation_idx, animationMode=0, animationTime=0, inculdeEntity=False, removeBlock=False, mirrorMode=0, integrity=100, seed=-1)
            else:
                block_comp = CF.CreateBlock(LID)
                palette = block_comp.GetBlankBlockPalette()
                palette.DeserializeBlockPalette(entity_data.palette_data)
                result = block_comp.SetBlockByBlockPalette(palette, dim_id, restore_pos, snapped_y_rot, 0)
                if not result:
                    print ('[ValkyrienBE] Failed to restore blocks at ({}, {}, {}) rot={}').format(restore_x, restore_y, restore_z, snapped_y_rot)
            if entity_data.shipyard_pos:
                sx, sy, sz = entity_data.shipyard_pos
                if entity_data.region_size:
                    rs = entity_data.region_size
                    sx2 = sx + rs[0] - 1
                    sy2 = sy + rs[1] - 1
                    sz2 = sz + rs[2] - 1
                else:
                    sx2, sy2, sz2 = sx, sy, sz
                cmd_comp = CF.CreateCommand(LID)
                cmd_comp.SetCommand(('/fill {} {} {} {} {} {} air').format(sx, sy, sz, sx2, sy2, sz2))
                if entity_data.shipyard_area_key:
                    chunk_comp = CF.CreateChunkSource(LID)
                    chunk_comp.DeleteArea(entity_data.shipyard_area_key)
                if entity_data.slot_index >= 0:
                    self._store.release_shipyard_slot(entity_data.slot_index)
                    self._kill_slot_tick_entity(entity_data.slot_index)
            return

    def on_health_change(self, args):
        if args['entityId'] in self._store.get_all_entities():
            if args['to'] <= 0.1:
                args['cancel'] = True
        return

