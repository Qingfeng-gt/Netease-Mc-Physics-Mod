# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
# Embedded file name: ValkyrienBE/ValkyrienBEServerSystem.py
"""
ValkyrienBE 服务端系统
薄编排层：创建 Store 和各 Manager，将引擎事件和客户端自定义事件委派给 Manager 处理。
"""
import mod.server.extraServerApi as serverApi
CF = serverApi.GetEngineCompFactory()
LID = serverApi.GetLevelId()
from ValkyrienBE.modConfig import ModName, ServerSystemName, ClientSystemName
from ValkyrienBE.framework.wrapper import SystemHandler, EventHandler
from ValkyrienBE.common import events
from ValkyrienBE.common.block_mass import get_block_mass_info, set_custom_mass, remove_custom_mass, get_custom_mass_overrides, load_custom_mass_overrides
from ValkyrienBE.server.PhysicsEntityStore import PhysicsEntityStore
from ValkyrienBE.server.PhysicsEntityManager import PhysicsEntityManager
from ValkyrienBE.server.InteractionManager import InteractionManager
from ValkyrienBE.server.CollisionManager import CollisionManager
from ValkyrienBE.server.PlayerManager import PlayerManager
ServerSystem = serverApi.GetServerSystemCls()
PxForceMode = serverApi.GetMinecraftEnum().PxForceMode

@SystemHandler(ModName, ServerSystemName)
class ValkyrienBEServerSystem(ServerSystem):

    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        self._store = PhysicsEntityStore()
        self._physics_mgr = PhysicsEntityManager(self, self._store)
        self._interaction_mgr = InteractionManager(self, self._store, self._physics_mgr)
        self._collision_mgr = CollisionManager(self, self._store)
        self._player_mgr = PlayerManager(self, self._store)
        self._can_push_physic_block = True
        return

    @EventHandler('LoadServerAddonScriptsAfter', priority=0)
    def _on_scripts_loaded(self, args):
        self._load_custom_mass_from_world()
        self._load_push_permission_from_world()
        self._physics_mgr.preload_entities_from_world()
        return

    @EventHandler('CustomCommandTriggerServerEvent', priority=0)
    def _on_custom_command(self, args):
        """处理自定义指令（/mass query/set/reset、/blockpush）"""
        command = args.get('command', '')
        if command == 'blockpush':
            self._handle_blockpush_command(args)
            return
        if command != 'mass':
            return
        cmd_args = args.get('args', [])
        origin = args.get('origin', {})
        pid = origin.get('entityId', '')
        if not cmd_args:
            return
        sub_cmd = cmd_args[0].get('value', '') if cmd_args else ''
        if sub_cmd == 'query' and len(cmd_args) >= 2:
            block_name = cmd_args[1].get('value', '')
            mass, friction, elasticity = get_block_mass_info(block_name)
            overrides = get_custom_mass_overrides()
            is_custom = block_name in overrides
            suffix = ' §e(自定义)' if is_custom else ' §7(默认)'
            msg = ('§a{} §f质量: §b{:.1f}kg §f摩擦: §b{:.2f} §f弹性: §b{:.2f}{}').format(block_name, mass, friction, elasticity, suffix)
            args['return_msg_key'] = msg
        elif sub_cmd == 'set' and len(cmd_args) >= 3:
            block_name = cmd_args[1].get('value', '')
            mass_val = cmd_args[2].get('value', 0)
            if mass_val < 0:
                args['return_failed'] = True
                args['return_msg_key'] = '§c质量不能为负数'
                return
            set_custom_mass(block_name, float(mass_val))
            self._save_custom_mass_to_world()
            args['return_msg_key'] = ('§a已设置 {} 质量为 §b{:.1f}kg').format(block_name, float(mass_val))
        elif sub_cmd == 'reset' and len(cmd_args) >= 2:
            block_name = cmd_args[1].get('value', '')
            remove_custom_mass(block_name)
            self._save_custom_mass_to_world()
            mass, _, _ = get_block_mass_info(block_name)
            args['return_msg_key'] = ('§a已重置 {} 为默认质量 §b{:.1f}kg').format(block_name, mass)
        else:
            args['return_failed'] = True
            args['return_msg_key'] = '§c用法: /mass query <方块> | /mass set <方块> <质量> | /mass reset <方块>'
        return

    def _handle_blockpush_command(self, args):
        """处理 /blockpush 指令，控制玩家是否能推动物理方块"""
        cmd_args = args.get('args', [])
        enable_str = cmd_args[0].get('value', '')
        self._can_push_physic_block = enable_str
        self._save_push_permission_to_world()
        status_str = '§a已启用' if self._can_push_physic_block else '§c已禁用'
        args['return_msg_key'] = status_str + '§f物理方块推动'
        return

    def _save_custom_mass_to_world(self):
        """保存自定义质量覆盖到世界 ExtraData"""
        extra_comp = CF.CreateExtraData(LID)
        extra_comp.SetExtraData('valkyrien_be_mass', get_custom_mass_overrides(), True)
        return

    def _load_custom_mass_from_world(self):
        """从世界 ExtraData 恢复自定义质量覆盖"""
        extra_comp = CF.CreateExtraData(LID)
        data = extra_comp.GetExtraData('valkyrien_be_mass')
        if data:
            load_custom_mass_overrides(data)
            print ('[ValkyrienBE] Loaded {} custom mass overrides from world').format(len(data))
        return

    def _save_push_permission_to_world(self):
        """保存推动权限标志到世界 ExtraData"""
        extra_comp = CF.CreateExtraData(LID)
        extra_comp.SetExtraData('valkyrien_be_push_permission', self._can_push_physic_block, True)
        return

    def _load_push_permission_from_world(self):
        """从世界 ExtraData 恢复推动权限标志"""
        extra_comp = CF.CreateExtraData(LID)
        data = extra_comp.GetExtraData('valkyrien_be_push_permission')
        if data is not None:
            self._can_push_physic_block = data
        print ('[ValkyrienBE] Push permission: {}').format('enabled' if self._can_push_physic_block else 'disabled')
        return

    @EventHandler('AddEntityServerEvent', priority=0)
    def _on_entity_added(self, args):
        self._physics_mgr.on_entity_added(args)
        return

    @EventHandler('AddServerPlayerEvent', priority=0)
    def _on_player_join(self, args):
        self._player_mgr.on_player_join(args)
        return

    @EventHandler('DelServerPlayerEvent', priority=0)
    def _on_player_leave(self, args):
        self._player_mgr.on_player_leave(args)
        return

    @EventHandler('PhysxTouchServerEvent', priority=0)
    def _on_physx_touch(self, args):
        self._collision_mgr.on_physx_touch(args)
        return

    @EventHandler('PlayerAttackEntityEvent', priority=0)
    def _on_player_attack_entity(self, args):
        self._physics_mgr.on_player_attack_entity(args)
        return

    @EventHandler('ExplosionServerEvent', priority=0)
    def _on_explosion(self, args):
        self._interaction_mgr.on_explosion(args)
        return

    @EventHandler('ServerChatEvent', priority=0)
    def _on_server_chat(self, args):
        self._player_mgr.on_server_chat(args)
        return

    @EventHandler('HealthChangeBeforeServerEvent', priority=0)
    def _on_health_change(self, args):
        self._physics_mgr.on_health_change(args)
        return

    @EventHandler(events.C2S_PHYSIC_BLOCK, namespace=ModName, system_name=ClientSystemName, priority=0)
    def _on_physic_block(self, args):
        self._physics_mgr.physicalize_block(args)
        return

    @EventHandler(events.C2S_PHYSIC_BLOCK_REGION, namespace=ModName, system_name=ClientSystemName, priority=0)
    def _on_physic_block_region(self, args):
        self._physics_mgr.physicalize_region(args)
        return

    @EventHandler(events.C2S_REMOVE_PHYSIC_BLOCK, namespace=ModName, system_name=ClientSystemName, priority=0)
    def _on_remove_physic_block(self, args):
        self._physics_mgr.remove_physic_block(args)
        return

    @EventHandler(events.C2S_DELETE_ALL_PHYS, namespace=ModName, system_name=ClientSystemName, priority=0)
    def _on_delete_all(self, args):
        self._physics_mgr.delete_all(args)
        return

    @EventHandler(events.C2S_CATCH_BLOCK, namespace=ModName, system_name=ClientSystemName, priority=0)
    def _on_catch_block(self, args):
        self._interaction_mgr.catch_block(args)
        return

    @EventHandler(events.C2S_RELEASE_BLOCK, namespace=ModName, system_name=ClientSystemName, priority=0)
    def _on_release_block(self, args):
        self._interaction_mgr.release_block(args)
        return

    @EventHandler(events.C2S_ROTATE_CAUGHT_BLOCK, namespace=ModName, system_name=ClientSystemName, priority=0)
    def _on_rotate_caught_block(self, args):
        self._interaction_mgr.rotate_caught_block(args)
        return

    @EventHandler(events.C2S_SUCK_BLOCK, namespace=ModName, system_name=ClientSystemName, priority=0)
    def _on_suck_block(self, args):
        self._interaction_mgr.suck_block(args)
        return

    @EventHandler(events.C2S_SPRAY_BLOCK, namespace=ModName, system_name=ClientSystemName, priority=0)
    def _on_spray_block(self, args):
        self._interaction_mgr.spray_block(args)
        return

    @EventHandler(events.C2S_INIT_PHYS_BLOCKS, namespace=ModName, system_name=ClientSystemName, priority=0)
    def _on_init_phys_blocks(self, args):
        self._player_mgr.request_init_phys_blocks(args)
        return

    @EventHandler(events.C2S_REQUEST_ENTITY_RENDER, namespace=ModName, system_name=ClientSystemName, priority=0)
    def _on_request_entity_render(self, args):
        self._player_mgr.request_entity_render(args)
        return

    @EventHandler(events.C2S_PLACE_BLOCK_ON_SHIP, namespace=ModName, system_name=ClientSystemName, priority=0)
    def _on_place_block_on_ship(self, args):
        self._physics_mgr.place_block_on_entity(args)
        return

    @EventHandler(events.C2S_DESTROY_BLOCK_ON_SHIP, namespace=ModName, system_name=ClientSystemName, priority=0)
    def _on_destroy_block_on_ship(self, args):
        self._physics_mgr.destroy_block_on_entity(args)
        return

    @EventHandler(events.C2S_REFRESH_SHIP, namespace=ModName, system_name=ClientSystemName, priority=0)
    def _on_refresh_ship(self, args):
        self._physics_mgr.refresh_entity(args.get('entityId', ''))
        return

    @EventHandler(events.C2S_FALLBACK_BLOCK_CONFIRM, namespace=ModName, system_name=ClientSystemName, priority=0)
    def _on_fallback_block_confirm(self, args):
        CF.CreateGame(LID).AddTimer(0, self._physics_mgr.on_fallback_confirm, args)
        return

    @EventHandler(events.C2S_EXIT_INTERACT, namespace=ModName, system_name=ClientSystemName, priority=0)
    def _on_exit_interact(self, args):
        pid = args.get('pid')
        if pid:
            self._physics_mgr.cleanup_player_fallbacks(pid)
        return

    def Update(self):
        self._physics_mgr.update()
        self._interaction_mgr.update()
        self._collision_mgr.update()
        return

    def Destroy(self):
        self._store.clear_all()
        return


