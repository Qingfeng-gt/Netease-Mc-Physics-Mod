# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
# Embedded file name: ValkyrienBE/ValkyrienBEClientSystem.py
"""
ValkyrienBE 客户端系统
薄编排层：创建各 Manager，注册 UI，将引擎事件和服务端自定义事件委派给 Manager 处理。
"""
import mod.client.extraClientApi as clientApi
from ValkyrienBE.modConfig import ModName, ClientSystemName, ServerSystemName, UI_BASE_PATH
from ValkyrienBE.framework.wrapper import SystemHandler, EventHandler
from ValkyrienBE.common import events
from ValkyrienBE.common.constants import PHYS_ITEM_NAME, PHYS_ENTITY_TYPE
from ValkyrienBE.client.RenderManager import RenderManager
from ValkyrienBE.client.EffectManager import EffectManager
from ValkyrienBE.client.InputManager import InputManager
from time import time
ClientSystem = clientApi.GetClientSystemCls()
CF = clientApi.GetEngineCompFactory()
LID = clientApi.GetLevelId()
PID = clientApi.GetLocalPlayerId()

@SystemHandler(ModName, ClientSystemName)
class ValkyrienBEClientSystem(ClientSystem):

    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        self._render_mgr = RenderManager(self)
        self._effect_mgr = EffectManager(self)
        self._input_mgr = InputManager(self, self._render_mgr, self._effect_mgr)
        self._phys_state_ui = None
        self._phys_state_set_ui = None
        self.lastTime = 0.0
        self.screen_current = 'hud.hud_screen'
        return

    @EventHandler('UiInitFinished', priority=0)
    def _on_ui_init(self, args):
        clientApi.RegisterUI(ModName, 'physStateUI', UI_BASE_PATH + 'PhysStateUI.PhysStateUI', 'phys_state_change_hud.main')
        clientApi.RegisterUI(ModName, 'physStateSetUI', UI_BASE_PATH + 'PhysStateSetUI.PhysStateSetUI', 'state_set_hud.main')
        self._phys_state_ui = clientApi.CreateUI(ModName, 'physStateUI', {'isHud': 1})
        self._phys_state_set_ui = clientApi.CreateUI(ModName, 'physStateSetUI', {'isHud': 1})
        self._phys_state_ui.set_input_manager(self._input_mgr)
        self._phys_state_set_ui.set_input_manager(self._input_mgr)
        self._input_mgr.phys_state_ui = self._phys_state_ui
        self._input_mgr.phys_state_set_ui = self._phys_state_set_ui
        eid_list = CF.CreateGame(LID).GetEntitiesAround(PID, 128, {})
        physBlockList = [eid for eid in eid_list if CF.CreateEngineType(eid).GetEngineTypeStr() == PHYS_ENTITY_TYPE]
        self.NotifyToServer(events.C2S_INIT_PHYS_BLOCKS, {'pid': PID, 'entityIdList': physBlockList})
        self._render_mgr.register_weapon_render()
        item = CF.CreateItem(PID).GetCarriedItem()
        item_name = item['newItemName'] if item else None
        self._render_mgr.update_held_item_query(item_name)
        return

    @EventHandler('OnLocalPlayerStopLoading', priority=0)
    def _on_player_stop_loading(self, args):
        return
        self.NotifyToServer(events.C2S_INIT_PHYS_BLOCKS, {'pid': PID})
        self._render_mgr.register_weapon_render()
        item = CF.CreateItem(PID).GetCarriedItem()
        item_name = item['newItemName'] if item else None
        self._render_mgr.update_held_item_query(item_name)
        return

    @EventHandler('OnCarriedNewItemChangedClientEvent', priority=0)
    def _on_carried_item_changed(self, args):
        self._input_mgr.on_carried_item_changed(args)
        return

    @EventHandler('TapBeforeClientEvent', priority=0)
    def _on_tap_before(self, args):
        self._input_mgr.on_tap_before(args)
        return

    @EventHandler('RightClickBeforeClientEvent', priority=0)
    def _on_right_click_before(self, args):
        self._input_mgr.on_right_click_before(args)
        return

    @EventHandler('OnCustomKeyPressInGame', priority=0)
    def _on_custom_key_press(self, args):
        self._input_mgr.on_custom_key_press(args)
        return

    @EventHandler('OnCustomGamepadPressInGame', priority=0)
    def _on_custom_gamepad_press(self, args):
        self._input_mgr.on_custom_gamepad_press(args)
        return

    @EventHandler('OnCustomKeyChangedEvent', priority=0)
    def _on_custom_key_changed(self, args):
        self._input_mgr.on_custom_key_changed(args)
        return

    @EventHandler('OnCustomGamepadChangedEvent', priority=0)
    def _on_custom_gamepad_changed(self, args):
        self._input_mgr.on_custom_gamepad_changed(args)
        return

    @EventHandler('GameRenderTickEvent', priority=0)
    def _on_render_tick(self, args=None):
        now = time()
        if self.lastTime == 0.0:
            self.lastTime = now
            return
        deltaTime = now - self.lastTime
        self.lastTime = now
        self._render_mgr.complementary_frame(deltaTime)
        return

    @EventHandler('OnScriptTickClient', priority=0)
    def _on_script_tick(self, args=None):
        self._render_mgr.sync_phys_rotation()
        return

    @EventHandler('AddEntityClientEvent', priority=0)
    def _on_entity_added_client(self, args):
        entity_id = args.get('id')
        engine_type = args.get('engineTypeStr', '')
        if engine_type == PHYS_ENTITY_TYPE and entity_id not in self._render_mgr.phys_block_palettes:
            self.NotifyToServer(events.C2S_REQUEST_ENTITY_RENDER, {'pid': PID, 'entityId': entity_id})
        return

    @EventHandler('PushScreenEvent', priority=0)
    def _on_push_screen(self, args):
        """判断目前屏幕ui"""
        self.screen_current = args['screenDef']
        return

    @EventHandler('PopScreenAfterClientEvent', priority=0)
    def _on_pop_screen(self, args):
        """处理屏幕弹出事件"""
        self.screen_current = args['screenDef']
        self._input_mgr.on_pop_screen_range_restore()
        return

    @EventHandler(events.S2C_RENDER_BLOCK, namespace=ModName, system_name=ServerSystemName, priority=0)
    def _on_render_block(self, args):
        self._render_mgr.render_block(args)
        return

    @EventHandler(events.S2C_RENDER_BLOCK_BATCH, namespace=ModName, system_name=ServerSystemName, priority=0)
    def _on_render_block_batch(self, args):
        self._render_mgr.render_block_batch(args)
        return

    @EventHandler(events.S2C_ON_CATCH_BLOCK, namespace=ModName, system_name=ServerSystemName, priority=0)
    def _on_catch_block(self, args):
        self._input_mgr.on_catch_block(args)
        return

    @EventHandler(events.S2C_ON_RELEASE_BLOCK, namespace=ModName, system_name=ServerSystemName, priority=0)
    def _on_release_block(self, args):
        self._input_mgr.on_release_block(args)
        return

    @EventHandler(events.S2C_ON_SPRAY_STATE_CHANGED, namespace=ModName, system_name=ServerSystemName, priority=0)
    def _on_spray_state_changed(self, args):
        self._input_mgr.on_spray_state_changed(args)
        return

    @EventHandler(events.S2C_ON_ALL_DELETED, namespace=ModName, system_name=ServerSystemName, priority=0)
    def _on_all_deleted(self, args):
        self._input_mgr.on_all_deleted(args)
        return

    @EventHandler(events.S2C_CONFIRM_STATE, namespace=ModName, system_name=ServerSystemName, priority=0)
    def _on_confirm_state(self, args):
        self._input_mgr.on_confirm_state(args)
        return

    @EventHandler(events.S2C_PLAY_SOUND_PARTICLE, namespace=ModName, system_name=ServerSystemName, priority=0)
    def _on_play_sound_particle(self, args):
        self._render_mgr.play_sound_particle(args)
        return

    @EventHandler(events.S2C_FALLBACK_BLOCK_READY, namespace=ModName, system_name=ServerSystemName, priority=0)
    def _on_fallback_block_ready(self, args):
        self._input_mgr.on_fallback_block_ready(args)
        return

    @EventHandler(events.S2C_RESET_BUTTONS, namespace=ModName, system_name=ServerSystemName, priority=0)
    def _on_reset_buttons(self, args):
        if self._phys_state_ui:
            self._phys_state_ui.ResetAllButtons()
        if self._phys_state_set_ui:
            self._phys_state_set_ui.ResetAllButtons()
        return

    def Update(self):
        self._input_mgr.update()
        return

    def Destroy(self):
        self._effect_mgr.destroy()
        self._render_mgr.destroy()
        return

