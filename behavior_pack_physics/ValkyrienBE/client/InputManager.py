# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
# Embedded file name: ValkyrienBE/client/InputManager.py
"""
输入管理器
负责：物理操作状态机、键盘/手柄/触屏输入处理、
      方块选取、点击交互、以及与 UI/Server 的通信。
"""
import math, mod.client.extraClientApi as clientApi
from ValkyrienBE.common import events
from ValkyrienBE.common.constants import PhysMode, PHYS_ITEM_NAME
from ValkyrienBE.util import Math
CF = clientApi.GetEngineCompFactory()
LID = clientApi.GetLevelId()
PID = clientApi.GetLocalPlayerId()

class InputManager(object):
    """输入管理器"""

    def __init__(self, system, render_mgr, effect_mgr):
        """
        @param system: ValkyrienBEClientSystem 实例
        @param render_mgr: RenderManager 实例
        @param effect_mgr: EffectManager 实例
        """
        self._system = system
        self.render_mgr = render_mgr
        self.effect_mgr = effect_mgr
        self.phys_state_ui = None
        self.phys_state_set_ui = None
        self.is_in_project = False
        self.phys_state = -1
        self.select_block_pos = None
        self.more_block_from_pos = None
        self.more_block_to_pos = None
        self._caught_entity_id = None
        self._catch_rotate_axis = 0
        self._pending_range_restore = False
        self._original_pick_range = 5.0
        self._key_data = CF.CreateConfigClient(LID).GetConfigData('xiaobo_phys_stimulate_key_data', True) or {}
        self._register_custom_keys()
        return

    def _register_custom_keys(self):
        """注册自定义按键和手柄映射"""
        pv = CF.CreatePlayerView(LID)
        kd = self._key_data
        pv.RegisterCustomKeyMapping('退出状态', int(kd.get('exit', 82)), '物理模拟')
        pv.RegisterCustomKeyMapping('状态切换左', int(kd.get('switch_left', 37)), '物理模拟')
        pv.RegisterCustomKeyMapping('状态切换右', int(kd.get('switch_right', 39)), '物理模拟')
        pv.RegisterCustomKeyMapping('物理化方块破坏', int(kd.get('destroy_phys_block', 72)), '物理模拟')
        pv.RegisterCustomKeyMapping('物理化方块交互', int(kd.get('interact_phys_block', 74)), '物理模拟')
        pv.RegisterCustomGamepadMapping('退出状态', int(kd.get('exit_gamepad', 0)), '物理模拟')
        pv.RegisterCustomGamepadMapping('状态切换左', int(kd.get('switch_left_gamepad', 0)), '物理模拟')
        pv.RegisterCustomGamepadMapping('状态切换右', int(kd.get('switch_right_gamepad', 0)), '物理模拟')
        pv.RegisterCustomGamepadMapping('状态确认', int(kd.get('switch_confirm_gamepad', 0)), '物理模拟')
        pv.RegisterCustomGamepadMapping('物理化方块破坏', int(kd.get('destroy_phys_block_gamepad', 0)), '物理模拟')
        pv.RegisterCustomGamepadMapping('物理化方块交互', int(kd.get('interact_phys_block_gamepad', 0)), '物理模拟')
        return

    def set_phys_state(self, state):
        """设置物理化操作状态"""
        self.is_in_project = True
        self.phys_state = state
        if state == PhysMode.SINGLE:
            self.phys_state_set_ui.set_one_block_panel_visible(True)
            CF.CreateGame(PID).SetTipMessage(clientApi.GenerateColor('GREEN') + '手持物理法杖右键或点击按钮即可物理化单个方块')
        elif state == PhysMode.REGION:
            self.more_block_from_pos = None
            self.more_block_to_pos = None
            self.phys_state_set_ui.set_more_block_panel_visible(True)
            CF.CreateGame(PID).SetTipMessage(clientApi.GenerateColor('GREEN') + '请选择起点方块, 然后点击确定起点')
        elif state == PhysMode.REMOVE:
            self.phys_state_set_ui.set_delete_phys_panel_visible(True)
            CF.CreateGame(PID).SetTipMessage(clientApi.GenerateColor('GREEN') + '手持物理法杖攻击方块或右键去物理化')
        elif state == PhysMode.CATCH:
            self._caught_entity_id = None
            self.phys_state_set_ui.set_catch_block_panel_visible(True)
            CF.CreateGame(PID).SetTipMessage(clientApi.GenerateColor('GREEN') + '手持物理法杖攻击或右键物理方块即可捉捕, 右键释放')
        elif state == PhysMode.SUCK:
            self.phys_state_set_ui.set_suck_block_panel_visible(True)
            CF.CreateGame(PID).SetTipMessage(clientApi.GenerateColor('GREEN') + '开启开关后磁吸玩家前方物理方块')
        elif state == PhysMode.SPRAY:
            self.phys_state_set_ui.set_spray_block_panel_visible(True)
            CF.CreateGame(PID).SetTipMessage(clientApi.GenerateColor('GREEN') + '点击按钮向准心方向喷射混凝土方块')
        elif state == PhysMode.REMOVE_ALL:
            self.is_in_project = False
            self.phys_state = -1
            self._system.NotifyToServer(events.C2S_DELETE_ALL_PHYS, {})
        elif state == PhysMode.INTERACT:
            self.phys_state_set_ui.set_interact_block_panel_visible(True)
            chat_comp = CF.CreateTextNotifyClient(LID)
            chat_comp.SetLeftCornerNotify('交互功能正在测试中, 可能存在bug, 请谨慎使用')
            chat_comp.SetLeftCornerNotify('目前容器方块需要空手才能交互')
            chat_comp.SetLeftCornerNotify('目前拉杆等方块需要非空手才能交互')
            chat_comp.SetLeftCornerNotify('闪烁和旋转问题需要等待引擎更新后才能修复')
            chat_comp.SetLeftCornerNotify('方块如果过长则无法交互')
            CF.CreateGame(PID).SetTipMessage(clientApi.GenerateColor('GREEN') + '请点击按钮或者绑定按键与物理化方块交互')
        return

    def quit_state(self):
        """退出当前物理操作状态"""
        if self._caught_entity_id is not None:
            self.release_block()
        if self.phys_state == PhysMode.SUCK:
            self.suck_block(False)
        if self.phys_state == PhysMode.SPRAY:
            self.spray_block(False)
        if self.phys_state == PhysMode.INTERACT:
            self._system.NotifyToServer(events.C2S_EXIT_INTERACT, {'pid': PID})
            if self._pending_range_restore:
                CF.CreatePlayer(PID).SetPickRange(self._original_pick_range)
                self._pending_range_restore = False
        self.is_in_project = False
        self.phys_state = -1
        self.select_block_pos = None
        self.effect_mgr.block_select.hide_all()
        self.effect_mgr.region_select.hide_all()
        self.more_block_from_pos = None
        self.more_block_to_pos = None
        self.phys_state_set_ui.hide_all()
        item = CF.CreateItem(PID).GetCarriedItem()
        if item and item['newItemName'] == PHYS_ITEM_NAME:
            self.phys_state_ui.Show()
        return

    def send_physic_block(self):
        if self.select_block_pos is not None:
            self._system.NotifyToServer(events.C2S_PHYSIC_BLOCK, {'blockPos': (self.select_block_pos), 'pid': PID})
        return

    def send_physic_block_region(self):
        if self.more_block_from_pos and self.more_block_to_pos:
            self._system.NotifyToServer(events.C2S_PHYSIC_BLOCK_REGION, {'fromPos': (self.more_block_from_pos), 'toPos': (self.more_block_to_pos), 
               'pid': PID})
        return

    def release_block(self):
        if self._caught_entity_id is not None:
            self._system.NotifyToServer(events.C2S_RELEASE_BLOCK, {'pid': PID})
            self._caught_entity_id = None
        return

    def suck_block(self, state):
        self._system.NotifyToServer(events.C2S_SUCK_BLOCK, {'state': state, 'pid': PID})
        return

    def spray_block(self, state):
        self._system.NotifyToServer(events.C2S_SPRAY_BLOCK, {'state': state, 'pid': PID})
        return

    def rotate_caught_block(self):
        """旋转捉捕中的方块90度"""
        if self._caught_entity_id is not None:
            self._system.NotifyToServer(events.C2S_ROTATE_CAUGHT_BLOCK, {'pid': PID, 
               'axis': (self._catch_rotate_axis)})
        return

    def set_catch_rotate_axis(self, axis):
        """设置捉捕旋转轴 0=X, 1=Y, 2=Z"""
        self._catch_rotate_axis = axis
        return

    def send_place_block_on_ship(self):
        """发送放置方块到船体事件"""
        self._system.NotifyToServer(events.C2S_PLACE_BLOCK_ON_SHIP, {'pid': PID})
        return

    def send_destroy_block_on_ship(self):
        """发送破坏船体方块事件"""
        self._system.NotifyToServer(events.C2S_DESTROY_BLOCK_ON_SHIP, {'pid': PID})
        return

    def on_fallback_block_ready(self, args):
        """
        服务端通知备用方块已就绪，客户端轮询检测放置结果。
        当 -64 位置的方块非空气时，发 C2S 确认给服务端执行 PlayerUseItemToPos。
        """
        args['retry'] = 0
        self._poll_fallback_block(args)
        return

    def _poll_fallback_block(self, args):
        """轮询检测 fallback 方块是否已放置"""
        fb_pos = args.get('fallback_block_pos')
        dim_id = args.get('dim_id', 0)
        retry = args.get('retry', 0)
        block_info = CF.CreateBlockInfo(LID).GetBlock(fb_pos)
        if block_info and block_info[0] != 'minecraft:air':
            self._original_pick_range = CF.CreatePlayer(PID).GetPickRange()
            CF.CreatePlayer(PID).SetPickRange(400)
            self._pending_range_restore = True
            self._system.NotifyToServer(events.C2S_FALLBACK_BLOCK_CONFIRM, args)
            CF.CreateGame(LID).AddTimer(1.0, self._delayed_range_check)
        elif retry < 60:
            args['retry'] = retry + 1
            CF.CreateGame(LID).AddTimer(0, self._poll_fallback_block, args)
        else:
            args['timeout'] = True
            self._system.NotifyToServer(events.C2S_FALLBACK_BLOCK_CONFIRM, args)
        return

    def _delayed_range_check(self, args=None):
        """延迟1秒后检查屏幕，如果是hud则恢复交互距离，否则等待PopScreen恢复"""
        if not self._pending_range_restore:
            return
        if self._system.screen_current == 'hud.hud_screen':
            CF.CreatePlayer(PID).SetPickRange(self._original_pick_range)
            self._pending_range_restore = False
        return

    def on_pop_screen_range_restore(self):
        """PopScreenAfterClientEvent回调：恢复交互距离"""
        if self._pending_range_restore:
            CF.CreatePlayer(PID).SetPickRange(self._original_pick_range)
            self._pending_range_restore = False
        return

    def on_catch_block(self, args):
        """服务端通知方块已被捉捕"""
        self._caught_entity_id = args['entityId']
        self.phys_state_set_ui.show_catch_release_button(True)
        return

    def on_release_block(self, args):
        """服务端通知方块已释放"""
        self._caught_entity_id = None
        self.phys_state_set_ui.show_catch_release_button(False)
        return

    def on_spray_state_changed(self, args):
        """服务端通知喷射状态变更"""
        state = args.get('state', False)
        if not state:
            self.phys_state_set_ui.reset_spray_button()
        return

    def on_all_deleted(self, args):
        """服务端通知所有物理方块已删除"""
        self._caught_entity_id = None
        self.render_mgr.on_all_deleted(args)
        return

    def on_confirm_state(self, args):
        """
        服务端通知玩家攻击到了物理实体 (S2C_CONFIRM_STATE)
        根据当前 phys_state 发送对应的 C2S 事件
        """
        entity_id = args.get('entityId')
        if not entity_id or not self.is_in_project:
            return
        if self.phys_state == PhysMode.REMOVE:
            self._system.NotifyToServer(events.C2S_REMOVE_PHYSIC_BLOCK, {'entityId': entity_id, 'pid': PID})
        elif self.phys_state == PhysMode.CATCH:
            if self._caught_entity_id is not None:
                self.release_block()
            else:
                self._system.NotifyToServer(events.C2S_CATCH_BLOCK, {'entityId': entity_id, 'pid': PID})
        return

    def on_carried_item_changed(self, args):
        """手持物品变化"""
        item_dict = args.get('itemDict')
        item_name = item_dict['newItemName'] if item_dict else None
        self.render_mgr.update_held_item_query(item_name)
        if self.is_in_project:
            return
        else:
            if not self.phys_state_ui:
                return
            if item_name == PHYS_ITEM_NAME:
                self.phys_state_ui.Show()
            else:
                self.phys_state_ui.Hide()
            return

    def on_tap_before(self, args):
        """左键事件"""
        if not self.is_in_project:
            return
        else:
            item = CF.CreateItem(PID).GetCarriedItem()
            if not item or item['newItemName'] != PHYS_ITEM_NAME:
                CF.CreateGame(PID).SetTipMessage(clientApi.GenerateColor('RED') + '请手持物理法杖使用此功能')
                return
            if self.phys_state == PhysMode.REMOVE:
                phys = self._click_to_get_phys_block('tap')
                if phys is not None:
                    self._system.NotifyToServer(events.C2S_REMOVE_PHYSIC_BLOCK, {'entityId': (phys['entityId']), 'pid': PID})
            elif self.phys_state == PhysMode.CATCH:
                phys = self._click_to_get_phys_block('tap')
                if phys is not None:
                    self._system.NotifyToServer(events.C2S_CATCH_BLOCK, {'entityId': (phys['entityId']), 'pid': PID})
            return

    def on_right_click_before(self, args):
        """右键事件"""
        item = CF.CreateItem(PID).GetCarriedItem()
        if not self.is_in_project:
            if not item or item['newItemName'] != PHYS_ITEM_NAME:
                return
            self.phys_state_ui.on_yes_button()
            return
        else:
            if not item or item['newItemName'] != PHYS_ITEM_NAME:
                CF.CreateGame(PID).SetTipMessage(clientApi.GenerateColor('RED') + '请手持物理法杖使用此功能')
                return
            if self.phys_state == PhysMode.SINGLE:
                self.send_physic_block()
            elif self.phys_state == PhysMode.REGION:
                self.phys_state_set_ui.on_more_block_right_click()
            elif self.phys_state == PhysMode.REMOVE:
                phys = self._click_to_get_phys_block('right')
                if phys is not None:
                    self._system.NotifyToServer(events.C2S_REMOVE_PHYSIC_BLOCK, {'entityId': (phys['entityId']), 'pid': PID})
            elif self.phys_state == PhysMode.CATCH:
                if self._caught_entity_id is not None:
                    self.release_block()
                else:
                    phys = self._click_to_get_phys_block('right')
                    if phys is not None:
                        self._system.NotifyToServer(events.C2S_CATCH_BLOCK, {'entityId': (phys['entityId']), 'pid': PID})
            elif self.phys_state == PhysMode.SUCK:
                self.phys_state_set_ui.on_suck_block_toggle_change_state()
            elif self.phys_state == PhysMode.SPRAY:
                self.phys_state_set_ui.on_spawn_block_click()
            return

    def _click_to_get_phys_block(self, click_type):
        """获取指向的物理方块实体ID"""
        is_split = CF.CreatePlayerView(LID).GetToggleOption(clientApi.GetMinecraftEnum().OptionId.SPLIT_CONTROLS)
        if is_split == 0:
            pick_data = CF.CreateCamera(LID).GetChosen()
        else:
            pick_data = CF.CreateCamera(LID).PickFacing()
        phys = None
        if pick_data['type'] == 'Block':
            hit_x = pick_data['hitPosX']
            hit_y = pick_data['hitPosY']
            hit_z = pick_data['hitPosZ']
            px, py, pz = CF.CreatePos(PID).GetPos()
            dir_vec = (hit_x - px, hit_y - py, hit_z - pz)
            phys_list = CF.CreatePhysx(LID).Raycast((px, py, pz), dir_vec, 50, 1)
            if phys_list:
                phys = phys_list[0]
        elif pick_data['type'] == 'Entity':
            entity_id = pick_data['entityId']
            if entity_id in self.render_mgr.phys_block_palettes:
                if click_type == 'tap':
                    phys = None
                else:
                    phys = {'entityId': entity_id}
            else:
                hit_x = pick_data['hitPosX']
                hit_y = pick_data['hitPosY']
                hit_z = pick_data['hitPosZ']
                px, py, pz = CF.CreatePos(PID).GetPos()
                dir_vec = (hit_x - px, hit_y - py, hit_z - pz)
                phys_list = CF.CreatePhysx(LID).Raycast((px, py, pz), dir_vec, 50, 1)
                if phys_list:
                    phys = phys_list[0]
        return phys

    def on_custom_key_press(self, args):
        """自定义键盘按键"""
        name = args.get('name')
        is_down = args.get('isDown') == '1'
        screen_name = args.get('screenName', '')
        if screen_name != 'hud_screen':
            return
        self._handle_custom_input(name, is_down)
        return

    def on_custom_gamepad_press(self, args):
        """自定义手柄按键"""
        name = args.get('name')
        is_down = args.get('isDown') == '1'
        screen_name = args.get('screenName', '')
        if screen_name != 'hud_screen':
            return
        self._handle_custom_input(name, is_down, is_gamepad=True)
        return

    def _handle_custom_input(self, name, is_down, is_gamepad=False):
        if name == '退出状态':
            if is_down and self.is_in_project:
                if self.phys_state == PhysMode.CATCH:
                    self.phys_state_set_ui.on_catch_block_exit_click()
                elif self.phys_state == PhysMode.SUCK:
                    self.phys_state_set_ui.on_suck_block_exit_click()
                elif self.phys_state == PhysMode.SPRAY:
                    self.phys_state_set_ui.on_spawn_block_exit_click()
                else:
                    self.quit_state()
        elif name == '状态切换右':
            if is_down and not self.is_in_project:
                self.phys_state_ui.on_right_state_change()
        elif name == '状态切换左':
            if is_down and not self.is_in_project:
                self.phys_state_ui.on_left_state_change()
        elif name == '状态确认' and is_gamepad:
            if is_down and not self.is_in_project:
                self.phys_state_ui.on_yes_button()
        elif name == '物理化方块破坏':
            if is_down and self.is_in_project and self.phys_state == PhysMode.INTERACT:
                self.phys_state_set_ui._onInteractLeftClick()
        elif name == '物理化方块交互':
            if is_down and self.is_in_project and self.phys_state == PhysMode.INTERACT:
                self.phys_state_set_ui._onInteractRightClick()
        return

    def on_custom_key_changed(self, args):
        """按键绑定变更"""
        name = args.get('name')
        old_key = args.get('oldKey')
        new_key = args.get('newKey')
        if old_key == new_key:
            return
        if name == '退出状态':
            self._key_data['exit'] = new_key
        elif name == '状态切换左':
            self._key_data['switch_left'] = new_key
        elif name == '状态切换右':
            self._key_data['switch_right'] = new_key
        elif name == '物理化方块破坏':
            self._key_data['destroy_phys_block'] = new_key
        elif name == '物理化方块交互':
            self._key_data['interact_phys_block'] = new_key
        CF.CreateConfigClient(LID).SetConfigData('xiaobo_phys_stimulate_key_data', self._key_data, True)
        return

    def on_custom_gamepad_changed(self, args):
        """手柄按键绑定变更"""
        name = args.get('name')
        old_key = args.get('oldKey')
        new_key = args.get('newKey')
        if old_key == new_key:
            return
        if name == '退出状态':
            self._key_data['exit_gamepad'] = new_key
        elif name == '状态切换左':
            self._key_data['switch_left_gamepad'] = new_key
        elif name == '状态切换右':
            self._key_data['switch_right_gamepad'] = new_key
        elif name == '物理化方块破坏':
            self._key_data['destroy_phys_block_gamepad'] = new_key
        elif name == '物理化方块交互':
            self._key_data['interact_phys_block_gamepad'] = new_key
        CF.CreateConfigClient(LID).SetConfigData('xiaobo_phys_stimulate_key_data', self._key_data, True)
        return

    def update(self):
        """每帧更新选取逻辑"""
        if not self.is_in_project:
            return
        if self.phys_state == PhysMode.SINGLE:
            self._update_single_block()
        elif self.phys_state == PhysMode.REGION:
            self._update_multi_block()
        return

    def _update_single_block(self):
        """单方块模式：高亮方块"""
        pick_data = CF.CreateCamera(LID).PickFacing()
        if pick_data['type'] is not None and pick_data['type'] != 'None':
            hit_x = pick_data['hitPosX']
            hit_y = pick_data['hitPosY']
            hit_z = pick_data['hitPosZ']
            px, py, pz = CF.CreatePos(PID).GetPos()
            dist = Math.point_distance((hit_x, hit_y, hit_z), (px, py, pz))
            if dist > 10:
                self.select_block_pos = None
                self.effect_mgr.block_select.hide_all()
                return
        if pick_data['type'] == 'Block':
            x, y, z = pick_data['x'], pick_data['y'], pick_data['z']
            self.select_block_pos = (x, y, z)
            self.effect_mgr.block_select.switch_to((x, y, z))
        else:
            self.select_block_pos = None
            self.effect_mgr.block_select.hide_all()
        return

    def _update_multi_block(self):
        """多方块模式：根据方向模式选取"""
        ui_node = self.phys_state_set_ui
        step = ui_node.more_block_step
        dir_mode = ui_node.more_block_dir_mode
        if step == 2:
            return
        if dir_mode == 2:
            return
        if dir_mode == 0:
            self._pick_block_by_facing(step)
        elif dir_mode == 1:
            self._pick_block_by_player(step)
        return

    def _pick_block_by_facing(self, step):
        pick_data = CF.CreateCamera(LID).PickFacing()
        if pick_data['type'] is not None and pick_data['type'] != 'None':
            hit_x = pick_data['hitPosX']
            hit_y = pick_data['hitPosY']
            hit_z = pick_data['hitPosZ']
            px, py, pz = CF.CreatePos(PID).GetPos()
            dist = Math.point_distance((hit_x, hit_y, hit_z), (px, py, pz))
            if dist > 50:
                self.select_block_pos = None
                self.effect_mgr.block_select.hide_all()
                return
        if pick_data['type'] == 'Block':
            x, y, z = pick_data['x'], pick_data['y'], pick_data['z']
            self._set_multi_block_select((x, y, z), step)
        else:
            self.select_block_pos = None
            self.effect_mgr.block_select.hide_all()
            if not (step == 1 and self.more_block_from_pos is not None):
                self.effect_mgr.region_select.hide_all()
        return

    def _pick_block_by_player(self, step):
        px, py, pz = CF.CreatePos(PID).GetPos()
        bx = int(math.floor(px))
        by = int(math.floor(py)) - 1
        bz = int(math.floor(pz))
        self._set_multi_block_select((bx, by, bz), step)
        return

    def _set_multi_block_select(self, block_pos, step):
        self.select_block_pos = block_pos
        self.effect_mgr.block_select.switch_to(block_pos)
        if step == 1 and self.more_block_from_pos is not None:
            self.effect_mgr.region_select.show_region(self.more_block_from_pos, block_pos)
        return

    def manual_adjust_pos(self, dx, dy, dz):
        """手动调整选取方块坐标"""
        if self.select_block_pos is None:
            return
        else:
            x, y, z = self.select_block_pos
            self.select_block_pos = (x + dx, y + dy, z + dz)
            self.effect_mgr.block_select.switch_to(self.select_block_pos)
            ui_node = self.phys_state_set_ui
            if ui_node.more_block_step == 1 and self.more_block_from_pos is not None:
                self.effect_mgr.region_select.show_region(self.more_block_from_pos, self.select_block_pos)
            return

