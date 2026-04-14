# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
# Embedded file name: ValkyrienBE/common/data_models.py
"""
数据模型类
用于结构化存储物理实体、捉捕状态等数据
Python 2.7 兼容（不使用 dataclass）
"""

class PhysicsEntityData(object):
    """物理实体数据"""

    def __init__(self, palette_data, dimension_id, palette_offset, aabb_list, palette_name, is_region=False, region_size=None, render_offset=None, collider_strategy=None, total_mass=0.0, shipyard_pos=None, structure_name=None, original_min_pos=None, original_max_pos=None, shipyard_area_key=None, slot_index=-1, balloon_count=0):
        """
        @param palette_data: dict 方块调色板序列化数据
        @param dimension_id: int 维度 ID
        @param palette_offset: tuple 调色板偏移 (x, y, z)
        @param aabb_list: list[(localCenter, halfExtents, sf, df, restitution, userData)] 碰撞盒列表
                          userData 格式: "mass&lx,ly,lz"
        @param palette_name: str 调色板名称
        @param is_region: bool 是否为区域物理化
        @param region_size: tuple|None 区域尺寸 (sizeX, sizeY, sizeZ)
        @param render_offset: tuple|None 渲染偏移 (x, y, z)
        @param collider_strategy: str|None 碰撞盒策略标记
        @param total_mass: float 总质量 (kg)
        @param shipyard_pos: tuple|None Shipyard 远端放置原点 (x, y, z)
        @param structure_name: str|None structure 保存名称 (如 "vbe:ship_0")
        @param original_min_pos: tuple|None 原始方块区域最小坐标
        @param original_max_pos: tuple|None 原始方块区域最大坐标
        @param shipyard_area_key: str|None SetAddArea 返回的 key
        @param slot_index: int Shipyard 槽位索引 (-1 表示未分配)
        """
        self.palette_data = palette_data
        self.dimension_id = dimension_id
        self.palette_offset = palette_offset
        self.aabb_list = aabb_list
        self.palette_name = palette_name
        self.is_region = is_region
        self.region_size = region_size
        self.render_offset = render_offset
        self.collider_strategy = collider_strategy
        self.total_mass = total_mass
        self.shipyard_pos = shipyard_pos
        self.structure_name = structure_name
        self.original_min_pos = original_min_pos
        self.original_max_pos = original_max_pos
        self.shipyard_area_key = shipyard_area_key
        self.slot_index = slot_index
        self.balloon_count = balloon_count
        return

    def to_save_dict(self):
        """转换为可序列化的字典（用于 ExtraData 存储）"""
        serialized_aabb = []
        for item in self.aabb_list:
            if len(item) >= 6:
                lc, he, sf, df, r, ud = item
                serialized_aabb.append([list(lc), list(he), sf, df, r, ud])
            else:
                lc, he, sf, df, r = item
                serialized_aabb.append([list(lc), list(he), sf, df, r, ''])

        result = {'paletteData': (self.palette_data), 
           'dimensionId': (self.dimension_id), 
           'paletteOffset': (list(self.palette_offset)), 
           'aabbList': serialized_aabb, 
           'paletteName': (self.palette_name), 
           'isRegion': (self.is_region), 
           'regionSize': (list(self.region_size) if self.region_size else None), 
           'renderOffset': (list(self.render_offset) if self.render_offset else None), 
           'colliderStrategy': (self.collider_strategy), 
           'totalMass': (self.total_mass), 
           'shipyardPos': (list(self.shipyard_pos) if self.shipyard_pos else None), 
           'structureName': (self.structure_name), 
           'originalMinPos': (list(self.original_min_pos) if self.original_min_pos else None), 
           'originalMaxPos': (list(self.original_max_pos) if self.original_max_pos else None), 
           'slotIndex': (self.slot_index), 
           'balloonCount': (self.balloon_count)}
        return result

    @staticmethod
    def from_save_dict(data):
        """从序列化字典恢复（向后兼容旧格式）"""
        aabb_list = []
        for item in data['aabbList']:
            if len(item) >= 6:
                aabb_list.append((tuple(item[0]), tuple(item[1]), item[2], item[3], item[4], item[5]))
            elif len(item) >= 5:
                aabb_list.append((tuple(item[0]), tuple(item[1]), item[2], item[3], item[4], ''))
            else:
                aabb_list.append((tuple(item[0]), tuple(item[1]), 0.05, 0.05, 0.0, ''))

        return PhysicsEntityData(palette_data=data['paletteData'], dimension_id=data['dimensionId'], palette_offset=tuple(data['paletteOffset']), aabb_list=aabb_list, palette_name=data['paletteName'], is_region=data.get('isRegion', False), region_size=tuple(data['regionSize']) if data.get('regionSize') else None, render_offset=tuple(data['renderOffset']) if data.get('renderOffset') else None, collider_strategy=data.get('colliderStrategy'), total_mass=data.get('totalMass', 0.0), shipyard_pos=tuple(data['shipyardPos']) if data.get('shipyardPos') else None, structure_name=data.get('structureName'), original_min_pos=tuple(data['originalMinPos']) if data.get('originalMinPos') else None, original_max_pos=tuple(data['originalMaxPos']) if data.get('originalMaxPos') else None, slot_index=data.get('slotIndex', -1), balloon_count=data.get('balloonCount', 0))

    def to_render_dict(self, entity_id, carry_player=''):
        """转换为客户端渲染所需的字典"""
        return {'entityId': entity_id, 
           'palette': (self.palette_data), 
           'palette_name': (self.palette_name), 
           'carry_player': carry_player, 
           'isRegion': (self.is_region), 
           'regionSize': (self.region_size), 
           'renderOffset': (self.render_offset), 
           'colliderStrategy': (self.collider_strategy)}


class CatchState(object):
    """捉捕状态数据"""

    def __init__(self, entity_id, prev_pos, last_pos, hold_dist, target_quat=None):
        """
        @param entity_id: str 被捉捕的实体 ID
        @param prev_pos: tuple 上一帧位置
        @param last_pos: tuple 当前帧位置
        @param hold_dist: float 持有距离
        @param target_quat: tuple|None 目标旋转四元数 (x, y, z, w)
        """
        self.entity_id = entity_id
        self.prev_pos = prev_pos
        self.last_pos = last_pos
        self.hold_dist = hold_dist
        self.target_quat = target_quat
        return

