# ValkyrienBE - 物理引擎行为包

## 项目介绍

ValkyrienBE 是一个为 Minecraft Bedrock Edition 开发的物理引擎行为包，旨在为游戏添加真实的物理效果和交互体验。该项目允许玩家创建、操作和与具有物理属性的方块和实体进行交互，为 Minecraft 世界带来更加真实的物理模拟。

## 功能特性

### 核心功能
- **物理方块系统**：将普通方块转换为具有物理属性的实体
- **物理实体管理**：创建、跟踪和管理物理实体
- **玩家交互**：支持抓取、释放、旋转物理方块
- **区域选择**：可以选择一个区域并将其物理化
- **物理属性调整**：通过命令修改方块的质量、摩擦和弹性
- **碰撞检测**：实现物理实体之间的碰撞效果
- **爆炸交互**：物理实体对爆炸的反应

### 命令系统
- `/mass query <方块>` - 查询方块的物理属性
- `/mass set <方块> <质量>` - 设置方块的自定义质量
- `/mass reset <方块>` - 重置方块的质量为默认值
- `/blockpush <true/false>` - 启用或禁用物理方块推动功能

### 客户端功能
- **物理方块渲染**：在客户端正确渲染物理实体
- **UI 界面**：提供物理状态显示和设置界面
- **特效系统**：为物理操作提供视觉反馈
- **输入管理**：处理玩家与物理方块的交互输入

## 安装方法

1. 确保你拥有 Minecraft Bedrock Edition
2. 将整个行为包文件夹复制到 Minecraft 的行为包目录中
3. 在游戏中启用该行为包
4. 创建或加载一个世界，开始体验物理引擎功能

## 使用指南

### 基本操作
1. **创建物理方块**：使用物理刺激棒（phy_stimulate_item）点击方块，将其转换为物理方块
2. **抓取物理方块**：长按物理方块进行抓取
3. **旋转物理方块**：抓取后使用旋转操作调整方块方向
4. **释放物理方块**：松开抓取键释放方块
5. **区域物理化**：使用区域选择工具选择一个区域，然后将其物理化

### 高级操作
1. **调整方块质量**：使用 `/mass set <方块> <质量>` 命令设置方块的质量
2. **启用/禁用推动**：使用 `/blockpush true` 或 `/blockpush false` 命令控制是否可以推动物理方块
3. **在物理实体上放置/破坏方块**：直接在物理实体上进行方块操作

## 技术架构

### 服务端系统
- **ValkyrienBEServerSystem**：服务端主系统，负责协调各管理器
- **PhysicsEntityStore**：物理实体存储
- **PhysicsEntityManager**：物理实体管理
- **InteractionManager**：玩家交互管理
- **CollisionManager**：碰撞检测管理
- **PlayerManager**：玩家管理

### 客户端系统
- **ValkyrienBEClientSystem**：客户端主系统
- **RenderManager**：渲染管理
- **EffectManager**：特效管理
- **InputManager**：输入管理

### 公共组件
- **EventBus**：事件总线
- **SystemRegister**：系统注册
- **block_mass**：方块质量管理
- **events**：事件定义

## 项目结构

```
behavior_pack_physics/
├── ValkyrienBE/           # 主要代码目录
│   ├── client/            # 客户端代码
│   ├── common/            # 公共代码
│   ├── framework/         # 框架代码
│   ├── server/            # 服务器代码
│   ├── ValkyrienBEClientSystem.py  # 客户端主系统
│   ├── ValkyrienBEServerSystem.py  # 服务端主系统
│   ├── modMain.py         # 模块入口
│   └── modConfig.py       # 模块配置
├── effects/               # 效果文件
├── entities/              # 实体文件
├── netease_blocks/        # 网易方块
├── netease_commands/      # 网易命令
├── netease_items_beh/     # 网易物品行为
├── netease_recipes/       # 网易配方
├── structures_netease_merge/  # 结构合并
└── manifest.json          # 项目配置文件
```

## 版本信息

- **当前版本**：0.0.6
- **最低引擎版本**：1.18.0

## 注意事项

- 物理实体数量过多可能会影响游戏性能
- 某些复杂结构可能无法正确物理化
- 请合理使用物理引擎功能，避免创造过于复杂的物理结构

## 未来计划

- 优化物理引擎性能
- 添加更多物理交互效果
- 支持更多方块类型的物理属性
- 增加物理实体的自定义选项

## 许可证

本项目采用 MIT 许可证，详情请参阅 LICENSE 文件。

## 贡献

欢迎提交问题和拉取请求，帮助改进这个项目。

---

**享受物理引擎带来的全新 Minecraft 体验！**