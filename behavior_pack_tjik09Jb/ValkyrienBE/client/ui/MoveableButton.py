# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
# Embedded file name: ValkyrienBE/client/ui/MoveableButton.py
"""
可拖动按钮基类
ScreenNode 的子类，支持通过触摸拖动来移动HUD按钮位置，
并自动避免与原生按钮和其他可拖动按钮碰撞和内嵌。
"""
import mod.client.extraClientApi as clientApi
ScreenNode = clientApi.GetScreenNodeCls()
CF = clientApi.GetEngineCompFactory()
LVID = clientApi.GetLevelId()
PID = clientApi.GetLocalPlayerId()
BP = 'variables_button_mappings_and_controls/safezone_screen_matrix/inner_matrix/safezone_screen_panel/root_screen_panel'
EN, ESN = clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName()
import_ = globals()['__builtins__']['__import__']
Gui = import_('gui')
GetOption = import_('setting', fromlist=['get_option']).get_option
Event = import_('common', fromlist=['eventUtil']).eventUtil.instance
GetConfigData = CF.CreateConfigClient(LVID).GetConfigData
SetConfigData = CF.CreateConfigClient(LVID).SetConfigData

def _get_nearest_pos(pos_list, pos):
    return min(pos_list, key=(lambda x: (x[0] - pos[0]) ** 2 + (x[1] - pos[1]) ** 2))


class MoveableButton(ScreenNode):
    """
    可拖动按钮基类

    使用 AddMoveableButton 注册可拖动按钮后，长按即可拖动。
    按钮位置自动持久化（通过 GetConfigData/SetConfigData），
    并在屏幕尺寸变化时自动重新校正位置。
    """

    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        self._move_timer = 0
        self._temp_pos = ()
        self._temp_offset = ()
        self._last_pos = ()
        self._delay_func = []
        self._moveable_widgets = {}
        self._initial_positions = {}
        self._origin_collision_box = []
        self._collision_box = []
        return

    def GetSavedButtonPos(self, custom_key, path):
        return GetConfigData(custom_key, True).get(path)

    def SetSavedButtonPos(self, custom_key, path, pos):
        saved_pos = GetConfigData(custom_key, True)
        saved_pos[path] = pos
        SetConfigData(custom_key, saved_pos, True)
        return

    def AddMoveableButton(self, path, callback, custom_key, move_parent=False):
        """
        注册可拖动按钮
        @param path: 按钮UI路径
        @param callback: 短按松手后触发的回调
        @param custom_key: 持久化存储键名
        @param move_parent: 是否移动父控件
        """
        real_path = path.rsplit('/', 1)[0] if move_parent else path
        self._moveable_widgets[real_path] = custom_key
        saved_pos = tuple(self.GetSavedButtonPos(custom_key, real_path) or ())
        if saved_pos:
            self.SetPosition(real_path, saved_pos)
            self._delay_func.append((self._InitCollisionBox, real_path))
            self._delay_func.append((self._CorrectButtonPos, real_path))

        def _on_move_button(args):
            touch_event = args['TouchEvent']
            if touch_event == 0 or touch_event == 3:
                self._last_pos = ()
                now_pos = self.GetGlobalPosition(real_path)
                if self._move_timer > 0 or now_pos == self._temp_pos:
                    self._move_timer = 0
                    callback(args)
                else:
                    self._CorrectPosAndSave(real_path)
            elif touch_event == 1:
                self._move_timer = 30
                self._temp_pos = self.GetGlobalPosition(real_path)
                self._temp_offset = (
                 args['TouchPosX'] - self._temp_pos[0],
                 args['TouchPosY'] - self._temp_pos[1])
                self._last_pos = self._temp_pos
                self._InitOriginCollisionBox()
                self._InitCollisionBox(real_path)
            elif self._move_timer == 0 and touch_event == 4:
                pos = (args['TouchPosX'] - self._temp_offset[0],
                 args['TouchPosY'] - self._temp_offset[1])
                self._CorrectButtonPos(real_path, pos)
            elif self._move_timer > 0 and touch_event == 6:
                self._move_timer = 32767
            return

        self.AddTouchEventHandler(path, _on_move_button, {'isSwallow': True})
        return

    def _InitOriginCollisionBox(self):
        self._origin_collision_box = []
        controls = [
         'pause', 'chat', 'fold_menu', 'emote']
        if GetOption('ctrl_camera_view'):
            controls.append('camera_view')
        if GetOption('ctrl_force_sprint'):
            controls.append('walkstate')
        new_controls = ('sneak_new_controls', 'jump_new_controls', 'sprint', 'default_move_stick_area')
        control_mode = GetOption('ctrl_interactionModel', 2)
        if control_mode == 0:
            controls += new_controls
        elif control_mode == 1:
            controls += new_controls + ('destroy_or_attack', 'build_or_interact')
        elif control_mode == 2:
            controls += ('sneak', 'jump', 'ascend', 'descend')
            move_area = [-13, -13, 13, 13]
            for i, name in enumerate(('move_left', 'move_up', 'move_right', 'move_down')):
                move_area[i] += clientApi.GetOriginAreaOffset('binding.area.' + name)[i]

            self._origin_collision_box.append(tuple(move_area))
        self._origin_collision_box += filter((lambda x: x != (0.0, 0.0, 0.0, 0.0)), (clientApi.GetOriginAreaOffset('binding.area.' + n) for n in controls))
        offset = Gui.get_global_position(self.screen_name, BP)
        size = Gui.get_size(self.screen_name, BP)
        self._origin_collision_box += (
         (
          -32768, -32768, 32767, offset[1]),
         (
          -32768, -32768, offset[0], 32767),
         (
          -32768, offset[1] + size[1], 32767, 32767),
         (
          offset[0] + size[0], -32768, 32767, 32767))
        return

    def _InitCollisionBox(self, button_path):
        collision_box = []
        x, y = self.GetSize(button_path)
        x, y = x - 2, y - 2
        for path in self._moveable_widgets:
            if path == button_path:
                continue
            pos = self.GetGlobalPosition(path)
            size = self.GetSize(path)
            collision_box.append((pos[0], pos[1], pos[0] + size[0], pos[1] + size[1]))

        self._collision_box = tuple((c[0] - x, c[1] - y, c[2] + x, c[3] + y) for c in collision_box + self._origin_collision_box)
        return

    def _CorrectButtonPos(self, path, pos=None):
        if not pos:
            pos = self.GetGlobalPosition(path)
        size = self.GetSize(path)
        hs0, hs1 = size[0] - 2, size[1] - 2
        pos = (pos[0] + hs0, pos[1] + hs1)
        if any(c[0] < pos[0] < c[2] and c[1] < pos[1] < c[3] for c in self._collision_box):
            if self._last_pos:
                pos = self.GetCollisionPos((
                 self._last_pos[0] + hs0, self._last_pos[1] + hs1), pos)
                if len(pos) == 4:
                    pos = self.GetCollisionPos(pos[:2], pos[2:])[:2]
            else:
                safe_pos = Gui.get_global_position(self.screen_name, BP)
                safe_size = Gui.get_size(self.screen_name, BP)
                safe_area = (
                 safe_pos[0] + hs0, safe_pos[1] + hs1,
                 safe_pos[0] + safe_size[0] - hs0, safe_pos[1] + safe_size[1] - hs1)
                pos = tuple(min(max(pos[n], safe_area[n]), safe_area[n + 2]) for n in (0,
                                                                                       1))
                pos_list = tuple(self.GetCollisionPos(p, pos) for p in (
                 (
                  safe_area[0], pos[1]),
                 (
                  pos[0], safe_area[1]),
                 (
                  safe_area[2], pos[1]),
                 (
                  pos[0], safe_area[3])) if not any(c[0] < p[0] < c[2] and c[1] < p[1] < c[3] for c in self._collision_box))
                if pos_list:
                    pos = _get_nearest_pos(pos_list, pos)
        if not any(c[0] < pos[0] < c[2] and c[1] < pos[1] < c[3] for c in self._collision_box):
            self._last_pos = (
             pos[0] - hs0, pos[1] - hs1)
            self.SetGlobalPosition(path, self._last_pos)
        return self.GetPosition(path)

    def GetCollisionPos(self, pos, new_pos):
        """获取从 pos 到 new_pos 的碰撞点和投影点，没有碰撞点则返回终点"""
        x1, y1 = pos
        x2, y2 = new_pos
        collision_pos = []
        a, b, c, d = (min(x1, x2), max(x1, x2), min(y1, y2), max(y1, y2))
        for x3, y3, x4, y4 in self._collision_box:
            if x2 < x1 and x3 >= x1 or x2 > x1 and x4 <= x1 or y2 < y1 and y3 >= y1 or y2 > y1 and y4 <= y1:
                continue
            for x5, y5, x6, y6, px, py in (
             (
              x3, y3, x4, y3, x2, y3),
             (
              x3, y3, x3, y4, x3, y2),
             (
              x3, y4, x4, y4, x2, y4),
             (
              x4, y3, x4, y4, x4, y2)):
                divisor = (x1 - x2) * (y5 - y6) - (y1 - y2) * (x5 - x6)
                if not divisor:
                    continue
                x7 = (x1 * y2 - y1 * x2) * (x5 - x6) - (x1 - x2) * (x5 * y6 - y5 * x6) - divisor
                y7 = (x1 * y2 - y1 * x2) * (y5 - y6) - (y1 - y2) * (x5 * y6 - y5 * x6) - divisor
                if a - 1e-06 < x7 < b + 1e-06 and c - 1e-06 < y7 < d + 1e-06 and x3 - 1e-06 < x7 < x4 + 1e-06 and y3 - 1e-06 < y7 < y4 + 1e-06 and not any(e[0] + 1e-06 < x7 < e[2] - 1e-06 and e[1] + 1e-06 < y7 < e[3] - 1e-06 for e in self._collision_box) and ((x5 != x7 or y5 != y7) and (x6 != x7 or y6 != y7) or x2 != x1 and y2 != y1):
                    collision_pos.append((x7, y7, px, py))

        if collision_pos:
            return _get_nearest_pos(collision_pos, new_pos)
        return new_pos

    def _CorrectPosAndSave(self, path):
        pos = self._CorrectButtonPos(path)
        custom_key = self._moveable_widgets.get(path)
        if custom_key:
            self.SetSavedButtonPos(custom_key, path, pos)
        return

    def ResetAllButtons(self):
        """重置所有可拖动按钮到初始位置，将位置设为 (0,0) 并同步持久化数据"""
        for path, custom_key in self._moveable_widgets.items():
            self.GetBaseUIControl(path).SetPosition((0, 0))
            if custom_key:
                self.SetSavedButtonPos(custom_key, path, (0, 0))

        return

    def _OnScreenSizeChanged(self, args):
        self._delay_func.append((self._OnScreenSizeChangedAfter, args))
        return

    def _OnScreenSizeChangedAfter(self, args):
        self._InitOriginCollisionBox()
        for path in self._moveable_widgets:
            self._InitCollisionBox(path)
            self._CorrectPosAndSave(path)

        return

    def Create(self):
        self._InitOriginCollisionBox()
        Event.ListenForEventClient(EN, ESN, 'HudButtonChangedClientEvent', self, self._OnScreenSizeChangedAfter, 10, True)
        Event.ListenForEventClient(EN, ESN, 'ScreenSizeChangedClientEvent', self, self._OnScreenSizeChanged, 10, True)
        return

    def Update(self):
        for func in self._delay_func:
            func[0](*func[1:])

        del self._delay_func[:]
        if self._move_timer:
            self._move_timer -= 1
            if self._move_timer == 0:
                CF.CreateDevice(PID).SetDeviceVibrate(20)
                CF.CreateGame(PID).SetTipMessage('你正在拖动按钮')
        return

    def Destroy(self):
        Event.UnListenForEventClient(EN, ESN, 'HudButtonChangedClientEvent', self, self._OnScreenSizeChangedAfter, 10, True)
        Event.UnListenForEventClient(EN, ESN, 'ScreenSizeChangedClientEvent', self, self._OnScreenSizeChanged, 10, True)
        return

