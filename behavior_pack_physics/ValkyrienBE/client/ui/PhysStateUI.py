# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
# Embedded file name: ValkyrienBE/client/ui/PhysStateUI.py
"""
物理状态选择 HUD
主界面上的可拖动按钮，用于选择物理操作模式（单方块/多方块/去物理化/捉捕/磁吸/喷射/一键删除）。
点击左右箭头切换模式，点击确认按钮将当前模式下发给 InputManager。
"""
import mod.client.extraClientApi as clientApi
from ValkyrienBE.client.ui.MoveableButton import MoveableButton
from ValkyrienBE.common.constants import PhysMode
CF = clientApi.GetEngineCompFactory()
LID = clientApi.GetLevelId()
PID = clientApi.GetLocalPlayerId()
BASE_PATH = '/variables_button_mappings_and_controls/safezone_screen_matrix/inner_matrix/safezone_screen_panel/root_screen_panel'

class PhysStateUI(MoveableButton):
    """
    物理状态选择 HUD

    通过左右箭头在 PhysMode 枚举间循环切换，
    确认后通知 InputManager 进入对应物理操作模式。
    继承 MoveableButton 以支持长按拖动。
    """
    PATH_IMAGE = BASE_PATH + '/panel/image'
    PATH_BUTTON = BASE_PATH + '/panel/image/button'
    PATH_RIGHT = BASE_PATH + '/panel/image/right'
    PATH_LEFT = BASE_PATH + '/panel/image/left'
    PATH_YES = BASE_PATH + '/panel/image/yes'
    PATH_LABEL = BASE_PATH + '/panel/image/label'

    def __init__(self, namespace, name, param):
        MoveableButton.__init__(self, namespace, name, param)
        self.state = 0
        self._input_mgr = None
        return

    def set_input_manager(self, input_mgr):
        """注入 InputManager 引用，用于确认模式后下发操作状态"""
        self._input_mgr = input_mgr
        return

    def Create(self):
        """UI 创建回调，注册可拖动按钮并绑定左右切换、确认按钮事件"""
        MoveableButton.Create(self)
        self.AddMoveableButton(self.PATH_BUTTON, self._pass_function, 'xiaobo_phys_hud_new2', True)
        right_btn = self.GetBaseUIControl(self.PATH_RIGHT).asButton()
        right_btn.AddTouchEventParams({'isSwallow': True})
        right_btn.SetButtonTouchUpCallback(self.on_right_state_change)
        left_btn = self.GetBaseUIControl(self.PATH_LEFT).asButton()
        left_btn.AddTouchEventParams({'isSwallow': True})
        left_btn.SetButtonTouchUpCallback(self.on_left_state_change)
        yes_btn = self.GetBaseUIControl(self.PATH_YES).asButton()
        yes_btn.AddTouchEventParams({'isSwallow': True})
        yes_btn.SetButtonTouchUpCallback(self.on_yes_button)
        return

    def on_right_state_change(self, args=None):
        """右箭头点击回调，模式索引 +1 并循环，刷新标签文本"""
        self.state = (self.state + 1) % PhysMode.COUNT
        label = self.GetBaseUIControl(self.PATH_LABEL).asLabel()
        label.SetText(PhysMode.NAMES.get(self.state, '未知'))
        return

    def on_left_state_change(self, args=None):
        """左箭头点击回调，模式索引 -1 并循环，刷新标签文本"""
        self.state = (self.state - 1) % PhysMode.COUNT
        label = self.GetBaseUIControl(self.PATH_LABEL).asLabel()
        label.SetText(PhysMode.NAMES.get(self.state, '未知'))
        return

    def _pass_function(self, args=None):
        """空回调，仅用于满足 AddMoveableButton 的回调参数要求"""
        return

    def Show(self):
        """显示物理状态选择面板"""
        self.GetBaseUIControl(self.PATH_IMAGE).SetVisible(True)
        return

    def Hide(self):
        """隐藏物理状态选择面板"""
        self.GetBaseUIControl(self.PATH_IMAGE).SetVisible(False)
        return

    def on_yes_button(self, args=None):
        """
        确认按钮回调

        将当前 state 下发给 InputManager；
        非一键删除模式时自动隐藏面板（删除模式保持可见以便连续操作）。
        """
        if self._input_mgr:
            if self.state != PhysMode.REMOVE_ALL:
                self.Hide()
            self._input_mgr.set_phys_state(self.state)
        return

