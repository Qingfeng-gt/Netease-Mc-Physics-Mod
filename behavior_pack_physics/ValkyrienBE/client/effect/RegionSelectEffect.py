# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
# Embedded file name: ValkyrienBE/client/effect/RegionSelectEffect.py
"""
区域选取特效类
给定两个角坐标(fromPos, toPos), 对区域外围6个面生成序列帧特效框选。
"""
import mod.client.extraClientApi as clientApi
CF = clientApi.GetEngineCompFactory()
_EFFECT_PATH = 'effects/block_select_frame.json'
_E = 0.501

class RegionSelectEffect(object):
    """
    区域选取特效管理器

    用法:
        effect = RegionSelectEffect(clientSystem)
        effect.show_region((0, 64, 0), (5, 66, 5))
        effect.hide_all()
        effect.destroy()
    """

    def __init__(self, client_system):
        """
        @param client_system: 客户端系统实例
        """
        self._client_system = client_system
        self._frame_ids = []
        self._current_from = None
        self._current_to = None
        return

    def show_region(self, from_pos, to_pos):
        """
        显示区域选取特效, 框选从 from_pos 到 to_pos 的整个区域
        @param from_pos: 起点方块坐标 (int, int, int)
        @param to_pos: 终点方块坐标 (int, int, int)
        @return: bool
        """
        min_x = min(int(from_pos[0]), int(to_pos[0]))
        min_y = min(int(from_pos[1]), int(to_pos[1]))
        min_z = min(int(from_pos[2]), int(to_pos[2]))
        max_x = max(int(from_pos[0]), int(to_pos[0]))
        max_y = max(int(from_pos[1]), int(to_pos[1]))
        max_z = max(int(from_pos[2]), int(to_pos[2]))
        new_from = (
         min_x, min_y, min_z)
        new_to = (max_x, max_y, max_z)
        if self._current_from == new_from and self._current_to == new_to and self._frame_ids:
            return True
        self.hide_all()
        self._current_from = new_from
        self._current_to = new_to
        size_x = max_x - min_x + 1
        size_y = max_y - min_y + 1
        size_z = max_z - min_z + 1
        cx = min_x + max_x - 2.0 + 0.5
        cy = min_y + max_y - 2.0 + 0.5
        cz = min_z + max_z - 2.0 + 0.5
        self._create_face((cx, max_y + _E + 0.5, cz), (90, 0, 0), (size_x * 0.5, size_z * 0.5, 0.5))
        self._create_face((cx, min_y - _E + 0.5, cz), (90, 0, 0), (size_x * 0.5, size_z * 0.5, 0.5))
        self._create_face((cx, cy, max_z + _E + 0.5), (0, 0, 0), (size_x * 0.5, size_y * 0.5, 0.5))
        self._create_face((cx, cy, min_z - _E + 0.5), (0, 0, 0), (size_x * 0.5, size_y * 0.5, 0.5))
        self._create_face((max_x + _E + 0.5, cy, cz), (0, 90, 0), (size_z * 0.5, size_y * 0.5, 0.5))
        self._create_face((min_x - _E + 0.5, cy, cz), (0, 90, 0), (size_z * 0.5, size_y * 0.5, 0.5))
        return len(self._frame_ids) > 0

    def _create_face(self, pos, rot, scale=None):
        """创建一个特效面"""
        frame_id = self._client_system.CreateEngineSfxFromEditor(_EFFECT_PATH, pos, rot)
        if frame_id is None:
            return
        else:
            control_comp = CF.CreateFrameAniControl(frame_id)
            control_comp.SetLoop(True)
            control_comp.SetFaceCamera(False)
            if scale:
                trans_comp = CF.CreateFrameAniTrans(frame_id)
                trans_comp.SetScale(scale)
            control_comp.Play()
            self._frame_ids.append(frame_id)
            return

    def hide_all(self):
        """隐藏所有区域选取特效"""
        for frame_id in self._frame_ids:
            self._client_system.DestroyEntity(frame_id)

        self._frame_ids = []
        self._current_from = None
        self._current_to = None
        return

    def get_region(self):
        """
        获取当前选区的两个角坐标
        @return: (fromPos, toPos) 或 None
        """
        if self._current_from is not None and self._current_to is not None:
            return (self._current_from, self._current_to)
        else:
            return

    def is_showing(self):
        return len(self._frame_ids) > 0

    def destroy(self):
        """销毁所有特效并释放资源"""
        self.hide_all()
        return


