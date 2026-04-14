# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
# Embedded file name: ValkyrienBE/client/ui/PhysStateSetUI.py
"""
物理状态操作面板 HUD
进入某个物理操作模式（单方块 / 多方块 / 删除 / 捉捕 / 磁吸 / 喷射 / 交互）后
显示的详细操作 UI。由 ClientSystem 在 UiInitFinished 时创建并注入 InputManager。
"""
import mod.client.extraClientApi as clientApi
ViewBinder = clientApi.GetViewBinderCls()
from ValkyrienBE.client.ui.MoveableButton import MoveableButton
from ValkyrienBE.common.constants import PHYS_ITEM_NAME
CF = clientApi.GetEngineCompFactory()
LID = clientApi.GetLevelId()
PID = clientApi.GetLocalPlayerId()
BASE_PATH = '/variables_button_mappings_and_controls/safezone_screen_matrix/inner_matrix/safezone_screen_panel/root_screen_panel'

class PhysStateSetUI(MoveableButton):
    """物理状态操作面板 HUD，管理七个功能子面板的显隐和交互回调。"""
    PATH_ONE_BLOCK = BASE_PATH + '/one_block_panel/one_block'
    PATH_MORE_BLOCK = BASE_PATH + '/more_block_panel/more_block'
    PATH_DELETE_BLOCK = BASE_PATH + '/delete_block_panel/delete_block'
    PATH_CATCH_BLOCK = BASE_PATH + '/catch_block_panel/catch_block'
    PATH_SUCK_BLOCK = BASE_PATH + '/suck_block_panel/suck_block'
    PATH_SPAWN_BLOCK = BASE_PATH + '/spawn_block_panel/spawn_block'
    PATH_INTERACT_BLOCK = BASE_PATH + '/interact_block'
    PATH_ONE_BLOCK_MOVE = PATH_ONE_BLOCK + '/movebutton'
    PATH_MORE_BLOCK_MOVE = PATH_MORE_BLOCK + '/movebutton'
    PATH_MORE_BLOCK_START = PATH_MORE_BLOCK + '/start'
    PATH_MORE_BLOCK_FRONT = PATH_MORE_BLOCK + '/front'
    PATH_MORE_BLOCK_YES = PATH_MORE_BLOCK + '/yes'
    PATH_MORE_BLOCK_YES_LABEL = PATH_MORE_BLOCK_YES + '/button_label'
    PATH_MORE_BLOCK_LAST = PATH_MORE_BLOCK + '/last'
    PATH_MORE_BLOCK_HAND_PANEL = PATH_MORE_BLOCK + '/hand_panel'
    PATH_MORE_BLOCK_FINAL = PATH_MORE_BLOCK + '/final'
    PATH_MORE_BLOCK_TOGGLE = PATH_MORE_BLOCK + '/switch_toggle(0)(0)'
    PATH_DELETE_BLOCK_MOVE = PATH_DELETE_BLOCK + '/movebutton'
    PATH_CATCH_BLOCK_MOVE = PATH_CATCH_BLOCK + '/movebutton'
    PATH_CATCH_RELEASE_BTN = PATH_CATCH_BLOCK + '/button(0)(0)'
    PATH_CATCH_RELEASE_BTN2 = PATH_CATCH_BLOCK + '/button(0)(0)(0)'
    PATH_SUCK_BLOCK_MOVE = PATH_SUCK_BLOCK + '/movebutton'
    PATH_SUCK_TOGGLE = PATH_SUCK_BLOCK + '/switch_toggle'
    PATH_SPAWN_BLOCK_MOVE = PATH_SPAWN_BLOCK + '/movebutton'
    PATH_SPAWN_BTN_LABEL = PATH_SPAWN_BLOCK + '/button(0)(0)/button_label'
    PATH_INTERACT_EXIT_MOVE = PATH_INTERACT_BLOCK + '/exit_panel/exit/movebutton'
    PATH_INTERACT_ATTACK = PATH_INTERACT_BLOCK + '/attack_panel/attack'
    PATH_INTERACT_USE = PATH_INTERACT_BLOCK + '/interact_panel/interact'
    PATH_INTERACT_IMAGE = PATH_INTERACT_BLOCK + '/image'

    def __init__(self, namespace, name, param):
        MoveableButton.__init__(self, namespace, name, param)
        self.more_block_pos_mode = 0
        self.more_block_dir_mode = 0
        self.more_block_step = 0
        self._spray_active = False
        self._input_mgr = None
        return

    def set_input_manager(self, input_mgr):
        """注入 InputManager 引用，供 UI 回调调用输入逻辑"""
        self._input_mgr = input_mgr
        return

    def Create(self):
        """UI 创建回调，为每个功能面板注册可拖动按钮"""
        MoveableButton.Create(self)
        self.AddMoveableButton(self.PATH_ONE_BLOCK_MOVE, self._pass_func, 'xiaobo_phys_one_block_hud_new2', True)
        self.AddMoveableButton(self.PATH_MORE_BLOCK_MOVE, self._pass_func, 'xiaobo_phys_more_block_hud_new2', True)
        self.AddMoveableButton(self.PATH_DELETE_BLOCK_MOVE, self._pass_func, 'xiaobo_phys_delete_block_hud_new2', True)
        self.AddMoveableButton(self.PATH_CATCH_BLOCK_MOVE, self._pass_func, 'xiaobo_phys_catch_block_hud_new2', True)
        self.AddMoveableButton(self.PATH_SUCK_BLOCK_MOVE, self._pass_func, 'xiaobo_phys_suck_block_hud_new2', True)
        self.AddMoveableButton(self.PATH_SPAWN_BLOCK_MOVE, self._pass_func, 'xiaobo_phys_spawn_block_hud_new2', True)
        self.AddMoveableButton(self.PATH_INTERACT_EXIT_MOVE, self._pass_func, 'xiaobo_phys_interact_block_hud_new2', True)
        self.AddMoveableButton(self.PATH_INTERACT_ATTACK, self._onInteractLeftClick, 'xiaobo_phys_interact_block_hud_left_new2', False)
        self.AddMoveableButton(self.PATH_INTERACT_USE, self._onInteractRightClick, 'xiaobo_phys_interact_block_hud_right_new2', False)
        return

    def _pass_func(self, args=None):
        """空回调，用于仅需拖动不需要点击逻辑的按钮"""
        return

    def _onInteractLeftClick(self, args=None):
        """交互面板攻击按钮回调 → 破坏船体方块"""
        if self._input_mgr:
            self._input_mgr.send_destroy_block_on_ship()
        return

    def _onInteractRightClick(self, args=None):
        """交互面板放置按钮回调 → 放置方块到船体"""
        if self._input_mgr:
            self._input_mgr.send_place_block_on_ship()
        return

    def set_one_block_panel_visible(self, visible):
        """设置单方块面板可见性"""
        self.GetBaseUIControl(self.PATH_ONE_BLOCK).SetVisible(visible)
        return

    def set_more_block_panel_visible(self, visible):
        """设置多方块面板可见性，同时重置选区状态"""
        self.GetBaseUIControl(self.PATH_MORE_BLOCK_START).asSwitchToggle().SetToggleState(True)
        self.GetBaseUIControl(self.PATH_MORE_BLOCK_FRONT).asSwitchToggle().SetToggleState(True)
        self.more_block_pos_mode = 0
        self.more_block_dir_mode = 0
        self.more_block_step = 0
        self.GetBaseUIControl(self.PATH_MORE_BLOCK).SetVisible(visible)
        if visible:
            self.more_block_step = 0
            self._update_more_block_ui()
        return

    def set_delete_phys_panel_visible(self, visible):
        """设置去物理化面板可见性"""
        self.GetBaseUIControl(self.PATH_DELETE_BLOCK).SetVisible(visible)
        return

    def set_catch_block_panel_visible(self, visible):
        """设置捉捕面板可见性，初始隐藏释放按钮"""
        self.GetBaseUIControl(self.PATH_CATCH_BLOCK).SetVisible(visible)
        self.GetBaseUIControl(self.PATH_CATCH_RELEASE_BTN).SetVisible(False)
        self.GetBaseUIControl(self.PATH_CATCH_RELEASE_BTN2).SetVisible(False)
        return

    def show_catch_release_button(self, visible):
        """控制捉捕面板中释放按钮的显隐"""
        self.GetBaseUIControl(self.PATH_CATCH_RELEASE_BTN).SetVisible(visible)
        self.GetBaseUIControl(self.PATH_CATCH_RELEASE_BTN2).SetVisible(visible)
        return

    def set_suck_block_panel_visible(self, visible):
        """设置磁吸面板可见性，同时重置磁吸开关为关闭"""
        self.GetBaseUIControl(self.PATH_SUCK_BLOCK).SetVisible(visible)
        self.GetBaseUIControl(self.PATH_SUCK_TOGGLE).asSwitchToggle().SetToggleState(False)
        return

    def set_spray_block_panel_visible(self, visible):
        """设置喷射面板可见性，同时重置按钮文字为"开始喷射" """
        self.GetBaseUIControl(self.PATH_SPAWN_BLOCK).SetVisible(visible)
        self._spray_active = False
        self.GetBaseUIControl(self.PATH_SPAWN_BTN_LABEL).asLabel().SetText('开始喷射')
        return

    def reset_spray_button(self):
        """重置喷射按钮状态和文字"""
        self._spray_active = False
        self.GetBaseUIControl(self.PATH_SPAWN_BTN_LABEL).asLabel().SetText('开始喷射')
        return

    def set_interact_block_panel_visible(self, visible):
        """设置交互面板可见性，根据是否分离操控决定图片显示"""
        self.GetBaseUIControl(self.PATH_INTERACT_BLOCK).SetVisible(visible)
        isSplit = CF.CreatePlayerView(LID).GetToggleOption(clientApi.GetMinecraftEnum().OptionId.SPLIT_CONTROLS)
        self.GetBaseUIControl(self.PATH_INTERACT_IMAGE).SetVisible(not isSplit)
        return

    def hide_all(self):
        """隐藏所有功能面板"""
        self.GetBaseUIControl(self.PATH_ONE_BLOCK).SetVisible(False)
        self.GetBaseUIControl(self.PATH_MORE_BLOCK).SetVisible(False)
        self.GetBaseUIControl(self.PATH_DELETE_BLOCK).SetVisible(False)
        self.GetBaseUIControl(self.PATH_CATCH_BLOCK).SetVisible(False)
        self.GetBaseUIControl(self.PATH_SUCK_BLOCK).SetVisible(False)
        self.GetBaseUIControl(self.PATH_SPAWN_BLOCK).SetVisible(False)
        self.GetBaseUIControl(self.PATH_INTERACT_BLOCK).SetVisible(False)
        return

    def _update_more_block_ui(self):
        """根据当前 more_block_step 刷新多方块面板中按钮和面板的显隐状态"""
        yes_btn = self.GetBaseUIControl(self.PATH_MORE_BLOCK_YES)
        last_btn = self.GetBaseUIControl(self.PATH_MORE_BLOCK_LAST)
        hand_panel = self.GetBaseUIControl(self.PATH_MORE_BLOCK_HAND_PANEL)
        if self.more_block_step == 0:
            yes_btn.SetVisible(True)
            last_btn.SetVisible(False)
            hand_panel.SetVisible(self.more_block_dir_mode == 2)
        elif self.more_block_step == 1:
            yes_btn.SetVisible(True)
            last_btn.SetVisible(False)
            hand_panel.SetVisible(self.more_block_dir_mode == 2)
        elif self.more_block_step == 2:
            yes_btn.SetVisible(False)
            last_btn.SetVisible(True)
            hand_panel.SetVisible(False)
        return

    def on_more_block_right_click(self):
        """多方块模式下右键确认，根据当前步骤推进选区流程"""
        if not self._input_mgr:
            return
        else:
            mgr = self._input_mgr
            if self.more_block_step == 0:
                if mgr.select_block_pos is None:
                    return
                mgr.more_block_from_pos = mgr.select_block_pos
                self.more_block_step = 1
                self.more_block_pos_mode = 1
                self._update_more_block_ui()
                self.GetBaseUIControl(self.PATH_MORE_BLOCK_FINAL).asSwitchToggle().SetToggleState(True)
                self.GetBaseUIControl(self.PATH_MORE_BLOCK_YES_LABEL).asLabel().SetText('确定终点')
                CF.CreateGame(PID).SetTipMessage(clientApi.GenerateColor('GREEN') + '起点已确定, 请选择终点')
            elif self.more_block_step == 1:
                if mgr.select_block_pos is None:
                    return
                mgr.more_block_to_pos = mgr.select_block_pos
                self.more_block_step = 2
                mgr.effect_mgr.region_select.show_region(mgr.more_block_from_pos, mgr.more_block_to_pos)
                self.GetBaseUIControl(self.PATH_MORE_BLOCK_TOGGLE).asSwitchToggle().SetToggleState(True)
                self.GetBaseUIControl(self.PATH_MORE_BLOCK_YES_LABEL).asLabel().SetText('确定起点')
                self._update_more_block_ui()
                CF.CreateGame(PID).SetTipMessage(clientApi.GenerateColor('GREEN') + '区域已选定, 点击确定结构进行物理化')
            elif self.more_block_step == 2:
                if mgr.more_block_from_pos is None or mgr.more_block_to_pos is None:
                    return
                mgr.send_physic_block_region()
                mgr.quit_state()
            return

    @ViewBinder.binding(ViewBinder.BF_ButtonClickUp, '#xiaobo_oneblock_phys')
    def on_one_block_phys_click(self, args):
        """单方块物理化按钮回调，需手持物理木棍"""
        if not self._input_mgr:
            return
        item = CF.CreateItem(PID).GetCarriedItem()
        if not item or item['newItemName'] != PHYS_ITEM_NAME:
            CF.CreateGame(PID).SetTipMessage(clientApi.GenerateColor('RED') + '请手持物理木棍使用此功能')
            return
        self._input_mgr.send_physic_block()
        return

    @ViewBinder.binding(ViewBinder.BF_ButtonClickUp, '#xiaobo_oneblock_delete')
    def on_one_block_delete_click(self, args):
        """单方块面板退出按钮回调"""
        if self._input_mgr:
            self._input_mgr.quit_state()
        return

    @ViewBinder.binding(ViewBinder.BF_ToggleChanged, '#xiaobo_moreblock_hud_pos')
    def on_more_block_pos_toggle(self, args):
        """多方块位置切换回调：在起点 / 终点模式间切换"""
        index = args['index']
        state = args['state']
        if not state or not self._input_mgr:
            return
        mgr = self._input_mgr
        self.more_block_pos_mode = index
        if index == 0:
            self.more_block_step = 0
            mgr.more_block_from_pos = None
            mgr.more_block_to_pos = None
            mgr.effect_mgr.region_select.hide_all()
            self.GetBaseUIControl(self.PATH_MORE_BLOCK_YES_LABEL).asLabel().SetText('确定起点')
        elif index == 1:
            if mgr.more_block_from_pos is not None:
                self.more_block_step = 1
            else:
                self.more_block_step = 0
            self.GetBaseUIControl(self.PATH_MORE_BLOCK_YES_LABEL).asLabel().SetText('确定终点')
        self._update_more_block_ui()
        return

    @ViewBinder.binding(ViewBinder.BF_ToggleChanged, '#xiaobo_moreblock_hud_direction')
    def on_more_block_dir_toggle(self, args):
        """多方块朝向切换回调"""
        index = args['index']
        state = args['state']
        if state:
            self.more_block_dir_mode = index
            self._update_more_block_ui()
        return

    @ViewBinder.binding(ViewBinder.BF_ButtonClickUp, '#xiaobo_moreblock_confirm')
    def on_more_block_confirm_click(self, args):
        """多方块确认按钮回调，推进选区流程"""
        self.on_more_block_right_click()
        return

    @ViewBinder.binding(ViewBinder.BF_ButtonClickUp, '#xiaobo_moreblock_cancel')
    def on_more_block_cancel_click(self, args):
        """多方块取消按钮回调，退出当前状态"""
        if self._input_mgr:
            self._input_mgr.quit_state()
        return

    @ViewBinder.binding(ViewBinder.BF_ButtonClickUp, '#xiaobo_moreblock_hud_last_confirm')
    def on_more_block_last_confirm_click(self, args):
        """多方块最终确认按钮回调，发送物理化区域请求"""
        if not self._input_mgr:
            return
        else:
            mgr = self._input_mgr
            if mgr.more_block_from_pos is None or mgr.more_block_to_pos is None:
                return
            mgr.send_physic_block_region()
            mgr.quit_state()
            return

    @ViewBinder.binding(ViewBinder.BF_ButtonClickUp, '#xiaobo_moreblock_hand_up')
    def on_hand_up(self, args):
        """手动调整：向上偏移"""
        if self._input_mgr:
            self._input_mgr.manual_adjust_pos(0, 1, 0)
        return

    @ViewBinder.binding(ViewBinder.BF_ButtonClickUp, '#xiaobo_moreblock_hand_down')
    def on_hand_down(self, args):
        """手动调整：向下偏移"""
        if self._input_mgr:
            self._input_mgr.manual_adjust_pos(0, -1, 0)
        return

    @ViewBinder.binding(ViewBinder.BF_ButtonClickUp, '#xiaobo_moreblock_hand_forward')
    def on_hand_forward(self, args):
        """手动调整：向前偏移"""
        if self._input_mgr:
            self._input_mgr.manual_adjust_pos(0, 0, 1)
        return

    @ViewBinder.binding(ViewBinder.BF_ButtonClickUp, '#xiaobo_moreblock_hand_backward')
    def on_hand_backward(self, args):
        """手动调整：向后偏移"""
        if self._input_mgr:
            self._input_mgr.manual_adjust_pos(0, 0, -1)
        return

    @ViewBinder.binding(ViewBinder.BF_ButtonClickUp, '#xiaobo_moreblock_hand_left')
    def on_hand_left(self, args):
        """手动调整：向左偏移"""
        if self._input_mgr:
            self._input_mgr.manual_adjust_pos(-1, 0, 0)
        return

    @ViewBinder.binding(ViewBinder.BF_ButtonClickUp, '#xiaobo_moreblock_hand_right')
    def on_hand_right(self, args):
        """手动调整：向右偏移"""
        if self._input_mgr:
            self._input_mgr.manual_adjust_pos(1, 0, 0)
        return

    @ViewBinder.binding(ViewBinder.BF_ButtonClickUp, '#xiaobo_delete_block_phys')
    def on_delete_block_phys_click(self, args):
        """去物理化面板退出按钮回调"""
        if self._input_mgr:
            self._input_mgr.quit_state()
        return

    @ViewBinder.binding(ViewBinder.BF_ButtonClickUp, '#xiaobo_catch_block_exit')
    def on_catch_block_exit_click(self, args=None):
        """捉捕面板退出按钮回调：释放方块并退出状态"""
        self.GetBaseUIControl(self.PATH_CATCH_RELEASE_BTN).SetVisible(False)
        self.GetBaseUIControl(self.PATH_CATCH_RELEASE_BTN2).SetVisible(False)
        if self._input_mgr:
            self._input_mgr.release_block()
            self._input_mgr.quit_state()
        return

    @ViewBinder.binding(ViewBinder.BF_ButtonClickUp, '#xiaobo_catch_block_release')
    def on_catch_block_release_click(self, args):
        """捉捕面板释放按钮回调：仅释放方块，不退出状态"""
        self.GetBaseUIControl(self.PATH_CATCH_RELEASE_BTN).SetVisible(False)
        self.GetBaseUIControl(self.PATH_CATCH_RELEASE_BTN2).SetVisible(False)
        if self._input_mgr:
            self._input_mgr.release_block()
        return

    @ViewBinder.binding(ViewBinder.BF_ButtonClickUp, '#xiaobo_catch_block_rotate')
    def on_catch_block_rotate_click(self, args):
        """捉捕面板旋转按钮回调"""
        if self._input_mgr:
            self._input_mgr.rotate_caught_block()
        return

    @ViewBinder.binding(ViewBinder.BF_ToggleChanged, '#xiaobo_catch_block_rotate')
    def on_catch_block_rotate_toggle(self, args):
        """捉捕面板旋转轴切换回调"""
        index = args['index']
        state = args['state']
        if state and self._input_mgr:
            self._input_mgr.set_catch_rotate_axis(index)
        return

    @ViewBinder.binding(ViewBinder.BF_ButtonClickUp, '#xiaobo_suck_block_exit')
    def on_suck_block_exit_click(self, args=None):
        """磁吸面板退出按钮回调：重置开关并退出状态"""
        self.GetBaseUIControl(self.PATH_SUCK_TOGGLE).asSwitchToggle().SetToggleState(False)
        if self._input_mgr:
            self._input_mgr.quit_state()
        return

    @ViewBinder.binding(ViewBinder.BF_ToggleChanged, '#xiaobo_suck_block_toggle')
    def on_suck_block_toggle(self, args):
        """磁吸开关切换回调"""
        state = args['state']
        if self._input_mgr:
            self._input_mgr.suck_block(state)
        return

    def on_suck_block_toggle_change_state(self):
        """外部调用：反转磁吸开关状态（用于键盘快捷键等场景）"""
        toggle = self.GetBaseUIControl(self.PATH_SUCK_TOGGLE).asSwitchToggle()
        toggle.SetToggleState(not toggle.GetToggleState())
        return

    @ViewBinder.binding(ViewBinder.BF_ButtonClickUp, '#xiaobo_spawn_block_exit')
    def on_spawn_block_exit_click(self, args=None):
        """喷射面板退出按钮回调：如果正在喷射则先停止"""
        if self._spray_active and self._input_mgr:
            self._spray_active = False
            self._input_mgr.spray_block(False)
        if self._input_mgr:
            self._input_mgr.quit_state()
        return

    @ViewBinder.binding(ViewBinder.BF_ButtonClickUp, '#xiaobo_spawn_block')
    def on_spawn_block_click(self, args=None):
        """喷射开始/停止按钮回调，需手持物理木棍"""
        item = CF.CreateItem(PID).GetCarriedItem()
        if not item or item['newItemName'] != PHYS_ITEM_NAME:
            CF.CreateGame(PID).SetTipMessage(clientApi.GenerateColor('RED') + '请手持物理木棍使用此功能')
            return
        self._spray_active = not self._spray_active
        if self._input_mgr:
            self._input_mgr.spray_block(self._spray_active)
        if self._spray_active:
            self.GetBaseUIControl(self.PATH_SPAWN_BTN_LABEL).asLabel().SetText('停止喷射')
        else:
            self.GetBaseUIControl(self.PATH_SPAWN_BTN_LABEL).asLabel().SetText('开始喷射')
        return

    @ViewBinder.binding(ViewBinder.BF_ButtonClickUp, '#xiaobo_interact_block_exit')
    def on_interact_block_exit_click(self, args=None):
        """交互面板退出按钮回调"""
        if self._input_mgr:
            self._input_mgr.quit_state()
        return

