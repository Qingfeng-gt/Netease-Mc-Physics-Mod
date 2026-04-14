# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
# Embedded file name: ValkyrienBE/server/InteractionManager.py
"""
玩家交互管理器
负责：捉捕/释放、磁吸、喷射系统的控制逻辑和每帧更新
"""
import math, random, mod.server.extraServerApi as serverApi
from ValkyrienBE.common.constants import CATCH_MIN_DIST, CATCH_MAX_DIST, CATCH_THROW_SCALE, CATCH_MAX_SPEED, SUCK_RANGE, SUCK_HOLD_DIST, SUCK_SPEED, SUCK_GRAVITY_COMP, SPRAY_MAX_COUNT, SPRAY_SPEED, SPRAY_SPREAD, SPRAY_SPAWN_DIST, STATIC_FRICTION, DYNAMIC_FRICTION, RESTITUTION, CONCRETE_COLORS, PHYS_ENTITY_TYPE, DEFAULT_COLLIDER_STRATEGY, MASS_NORMALIZE, EXPLOSION_RADIUS, EXPLOSION_FORCE, EXPLOSION_UP_BIAS
from ValkyrienBE.common.data_models import PhysicsEntityData, CatchState
from ValkyrienBE.common import events
CF = serverApi.GetEngineCompFactory()
LID = serverApi.GetLevelId()
PxForceMode = serverApi.GetMinecraftEnum().PxForceMode
PxRigidBodyFlag = serverApi.GetMinecraftEnum().PxRigidBodyFlag
PxEventMask = serverApi.GetMinecraftEnum().PxEventMask
_EVENT_MASK = PxEventMask.Server | PxEventMask.Found_Detail | PxEventMask.Lost | PxEventMask.Found
_HALF_SQRT2 = 0.7071067811865476
_ROT90_QUATS = {0: (
     _HALF_SQRT2, 0, 0, _HALF_SQRT2), 
   1: (
     0, _HALF_SQRT2, 0, _HALF_SQRT2), 
   2: (
     0, 0, _HALF_SQRT2, _HALF_SQRT2)}

def _quat_multiply(q1, q2):
    """四元数乘法 q1 * q2，格式 (x, y, z, w)"""
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    return (
     w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
     w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
     w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2)


class InteractionManager(object):
    """玩家交互管理器"""

    def __init__(self, system, store, physics_mgr):
        """
        @param system: ValkyrienBEServerSystem 实例
        @param store: PhysicsEntityStore 实例
        @param physics_mgr: PhysicsEntityManager 实例（喷射时需要保存数据）
        """
        self._system = system
        self._store = store
        self._physics_mgr = physics_mgr
        return

    def catch_block(self, args):
        """捉捕物理化方块"""
        entity_id = args['entityId']
        pid = args['pid']
        if entity_id in self._store._spray_entity_ids:
            CF.CreateGame(pid).SetOneTipMessage(pid, serverApi.GenerateColor('RED') + '喷射方块不可操作')
            return
        if self._store.has_caught(pid):
            CF.CreateGame(pid).SetOneTipMessage(pid, serverApi.GenerateColor('RED') + '你已经捉捕了一个方块, 请先释放')
            return
        if self._store.is_entity_caught(entity_id):
            CF.CreateGame(pid).SetOneTipMessage(pid, serverApi.GenerateColor('RED') + '该方块已被其他玩家捉捕')
            return
        if not self._store.has_entity(entity_id):
            return
        player_pos = CF.CreatePos(pid).GetPos()
        entity_pos = CF.CreatePos(entity_id).GetPos()
        if player_pos and entity_pos:
            dx = entity_pos[0] - player_pos[0]
            dy = entity_pos[1] - (player_pos[1] + 1.62)
            dz = entity_pos[2] - player_pos[2]
            hold_dist = math.sqrt(dx * dx + dy * dy + dz * dz)
            hold_dist = max(CATCH_MIN_DIST, min(hold_dist, CATCH_MAX_DIST))
        else:
            hold_dist = 5.0
        phys_comp = CF.CreatePhysx(entity_id)
        phys_comp.SetRigidBodyFlag(PxRigidBodyFlag.eKINEMATIC, True)
        current_quat = phys_comp.GetQuaternion() or (0, 0, 0, 1)
        catch_state = CatchState(entity_id=entity_id, prev_pos=entity_pos, last_pos=entity_pos, hold_dist=hold_dist, target_quat=current_quat)
        self._store.set_caught(pid, catch_state)
        CF.CreateGame(pid).SetOneTipMessage(pid, serverApi.GenerateColor('GREEN') + '已捉捕方块! 右键释放')
        self._system.NotifyToClient(pid, events.S2C_ON_CATCH_BLOCK, {'entityId': entity_id})
        return

    def release_block(self, args):
        """释放捉捕的方块"""
        pid = args['pid']
        catch_state = self._store.get_caught(pid)
        if not catch_state:
            return
        entity_id = catch_state.entity_id
        phys_comp = CF.CreatePhysx(entity_id)
        phys_comp.SetRigidBodyFlag(PxRigidBodyFlag.eKINEMATIC, False)
        last_pos = catch_state.last_pos
        prev_pos = catch_state.prev_pos
        if last_pos and prev_pos:
            throw_vel = ((last_pos[0] - prev_pos[0]) * CATCH_THROW_SCALE,
             (last_pos[1] - prev_pos[1]) * CATCH_THROW_SCALE,
             (last_pos[2] - prev_pos[2]) * CATCH_THROW_SCALE)
            speed = math.sqrt(throw_vel[0] ** 2 + throw_vel[1] ** 2 + throw_vel[2] ** 2)
            if speed > CATCH_MAX_SPEED:
                s = CATCH_MAX_SPEED - speed
                throw_vel = (throw_vel[0] * s, throw_vel[1] * s, throw_vel[2] * s)
            phys_comp.AddForce(throw_vel, PxForceMode.eVELOCITY_CHANGE)
        self._store.remove_caught(pid)
        self._system.NotifyToClient(pid, events.S2C_ON_RELEASE_BLOCK, {'entityId': entity_id})
        return

    def rotate_caught_block(self, args):
        """旋转捉捕中的方块90度"""
        pid = args['pid']
        axis = args.get('axis', 1)
        catch_state = self._store.get_caught(pid)
        if not catch_state:
            return
        else:
            rot_quat = _ROT90_QUATS.get(axis)
            if not rot_quat:
                return
            current = catch_state.target_quat
            if current is None:
                current = CF.CreatePhysx(catch_state.entity_id).GetQuaternion()
                if not current:
                    current = (0, 0, 0, 1)
            catch_state.target_quat = _quat_multiply(current, rot_quat)
            return

    def suck_block(self, args):
        """切换磁吸状态"""
        pid = args['pid']
        state = args['state']
        if state:
            self._store.add_sucking(pid)
            CF.CreateGame(pid).SetOneTipMessage(pid, serverApi.GenerateColor('GREEN') + '磁吸已开启')
        else:
            self._store.remove_sucking(pid)
            CF.CreateGame(pid).SetOneTipMessage(pid, serverApi.GenerateColor('YELLOW') + '磁吸已关闭')
        return

    def spray_block(self, args):
        """切换喷射状态"""
        pid = args['pid']
        state = args['state']
        if state:
            if self._ensure_concrete_palettes(pid):
                self._store.add_spraying(pid)
                CF.CreateGame(pid).SetOneTipMessage(pid, serverApi.GenerateColor('GREEN') + '喷射已开启')
            else:
                CF.CreateGame(pid).SetOneTipMessage(pid, serverApi.GenerateColor('RED') + '混凝土调色板初始化失败')
                self._system.NotifyToClient(pid, events.S2C_ON_SPRAY_STATE_CHANGED, {'state': False})
        else:
            self._store.remove_spraying(pid)
            CF.CreateGame(pid).SetOneTipMessage(pid, serverApi.GenerateColor('YELLOW') + '喷射已关闭')
        return

    def _ensure_concrete_palettes(self, pid):
        """初始化 16 色混凝土调色板缓存"""
        if self._store._concrete_palettes:
            return True
        dimension_id = CF.CreateDimension(pid).GetEntityDimensionId()
        player_pos = CF.CreatePos(pid).GetPos()
        if not player_pos:
            return False
        temp_pos = (int(player_pos[0]), 300, int(player_pos[2]))
        block_info_comp = CF.CreateBlockInfo(LID)
        block_comp = CF.CreateBlock(LID)
        for aux in range(16):
            block_dict = {'name': 'minecraft:concrete', 'aux': aux}
            block_info_comp.SetBlockNew(temp_pos, block_dict, 0, dimension_id, True)
            palette = block_comp.GetBlockPaletteBetweenPos(dimension_id, temp_pos, temp_pos)
            if palette:
                palette_data = palette.SerializeBlockPalette()
                palette_name = ('concrete_{}').format(CONCRETE_COLORS[aux])
                self._store._concrete_palettes[aux] = {'paletteData': palette_data, 
                   'paletteName': palette_name}

        air_dict = {'name': 'minecraft:air', 'aux': 0}
        block_info_comp.SetBlockNew(temp_pos, air_dict, 0, dimension_id, True)
        return bool(self._store._concrete_palettes)

    def update(self):
        """每帧调用"""
        self._update_caught_entities()
        self._update_sucking_players()
        self._update_spraying_players()
        return

    def _update_caught_entities(self):
        """每帧更新被捉捕方块跟随玩家准心"""
        remove_list = []
        for pid, catch_state in self._store.get_all_caught().items():
            entity_id = catch_state.entity_id
            player_pos = CF.CreatePos(pid).GetPos()
            entity_pos = CF.CreatePos(entity_id).GetPos()
            if not player_pos or not entity_pos:
                remove_list.append(pid)
                continue
            catch_state.prev_pos = catch_state.last_pos
            catch_state.last_pos = entity_pos
            rot = CF.CreateRot(pid).GetRot()
            if not rot:
                continue
            look_dir = serverApi.GetDirFromRot(rot)
            lx, ly, lz = look_dir
            hold_dist = catch_state.hold_dist
            eye_y = player_pos[1] + 1.62
            target_pos = (
             player_pos[0] + lx * hold_dist,
             eye_y + ly * hold_dist,
             player_pos[2] + lz * hold_dist)
            phys_comp = CF.CreatePhysx(entity_id)
            phys_comp.SetKinematicTarget(target_pos, catch_state.target_quat)

        for pid in remove_list:
            catch_state = self._store.get_caught(pid)
            if catch_state:
                entity_id = catch_state.entity_id
                try:
                    phys_comp = CF.CreatePhysx(entity_id)
                    phys_comp.SetRigidBodyFlag(PxRigidBodyFlag.eKINEMATIC, False)
                except:
                    pass

                self._store.remove_caught(pid)
                self._system.NotifyToClient(pid, events.S2C_ON_RELEASE_BLOCK, {'entityId': entity_id})

        return

    def _update_sucking_players(self):
        """每帧为磁吸玩家吸引周围物理方块"""
        remove_list = []
        for pid in list(self._store.get_sucking_players()):
            player_pos = CF.CreatePos(pid).GetPos()
            if not player_pos:
                remove_list.append(pid)
                continue
            rot = CF.CreateRot(pid).GetRot()
            if not rot:
                continue
            look_dir = serverApi.GetDirFromRot(rot)
            lx, ly, lz = look_dir
            eye_x, eye_y, eye_z = player_pos[0], player_pos[1], player_pos[2]
            target_x = eye_x + lx * SUCK_HOLD_DIST
            target_y = eye_y + ly * SUCK_HOLD_DIST
            target_z = eye_z + lz * SUCK_HOLD_DIST
            for entity_id in list(self._store.get_all_entities().keys()):
                if self._store.is_entity_caught(entity_id):
                    continue
                e_pos = CF.CreatePos(entity_id).GetPos()
                if not e_pos:
                    continue
                dx = e_pos[0] - eye_x
                dy = e_pos[1] - eye_y
                dz = e_pos[2] - eye_z
                dist = math.sqrt(dx * dx + dy * dy + dz * dz)
                if dist < 0.1 or dist > SUCK_RANGE:
                    continue
                entity_data = self._store.get_entity(entity_id)
                if entity_data and entity_data.total_mass > 0:
                    mass_factor = MASS_NORMALIZE - entity_data.total_mass
                else:
                    mass_factor = 1.0
                to_target_x = target_x - e_pos[0]
                to_target_y = target_y - e_pos[1]
                to_target_z = target_z - e_pos[2]
                t_dist = math.sqrt(to_target_x ** 2 + to_target_y ** 2 + to_target_z ** 2)
                phys_comp = CF.CreatePhysx(entity_id)
                motion_comp = CF.CreateActorMotion(entity_id)
                motion = motion_comp.GetMotion()
                if t_dist < 0.15:
                    des_vx = des_vy = des_vz = 0.0
                else:
                    des_speed = SUCK_SPEED * min(t_dist - 3.0, 1.0)
                    des_vx = (to_target_x - t_dist) * des_speed
                    des_vy = (to_target_y - t_dist) * des_speed
                    des_vz = (to_target_z - t_dist) * des_speed
                if motion:
                    cur_vx = motion[0] * 30.0
                    cur_vy = motion[1] * 30.0
                    cur_vz = motion[2] * 30.0
                    corr_x = des_vx - cur_vx
                    corr_y = des_vy - cur_vy + SUCK_GRAVITY_COMP
                    corr_z = des_vz - cur_vz
                else:
                    corr_x = des_vx
                    corr_y = des_vy + SUCK_GRAVITY_COMP
                    corr_z = des_vz
                phys_comp.AddForce((
                 corr_x * mass_factor, corr_y * mass_factor, corr_z * mass_factor), PxForceMode.eVELOCITY_CHANGE)

        for pid in remove_list:
            self._store.remove_sucking(pid)

        return

    def _update_spraying_players(self):
        """每帧为喷射玩家生成混凝土物理方块"""
        concrete_palettes = self._store._concrete_palettes
        spraying_players = self._store.get_spraying_players()
        if not concrete_palettes or not spraying_players:
            return
        if len(self._store._spray_entity_ids) >= SPRAY_MAX_COUNT:
            for pid in list(spraying_players):
                CF.CreateGame(pid).SetOneTipMessage(pid, serverApi.GenerateColor('RED') + ('喷射方块已达上限({})').format(SPRAY_MAX_COUNT))
                self._system.NotifyToClient(pid, events.S2C_ON_SPRAY_STATE_CHANGED, {'state': False})

            spraying_players.clear()
            return
        else:
            remove_list = []
            for pid in list(spraying_players):
                player_pos = CF.CreatePos(pid).GetPos()
                if not player_pos:
                    remove_list.append(pid)
                    continue
                rot = CF.CreateRot(pid).GetRot()
                if not rot:
                    continue
                look_dir = serverApi.GetDirFromRot(rot)
                lx, ly, lz = look_dir
                eye_x = player_pos[0]
                eye_y = player_pos[1] + 1.62
                eye_z = player_pos[2]
                dimension_id = CF.CreateDimension(pid).GetEntityDimensionId()
                color_idx = random.randint(0, 15)
                cache_data = concrete_palettes.get(color_idx)
                if not cache_data:
                    continue
                spawn_pos = (eye_x + lx * SPRAY_SPAWN_DIST + (random.random() - 0.5) * 0.3,
                 eye_y + ly * SPRAY_SPAWN_DIST + (random.random() - 0.5) * 0.3,
                 eye_z + lz * SPRAY_SPAWN_DIST + (random.random() - 0.5) * 0.3)
                _CONCRETE_FRICTION = 0.4
                _CONCRETE_ELASTICITY = 0.0
                _CONCRETE_MASS = 2400.0
                concrete_aabb = ((0, 0.5, 0), (0.5, 0.5, 0.5),
                 _CONCRETE_FRICTION, _CONCRETE_FRICTION, _CONCRETE_ELASTICITY)
                self._store.enqueue_pending_entity([
                 concrete_aabb], region_size=None, render_offset=(0, 0, 0), collider_strategy=DEFAULT_COLLIDER_STRATEGY)
                entity_id = None
                while not entity_id:
                    entity_id = self._system.CreateEngineEntityByTypeStr(PHYS_ENTITY_TYPE, spawn_pos, (0,
                                                                                                       0), dimension_id)

                vx = (lx + (random.random() - 0.5) * SPRAY_SPREAD) * SPRAY_SPEED
                vy = (ly + (random.random() - 0.5) * SPRAY_SPREAD) * SPRAY_SPEED
                vz = (lz + (random.random() - 0.5) * SPRAY_SPREAD) * SPRAY_SPEED
                phys_comp = CF.CreatePhysx(entity_id)
                phys_comp.AddForce((vx, vy, vz), PxForceMode.eVELOCITY_CHANGE)
                palette_data = cache_data['paletteData']
                palette_name = cache_data['paletteName']
                entity_data = PhysicsEntityData(palette_data=palette_data, dimension_id=dimension_id, palette_offset=(-0.5,
                                                                                                                      0,
                                                                                                                      -0.5), aabb_list=[
                 concrete_aabb], palette_name=palette_name, is_region=False, region_size=None, render_offset=(0,
                                                                                                              0,
                                                                                                              0), collider_strategy=DEFAULT_COLLIDER_STRATEGY, total_mass=_CONCRETE_MASS)
                self._store.add_entity(entity_id, entity_data)
                self._store._spray_entity_ids.add(entity_id)
                self._physics_mgr.save_entity_extra_data(entity_id)
                render_data = entity_data.to_render_dict(entity_id)
                self._system.BroadcastToAllClient(events.S2C_RENDER_BLOCK, render_data)

            for pid in remove_list:
                self._store.remove_spraying(pid)

            return

    def on_explosion(self, args):
        """
        爆炸事件回调：对范围内的物理化方块施加冲击力。
        力大小与距离平方成反比，附带向上偏移模拟抛飞效果。
        @param args: ExplosionServerEvent 参数
        """
        explode_pos = args.get('explodePos')
        dimension_id = args.get('dimensionId', 0)
        if not explode_pos:
            return
        ex, ey, ez = explode_pos
        radius_sq = EXPLOSION_RADIUS * EXPLOSION_RADIUS
        for entity_id, entity_data in self._store.get_all_entities().items():
            if entity_data.dimension_id != dimension_id:
                continue
            entity_pos = CF.CreatePos(entity_id).GetPos()
            if not entity_pos:
                continue
            dx = entity_pos[0] - ex
            dy = entity_pos[1] - ey
            dz = entity_pos[2] - ez
            dist_sq = dx * dx + dy * dy + dz * dz
            if dist_sq > radius_sq or dist_sq < 0.01:
                continue
            dist = math.sqrt(dist_sq)
            strength = EXPLOSION_FORCE - dist
            nx, ny, nz = dx - dist, dy - dist, dz - dist
            ny += EXPLOSION_UP_BIAS
            fx = nx * strength
            fy = ny * strength
            fz = nz * strength
            phys_comp = CF.CreatePhysx(entity_id)
            phys_comp.AddForce((fx, fy, fz), PxForceMode.eVELOCITY_CHANGE)

        return

