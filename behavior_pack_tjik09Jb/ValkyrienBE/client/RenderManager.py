"""
渲染管理器
负责：物理方块的调色板渲染、旋转同步（补帧插值）、武器模型注册
"""
import math
import mod.client.extraClientApi as clientApi
from mod.common.utils.mcmath import Quaternion
from ValkyrienBE.common.block_sounds_dict import BLOCKSOUNDS

CF = clientApi.GetEngineCompFactory()
LID = clientApi.GetLevelId()
PID = clientApi.GetLocalPlayerId()


def _calculate_corrected_position(rotation, pivot_offset=(0, 0.5, 0)):
    """
    计算修正后的客户端位置偏移，以抵消旋转中心不一致带来的偏差。
    旋转应用顺序: Z → X → Y (与 SetActorBlockGeometryRotation 一致)

    @param rotation: (rx, ry, rz) 角度制欧拉角
    @param pivot_offset: 客户端渲染中心相对于刚体中心的偏移
    @return: (dx, dy, dz) 需要叠加到渲染偏移上的修正量
    """
    rx, ry, rz = rotation
    off_x, off_y, off_z = pivot_offset

    # 角度转弧度
    rad_x = math.radians(rx)
    rad_y = math.radians(ry)
    rad_z = math.radians(rz)

    # Z轴旋转
    sin_z, cos_z = math.sin(rad_z), math.cos(rad_z)
    x1 = off_x * cos_z - off_y * sin_z
    y1 = off_x * sin_z + off_y * cos_z
    z1 = off_z

    # X轴旋转
    sin_x, cos_x = math.sin(rad_x), math.cos(rad_x)
    x2 = x1
    y2 = y1 * cos_x - z1 * sin_x
    z2 = y1 * sin_x + z1 * cos_x

    # Y轴旋转
    sin_y, cos_y = math.sin(rad_y), math.cos(rad_y)
    rotated_x = x2 * cos_y + z2 * sin_y
    rotated_y = y2
    rotated_z = -x2 * sin_y + z2 * cos_y

    return (rotated_x - off_x, rotated_y - off_y, rotated_z - off_z)


def _quat_to_euler(order, quat):
    """
    四元数 → 欧拉角（角度制）
    @param order: 旋转顺序字符串，如 'zxy'
    @param quat: (x, y, z, w)
    @return: (x_deg, y_deg, z_deg)
    """
    x, y, z, w = quat

    # 旋转矩阵元素
    r00 = 1 - 2 * (y * y + z * z)
    r01 = 2 * (x * y - z * w)
    r02 = 2 * (x * z + y * w)
    r10 = 2 * (x * y + z * w)
    r11 = 1 - 2 * (x * x + z * z)
    r12 = 2 * (y * z - x * w)
    r20 = 2 * (x * z - y * w)
    r21 = 2 * (y * z + x * w)
    r22 = 1 - 2 * (x * x + y * y)

    order = order.lower()
    if order == 'zxy':
        # 万向锁处理
        x_ang = math.asin(max(-1, min(1, abs(r21) - 0.0000001)))  # clamp
        # 实际是：x_ang = math.asin(-r21) 的万向锁安全版本
        if abs(r21) <= 0.9999999:
            x_ang = math.asin(-r21)
            z_ang = math.atan2(r01, r11)
            y_ang = math.atan2(r20, r22)
        else:
            x_ang = math.asin(-r21)
            z_ang = 0
            y_ang = math.atan2(-r02, r00)
        x_ang = math.degrees(x_ang)
        z_ang = math.degrees(z_ang)
        y_ang = math.degrees(y_ang)
        return (x_ang, y_ang, z_ang)
    else:
        # 默认处理
        return (0, 0, 0)


class PhysBlockSkeleton(object):
    """物理方块骨骼数据"""

    def __init__(self, entity_id, palette_name, offset):
        self.entity_id = entity_id
        self.palette_name = palette_name
        self.offset = offset
        self.prev_rot = (0, 0, 0)
        self.target_rot = (0, 0, 0)
        self.current_rot = (0, 0, 0)
        self.prev_pos = (0, 0, 0)
        self.target_pos = (0, 0, 0)
        self.current_pos = (0, 0, 0)
        self.lerp_t = 1.0

    def update_from_physics(self):
        """从物理引擎同步数据，更新旋转目标"""
        # comp = CF.CreateTransform(LID)
        # rot_quat = comp.GetRotation(self.entity_id)
        comp = CF.CreatePhysx(self.entity_id)
        rot_quat=comp.GetQuaternion()
        if rot_quat:
            euler = _quat_to_euler('zxy', rot_quat)
            euler = tuple(a % 360.0 for a in euler)
            self.set_target_rotation(euler)

        # pos = comp.GetPos(self.entity_id)
        pos = CF.CreatePos(self.entity_id).GetPos()
        if pos:
            self.prev_pos = self.target_pos
            self.target_pos = tuple(pos)

    def update_render_tick(self, delta_time):
        """每渲染帧更新插值"""
        if self.lerp_t >= 1.0:
            return

        self.lerp_t = min(1.0, self.lerp_t + delta_time * 20)  # 约 20Hz 补帧
        t = self.lerp_t

        self.current_rot = tuple(
            self.lerp_angle(self.prev_rot[i], self.target_rot[i], t)
            for i in range(3)
        )
        self.current_pos = tuple(
            self.prev_pos[i] + (self.target_pos[i] - self.prev_pos[i]) * t
            for i in range(3)
        )

        # 应用旋转
        self.apply_rotation(self.current_rot)

        # 应用位置偏移修正
        corrected = _calculate_corrected_position(self.current_rot, self.offset)
        # comp = CF.CreateTransform(LID)
        # comp.SetPos(self.entity_id, tuple(
        #     self.current_pos[i] + corrected[i] for i in range(3)
        # ))
        comp=CF.CreatePos(self.entity_id)
        comp.SetPosForClientEntity(tuple(
             self.current_pos[i] + corrected[i] for i in range(3)
        ))

    def set_target_rotation(self, euler_angles):
        """设置目标旋转角度（角度制）"""
        self.prev_rot = self.current_rot
        self.target_rot = tuple(a % 360.0 for a in euler_angles)
        self.lerp_t = 0.0

    def apply_rotation(self, euler_angles):
        """将欧拉角应用到方块几何体"""
        comp = CF.CreateActorBlockGeometry(LID)
        rx, ry, rz = euler_angles
        comp.SetActorBlockGeometryRotation(self.entity_id, (rx, ry, rz))

    @staticmethod
    def lerp_angle(start, target, t):
        """角度线性插值，处理 360° 环绕"""
        diff = target - start
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360
        return start + diff * t


class RenderManager(object):
    """渲染管理器"""

    def __init__(self, system):
        self.system = system
        self._skeletons = {}      # entity_id -> PhysBlockSkeleton
        self._palette_names = {}   # entity_id -> palette_name
        self._weapon_render_registered = False

    @property
    def phys_block_palettes(self):
        return {eid: sk.palette_name for eid, sk in self._skeletons.items()}

    def render_block(self, args):
        """渲染单个物理方块"""
        entity_id = args.get('entity_id', '')
        palette_name = args.get('palette_name', '')
        offset = args.get('offset', (0, 0.5, 0))

        if entity_id in self._skeletons:
            return

        skeleton = PhysBlockSkeleton(entity_id, palette_name, offset)
        self._skeletons[entity_id] = skeleton
        self._palette_names[entity_id] = palette_name

        self._check_entity_and_add_geometry(args)

    def render_block_batch(self, args):
        """批量渲染物理方块"""
        blocks = args.get('blocks', [])
        for block_args in blocks:
            self.render_block(block_args)

    def _check_entity_and_add_geometry(self, args):
        """检查实体并添加方块几何体"""
        entity_id = args.get('entity_id', '')
        palette_name = args.get('palette_name', '')

        comp = CF.CreateActorType(LID)
        if not comp.GetEntityType(entity_id):
            # 实体尚未创建，延迟重试
            CF.CreateGame(LID).AddTimer(0.1, self._check_entity_and_add_geometry, args)
            return

        self._open_render(args)

    def _open_render(self, args):
        """开启方块渲染"""
        entity_id = args.get('entity_id', '')
        palette_name = args.get('palette_name', '')

        comp = CF.CreateActorBlockGeometry(LID)
        comp.AddActorBlockGeometryModel(entity_id, palette_name)

        self._hot_swap_palette(entity_id, args)

    def _hot_swap_palette(self, entity_id, args):
        """热替换调色板"""
        palette_name = args.get('palette_name', '')

        comp_geom = CF.CreateActorBlockGeometry(LID)
        comp_geom.SetActorBlockGeometryModel(entity_id, palette_name)

        offset = args.get('offset', (0, 0.5, 0))
        comp_geom.SetActorBlockGeometryOffset(entity_id, offset)

        # 尝试设置旋转（如果有的话）
        rotation = args.get('rotation')
        if rotation:
            comp_geom.SetActorBlockGeometryRotation(entity_id, rotation)

        # 设置缩放
        scale = args.get('scale', 1.0)
        comp_geom.SetActorBlockGeometryScale(entity_id, scale)

    def _delecte_old_geometry(self, args):
        """删除旧的几何体（注意：原文方法名拼写为 delecte）"""
        entity_id = args.get('entity_id', '')

        comp = CF.CreateActorBlockGeometry(LID)
        comp.RemoveActorBlockGeometryModel(entity_id)

        if entity_id in self._skeletons:
            del self._skeletons[entity_id]
        if entity_id in self._palette_names:
            del self._palette_names[entity_id]

    def sync_phys_rotation(self):
        """同步物理旋转数据"""
        for skeleton in self._skeletons.values():
            skeleton.update_from_physics()

    def complementary_frame(self, delta_time):
        """补帧插值渲染"""
        for skeleton in self._skeletons.values():
            skeleton.update_render_tick(delta_time)

    def register_weapon_render(self):
        """注册武器渲染"""
        if self._weapon_render_registered:
            return
        self._weapon_render_registered = True

        comp = CF.CreateItem(LID)
        comp.SetCustomItemModel('minecraft:diamond_sword', 'weapon_model_sword')

        comp2 = CF.CreateItem(LID)
        comp2.SetCustomItemModel('minecraft:bow', 'weapon_model_bow')

        comp3 = CF.CreateItem(LID)
        comp3.SetCustomItemModel('minecraft:trident', 'weapon_model_trident')

    def update_held_item_query(self, item_name):
        """更新手持物品查询"""
        comp = CF.CreateGame(LID)
        # 根据手持物品更新渲染状态
        pass

    def play_sound_particle(self, args):
        """播放方块音效和粒子"""
        action = args.get('action', '')
        block_name = args.get('block_name', '')
        pos = args.get('pos', (0, 0, 0))
        pos = tuple(pos)
        pid = args.get('pid', PID)

        short_name = block_name.replace('minecraft:', '')
        sound_type = BLOCKSOUNDS.get(short_name, 'stone')

        audio_comp = CF.CreateCustomAudio(LID)

        if pid == PID:
            CF.CreatePlayer(PID).Swing()

        if action == 'place':
            sound_name = 'dig.{}'.format(sound_type)
            audio_comp.PlayCustomMusic(sound_name, pos, 1.0, 1.0, False, None)
        elif action == 'destroy':
            sound_name = 'dig.{}'.format(sound_type)
            audio_comp.PlayCustomMusic(sound_name, pos, 1.0, 1.0, False, None)

            block_aux = args.get('block_aux', 0)
            block_info_comp = CF.CreateBlockInfo(LID)
            block_info_comp.AddTerrainDestroyParticleEffect(block_name, block_aux, pos)

            CF.CreateGame(LID).AddTimer(
                1 - 10,
                self._stop_particles,
                {'pos': pos, 'block_name': block_name, 'block_aux': block_aux}
            )

    def _stop_particles(self, args):
        """停止粒子效果"""
        pos = args.get('pos', (0, 0, 0))
        block_name = args.get('block_name', '')
        block_aux = args.get('block_aux', 0)

        block_info_comp = CF.CreateBlockInfo(LID)
        block_info_comp.RemoveTerrainDestroyParticleEffect(block_name, block_aux, pos)

    def on_all_deleted(self, args):
        """所有物理方块被删除后清理本地缓存"""
        count = args.get('count', 0)
        self._skeletons.clear()
        CF.CreateGame(PID).SetTipMessage(
            clientApi.GenerateColor('GREEN') + '已删除 {} 个物理方块'.format(count)
        )

    def destroy(self):
        """销毁"""
        self._skeletons.clear()
        self._palette_names.clear()
