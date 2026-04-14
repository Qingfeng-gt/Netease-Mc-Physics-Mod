# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
# Embedded file name: ValkyrienBE/client/effect/BlockSelectEffect.py
"""
方块选取特效类
输入方块坐标, 通过序列帧生成白色特效框选住方块。
使用6个序列帧平面分别贴在方块6个面上, 组成立体选取框效果。
"""
import mod.client.extraClientApi as clientApi
CF = clientApi.GetEngineCompFactory()
_EFFECT_PATH = 'effects/block_select_frame.json'
_E = 0.501
_FACE_CONFIGS = (
 (
  (
   0, _E, 0), (90, 0, 0)),
 (
  (
   0, -_E, 0), (90, 0, 0)),
 (
  (
   _E, 0, 0), (0, 90, 0)),
 (
  (
   -_E, 0, 0), (0, 90, 0)),
 (
  (
   0, 0, _E), (0, 0, 0)),
 (
  (
   0, 0, -_E), (0, 0, 0)))

class BlockSelectEffect(object):
    """
    方块选取特效管理器

    用法:
        effect = BlockSelectEffect(clientSystem)
        effect.show((10, 64, 20))
        effect.hide((10, 64, 20))
        effect.switchTo((12, 64, 22))
        effect.hideAll()
        effect.destroy()
    """

    def __init__(self, client_system):
        """
        @param client_system: 客户端系统实例 (需有 CreateEngineSfxFromEditor/DestroyEntity 方法)
        """
        self._client_system = client_system
        self._effect_map = {}
        return

    def show(self, block_pos):
        """
        在指定方块坐标显示选取特效
        @param block_pos: (int, int, int)
        @return: bool
        """
        key = (
         int(block_pos[0]), int(block_pos[1]), int(block_pos[2]))
        if key in self._effect_map:
            return True
        else:
            center_pos = (
             key[0] + 0.5, key[1] + 0.5, key[2] + 0.5)
            frame_ids = []
            for offset, rot in _FACE_CONFIGS:
                face_pos = (
                 center_pos[0] + offset[0],
                 center_pos[1] + offset[1],
                 center_pos[2] + offset[2])
                frame_id = self._client_system.CreateEngineSfxFromEditor(_EFFECT_PATH, face_pos, rot)
                if frame_id is None:
                    continue
                control_comp = CF.CreateFrameAniControl(frame_id)
                control_comp.SetLoop(True)
                control_comp.SetFaceCamera(False)
                control_comp.Play()
                frame_ids.append(frame_id)

            if not frame_ids:
                return False
            self._effect_map[key] = frame_ids
            return True

    def hide(self, block_pos):
        """隐藏指定方块坐标的选取特效"""
        key = (
         int(block_pos[0]), int(block_pos[1]), int(block_pos[2]))
        frame_ids = self._effect_map.pop(key, None)
        if frame_ids is None:
            return
        else:
            for frame_id in frame_ids:
                self._client_system.DestroyEntity(frame_id)

            return

    def hide_all(self):
        """隐藏所有方块选取特效"""
        for frame_ids in self._effect_map.values():
            for frame_id in frame_ids:
                self._client_system.DestroyEntity(frame_id)

        self._effect_map.clear()
        return

    def switch_to(self, block_pos):
        """切换选取到指定方块（先清除所有旧特效, 再在新位置显示）"""
        self.hide_all()
        return self.show(block_pos)

    def is_showing(self, block_pos):
        """判断指定方块是否正在显示选取特效"""
        key = (
         int(block_pos[0]), int(block_pos[1]), int(block_pos[2]))
        return key in self._effect_map

    def get_showing_positions(self):
        """获取当前所有正在显示选取特效的方块坐标"""
        return list(self._effect_map.keys())

    def destroy(self):
        """销毁所有特效并释放资源"""
        self.hide_all()
        return

