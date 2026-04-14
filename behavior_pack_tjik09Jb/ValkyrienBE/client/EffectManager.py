# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
# Embedded file name: ValkyrienBE/client/EffectManager.py
"""
特效管理器
负责：方块选取特效和区域选取特效的管理
"""
from ValkyrienBE.client.effect.BlockSelectEffect import BlockSelectEffect
from ValkyrienBE.client.effect.RegionSelectEffect import RegionSelectEffect

class EffectManager(object):
    """特效管理器"""

    def __init__(self, system):
        """
        @param system: ValkyrienBEClientSystem 实例
        """
        self._system = system
        self.block_select = BlockSelectEffect(system)
        self.region_select = RegionSelectEffect(system)
        return

    def destroy(self):
        """销毁所有特效"""
        self.block_select.destroy()
        self.region_select.destroy()
        return


