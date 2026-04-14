# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
# Embedded file name: ValkyrienBE/common/constants.py
"""
全局常量定义
物理状态枚举、物品名、配置常量等
"""

class PhysMode:
    """物理操作模式枚举"""
    SINGLE = 0
    REGION = 1
    REMOVE = 2
    CATCH = 3
    SUCK = 4
    SPRAY = 5
    REMOVE_ALL = 6
    INTERACT = 7
    NAMES = {0: '物理化(单个)', 
       1: '物理化(批量)', 
       2: '去物理化', 
       3: '捉捕', 
       4: '磁吸', 
       5: '喷射', 
       6: '一键删除', 
       7: '交互'}
    COUNT = 8

    @staticmethod
    def get_name(mode):
        """获取模式名称"""
        return PhysMode.NAMES.get(mode, '未知')


PHYS_ITEM_NAME = 'phy_stimulate:stick'
PHYS_ENTITY_TYPE = 'physstimu:xiaobo_block_phys'
STATIC_FRICTION = 0.05
DYNAMIC_FRICTION = 0.05
RESTITUTION = 0.0
CATCH_MIN_DIST = 2.0
CATCH_MAX_DIST = 15.0
CATCH_THROW_SCALE = 20.0
CATCH_MAX_SPEED = 30.0
SUCK_RANGE = 20.0
SUCK_HOLD_DIST = 13
SUCK_SPEED = 3
SUCK_GRAVITY_COMP = 0.5
SPRAY_MAX_COUNT = 1000
SPRAY_SPEED = 15.0
SPRAY_SPREAD = 0.15
SPRAY_SPAWN_DIST = 2.0
PLAYER_MASS = 3
MIN_PUSH = 0.5
MASS_NORMALIZE = 1000.0
EXPLOSION_RADIUS = 16.0
EXPLOSION_FORCE = 100
EXPLOSION_UP_BIAS = 0.4
MAX_REGION_BLOCKS = 12800
COLLIDER_STRATEGY_PER_BLOCK = 'per_block'
COLLIDER_STRATEGY_MERGED = 'merged'
COLLIDER_STRATEGY_AUTO = 'auto'
DEFAULT_COLLIDER_STRATEGY = COLLIDER_STRATEGY_PER_BLOCK
UNSUPPORTED_PHYSICAL_BLOCKS = frozenset([
 'minecraft:bedrock'])
CONCRETE_COLORS = [
 25, 26, 27, 28, 29, 30, 
 31, 32, 33, 34, 35, 36, 
 37, 38, 39, 
 40]
SHIPYARD_BASE_X = 100000
SHIPYARD_BASE_Z = 100000
SHIPYARD_Y = 64
SHIPYARD_SLOT_SIZE = 80
SHIPYARD_GRID_WIDTH = 100
SHIPYARD_PADDING = 100
SHIPYARD_STRUCT_PREFIX = 'vbe'
PHYS_HOME_SIZE = 64
PHYS_HOME_STRUCTURE = 'valkyrien:phys_home'
BALLOON_BLOCK_NAME = 'valkyrien_be:valkyrien_be_balloon'
ENTITY_GRAVITY = -0.08
BALLOON_MASS_PER_BLOCK = 5000.0
BALLOON_HEIGHT_DECAY_ENABLED = True
BALLOON_MIN_HEIGHT = 64.0
BALLOON_MAX_HEIGHT = 400.0
