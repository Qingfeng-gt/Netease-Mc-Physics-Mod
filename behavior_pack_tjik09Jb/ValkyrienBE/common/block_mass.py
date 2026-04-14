# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
# Embedded file name: ValkyrienBE/common/block_mass.py
"""
方块质量数据表
数据来源: Valkyrien Skies 2 (vs_mass)
映射为基岩版方块名称

每个条目格式: (mass_kg, friction, elasticity)
- mass: 质量(kg), 基于真实材料密度
- friction: 摩擦系数, 同时用于静摩擦和动摩擦
- elasticity: 弹性系数(回弹), 用作 PhysX restitution
"""
DEFAULT_BLOCK_MASS = 1000.0
DEFAULT_BLOCK_FRICTION = 0.5
DEFAULT_BLOCK_ELASTICITY = 0.0
_F = DEFAULT_BLOCK_FRICTION
_E = DEFAULT_BLOCK_ELASTICITY
_COLORS = [
 4, 5, 6, 7, 8, 9, 
 10, 11, 12, 13, 14, 15, 
 16, 17, 18, 19]
_OVERWORLD_WOODS = [
 20, 21, 22, 23, 24, 
 25, 26, 27, 28]
_NETHER_WOODS = [
 'crimson', 'warped']
_ALL_WOOD_NAMES = _OVERWORLD_WOODS + _NETHER_WOODS + ['bamboo']
_BLOCK_MASS_TABLE = {'minecraft:air': (
                   0.0, _F, _E), 
   'minecraft:barrier': (
                       0.1, _F, _E), 
   'minecraft:command_block': (
                             0.1, _F, _E), 
   'minecraft:chain_command_block': (
                                   0.1, _F, _E), 
   'minecraft:repeating_command_block': (
                                       0.1, _F, _E), 
   'minecraft:structure_block': (
                               0.1, _F, _E), 
   'minecraft:fire': (
                    0.1, _F, _E), 
   'minecraft:soul_fire': (
                         0.1, _F, _E), 
   'minecraft:portal': (
                      0.1, _F, _E), 
   'minecraft:end_portal': (
                          0.1, _F, _E), 
   'minecraft:end_gateway': (
                           0.1, _F, _E), 
   'minecraft:bedrock': (
                       3000.0, 0.8, _E), 
   'minecraft:iron_block': (
                          7850.0, 0.2, _E), 
   'minecraft:iron_bars': (
                         250.0, 0.2, _E), 
   'minecraft:iron_door': (
                         750.0, 0.35, _E), 
   'minecraft:iron_trapdoor': (
                             1000.0, 0.35, _E), 
   'minecraft:heavy_weighted_pressure_plate': (
                                             500.0, _F, _E), 
   'minecraft:chain': (
                     50.0, 0.7, _E), 
   'minecraft:copper_block': (
                            9000.0, 0.2, _E), 
   'minecraft:exposed_copper': (
                              9000.0, 0.25, _E), 
   'minecraft:weathered_copper': (
                                9000.0, 0.3, _E), 
   'minecraft:oxidized_copper': (
                               9000.0, 0.35, _E), 
   'minecraft:waxed_copper': (
                            9000.0, 0.15, _E), 
   'minecraft:waxed_exposed_copper': (
                                    9000.0, 0.2, _E), 
   'minecraft:waxed_weathered_copper': (
                                      9000.0, 0.25, _E), 
   'minecraft:waxed_oxidized_copper': (
                                     9000.0, 0.3, _E), 
   'minecraft:coal_block': (
                          1500.0, 0.7, _E), 
   'minecraft:gold_block': (
                          19300.0, 0.2, _E), 
   'minecraft:light_weighted_pressure_plate': (
                                             1000.0, _F, _E), 
   'minecraft:redstone_block': (
                              3000.0, 0.4, _E), 
   'minecraft:emerald_block': (
                             2750.0, 0.1, _E), 
   'minecraft:lapis_block': (
                           2750.0, 0.5, _E), 
   'minecraft:diamond_block': (
                             3500.0, 0.1, _E), 
   'minecraft:netherite_block': (
                               89680.0, 0.2, _E), 
   'minecraft:amethyst_block': (
                              2650.0, 1.0, _E), 
   'minecraft:stone': (
                     2500.0, 0.6, _E), 
   'minecraft:stone_stairs': (
                            1875.0, 0.6, _E), 
   'minecraft:normal_stone_stairs': (
                                   1875.0, 0.6, _E), 
   'minecraft:normal_stone_slab': (
                                 1250.0, 0.6, _E), 
   'minecraft:stone_pressure_plate': (
                                    100.0, _F, _E), 
   'minecraft:stone_button': (
                            30.0, _F, _E), 
   'minecraft:andesite': (
                        2500.0, 0.6, _E), 
   'minecraft:andesite_stairs': (
                               1875.0, 0.6, _E), 
   'minecraft:andesite_slab': (
                             1250.0, 0.6, _E), 
   'minecraft:andesite_wall': (
                             1250.0, 0.6, _E), 
   'minecraft:polished_andesite': (
                                 2500.0, 0.4, _E), 
   'minecraft:polished_andesite_stairs': (
                                        1875.0, 0.5, _E), 
   'minecraft:polished_andesite_slab': (
                                      1250.0, 0.4, _E), 
   'minecraft:basalt': (
                      3000.0, 0.6, _E), 
   'minecraft:smooth_basalt': (
                             3000.0, 0.5, _E), 
   'minecraft:polished_basalt': (
                               3000.0, 0.4, _E), 
   'minecraft:blackstone': (
                          3500.0, 0.7, _E), 
   'minecraft:gilded_blackstone': (
                                 3600.0, 0.7, _E), 
   'minecraft:blackstone_stairs': (
                                 2625.0, 0.7, _E), 
   'minecraft:blackstone_slab': (
                               1750.0, 0.7, _E), 
   'minecraft:blackstone_wall': (
                               1750.0, 0.7, _E), 
   'minecraft:chiseled_polished_blackstone': (
                                            3500.0, 0.6, _E), 
   'minecraft:polished_blackstone': (
                                   3500.0, 0.5, _E), 
   'minecraft:polished_blackstone_stairs': (
                                          2625.0, 0.5, _E), 
   'minecraft:polished_blackstone_slab': (
                                        1750.0, 0.5, _E), 
   'minecraft:polished_blackstone_wall': (
                                        1750.0, 0.5, _E), 
   'minecraft:polished_blackstone_pressure_plate': (
                                                  200.0, _F, _E), 
   'minecraft:polished_blackstone_button': (
                                          40.0, _F, _E), 
   'minecraft:polished_blackstone_bricks': (
                                          2500.0, 0.4, _E), 
   'minecraft:cracked_polished_blackstone_bricks': (
                                                  2500.0, 0.6, _E), 
   'minecraft:polished_blackstone_brick_stairs': (
                                                2625.0, 0.4, _E), 
   'minecraft:polished_blackstone_brick_slab': (
                                              1750.0, 0.5, _E), 
   'minecraft:polished_blackstone_brick_wall': (
                                              1750.0, 0.4, _E), 
   'minecraft:cobblestone': (
                           2400.0, 0.8, _E), 
   'minecraft:cobblestone_stairs': (
                                  1800.0, 0.8, _E), 
   'minecraft:cobblestone_slab': (
                                1200.0, 0.8, _E), 
   'minecraft:cobblestone_wall': (
                                1200.0, 0.8, _E), 
   'minecraft:mossy_cobblestone': (
                                 2400.0, 0.8, _E), 
   'minecraft:mossy_cobblestone_stairs': (
                                        1800.0, 0.8, _E), 
   'minecraft:mossy_cobblestone_slab': (
                                      1200.0, 0.8, _E), 
   'minecraft:mossy_cobblestone_wall': (
                                      1200.0, 0.8, _E), 
   'minecraft:deepslate': (
                         2900.0, 0.5, _E), 
   'minecraft:cobbled_deepslate': (
                                 2750.0, 0.8, _E), 
   'minecraft:cobbled_deepslate_stairs': (
                                        2060.25, 0.8, _E), 
   'minecraft:cobbled_deepslate_slab': (
                                      1375.0, 0.8, _E), 
   'minecraft:cobbled_deepslate_wall': (
                                      1350.0, 0.8, _E), 
   'minecraft:chiseled_deepslate': (
                                  2750.0, 0.6, _E), 
   'minecraft:polished_deepslate': (
                                  2750.0, 0.35, _E), 
   'minecraft:polished_deepslate_stairs': (
                                         2062.5, 0.35, _E), 
   'minecraft:polished_deepslate_slab': (
                                       1375.0, 0.35, _E), 
   'minecraft:polished_deepslate_wall': (
                                       1350.0, 0.45, _E), 
   'minecraft:deepslate_bricks': (
                                2750.0, 0.5, _E), 
   'minecraft:cracked_deepslate_bricks': (
                                        2750.0, 0.6, _E), 
   'minecraft:deepslate_brick_stairs': (
                                      2062.5, 0.5, _E), 
   'minecraft:deepslate_brick_slab': (
                                    1375.0, 0.5, _E), 
   'minecraft:deepslate_brick_wall': (
                                    1350.0, 0.5, _E), 
   'minecraft:deepslate_tiles': (
                               2750.0, 0.6, _E), 
   'minecraft:cracked_deepslate_tiles': (
                                       2750.0, 0.7, _E), 
   'minecraft:deepslate_tile_stairs': (
                                     2062.5, 0.6, _E), 
   'minecraft:deepslate_tile_slab': (
                                   1375.0, 0.6, _E), 
   'minecraft:deepslate_tile_wall': (
                                   1350.0, 0.6, _E), 
   'minecraft:reinforced_deepslate': (
                                    4000.0, 0.7, _E), 
   'minecraft:diorite': (
                       2500.0, 0.6, _E), 
   'minecraft:diorite_stairs': (
                              1875.0, 0.6, _E), 
   'minecraft:diorite_slab': (
                            1250.0, 0.6, _E), 
   'minecraft:diorite_wall': (
                            1250.0, 0.6, _E), 
   'minecraft:polished_diorite': (
                                2500.0, 0.4, _E), 
   'minecraft:polished_diorite_stairs': (
                                       1875.0, 0.5, _E), 
   'minecraft:polished_diorite_slab': (
                                     1250.0, 0.4, _E), 
   'minecraft:end_stone': (
                         1000.0, 0.6, _E), 
   'minecraft:end_bricks': (
                          1000.0, 0.5, _E), 
   'minecraft:end_brick_stairs': (
                                750.0, 0.5, _E), 
   'minecraft:end_stone_brick_slab': (
                                    500.0, 0.5, _E), 
   'minecraft:end_stone_brick_wall': (
                                    500.0, 0.5, _E), 
   'minecraft:granite': (
                       2500.0, 0.6, _E), 
   'minecraft:granite_stairs': (
                              1875.0, 0.6, _E), 
   'minecraft:granite_slab': (
                            1250.0, 0.6, _E), 
   'minecraft:granite_wall': (
                            1250.0, 0.6, _E), 
   'minecraft:polished_granite': (
                                2500.0, 0.4, _E), 
   'minecraft:polished_granite_stairs': (
                                       1875.0, 0.5, _E), 
   'minecraft:polished_granite_slab': (
                                     1250.0, 0.4, _E), 
   'minecraft:smooth_stone': (
                            2500.0, 0.4, _E), 
   'minecraft:smooth_stone_slab': (
                                 1250.0, 0.4, _E), 
   'minecraft:stone_bricks': (
                            2500.0, 0.5, _E), 
   'minecraft:cracked_stone_bricks': (
                                    2500.0, 0.7, _E), 
   'minecraft:stone_brick_stairs': (
                                  1875.0, 0.5, _E), 
   'minecraft:stone_brick_slab': (
                                1250.0, 0.5, _E), 
   'minecraft:stone_brick_wall': (
                                1250.0, 0.5, _E), 
   'minecraft:chiseled_stone_bricks': (
                                     2500.0, 0.6, _E), 
   'minecraft:mossy_stone_bricks': (
                                  2500.0, 0.3, _E), 
   'minecraft:mossy_stone_brick_stairs': (
                                        1875.0, 0.3, _E), 
   'minecraft:mossy_stone_brick_slab': (
                                      1250.0, 0.3, _E), 
   'minecraft:mossy_stone_brick_wall': (
                                      1250.0, 0.3, _E), 
   'minecraft:brick_block': (
                           2000.0, 0.6, _E), 
   'minecraft:brick_stairs': (
                            1500.0, 0.6, _E), 
   'minecraft:brick_slab': (
                          1000.0, 0.6, _E), 
   'minecraft:brick_wall': (
                          1000.0, 0.6, _E), 
   'minecraft:mud': (
                   1250.0, 0.9, _E), 
   'minecraft:packed_mud': (
                          1500.0, 0.7, _E), 
   'minecraft:mud_bricks': (
                          1500.0, 0.7, _E), 
   'minecraft:mud_brick_stairs': (
                                1120.5, 0.7, _E), 
   'minecraft:mud_brick_slab': (
                              750.0, 0.7, _E), 
   'minecraft:mud_brick_wall': (
                              750.0, 0.7, _E), 
   'minecraft:netherrack': (
                          1000.0, 0.4, _E), 
   'minecraft:nether_brick': (
                            2000.0, 0.5, _E), 
   'minecraft:cracked_nether_bricks': (
                                     2000.0, 0.7, _E), 
   'minecraft:nether_brick_stairs': (
                                   1500.0, 0.6, _E), 
   'minecraft:nether_brick_slab': (
                                 1000.0, 0.6, _E), 
   'minecraft:nether_brick_wall': (
                                 1000.0, 0.6, _E), 
   'minecraft:nether_brick_fence': (
                                  500.0, 0.6, _E), 
   'minecraft:chiseled_nether_bricks': (
                                      2000.0, 0.6, _E), 
   'minecraft:red_nether_brick': (
                                2000.0, 0.5, _E), 
   'minecraft:red_nether_brick_stairs': (
                                       1500.0, 0.6, _E), 
   'minecraft:red_nether_brick_slab': (
                                     1000.0, 0.6, _E), 
   'minecraft:red_nether_brick_wall': (
                                     1000.0, 0.6, _E), 
   'minecraft:sea_lantern': (
                           2500.0, 0.2, _E), 
   'minecraft:prismarine': (
                          2000.0, 0.8, _E), 
   'minecraft:prismarine_stairs': (
                                 1500.0, 0.8, _E), 
   'minecraft:prismarine_slab': (
                               1000.0, 0.8, _E), 
   'minecraft:prismarine_wall': (
                               1000.0, 0.8, _E), 
   'minecraft:prismarine_bricks': (
                                 3000.0, 0.5, _E), 
   'minecraft:prismarine_bricks_stairs': (
                                        2250.0, 0.5, _E), 
   'minecraft:prismarine_brick_slab': (
                                     1500.0, 0.5, _E), 
   'minecraft:dark_prismarine': (
                               3000.0, 0.6, _E), 
   'minecraft:dark_prismarine_stairs': (
                                      2250.0, 0.6, _E), 
   'minecraft:dark_prismarine_slab': (
                                    1500.0, 0.6, _E), 
   'minecraft:purpur_block': (
                            100.0, 0.6, _E), 
   'minecraft:purpur_pillar': (
                             100.0, 0.6, _E), 
   'minecraft:purpur_stairs': (
                             75.0, 0.6, _E), 
   'minecraft:purpur_slab': (
                           50.0, 0.6, _E), 
   'minecraft:quartz_block': (
                            2400.0, 0.6, _E), 
   'minecraft:quartz_stairs': (
                             1800.0, 0.5, _E), 
   'minecraft:quartz_slab': (
                           1200.0, 0.5, _E), 
   'minecraft:chiseled_quartz_block': (
                                     2400.0, 0.6, _E), 
   'minecraft:quartz_bricks': (
                             2400.0, 0.5, _E), 
   'minecraft:quartz_pillar': (
                             2400.0, 0.5, _E), 
   'minecraft:smooth_quartz': (
                             2400.0, 0.3, _E), 
   'minecraft:smooth_quartz_stairs': (
                                    1800.0, 0.3, _E), 
   'minecraft:smooth_quartz_slab': (
                                  1200.0, 0.3, _E), 
   'minecraft:sandstone': (
                         2400.0, 0.6, _E), 
   'minecraft:sandstone_stairs': (
                                1800.0, 0.6, _E), 
   'minecraft:sandstone_slab': (
                              1200.0, 0.6, _E), 
   'minecraft:sandstone_wall': (
                              1200.0, 0.6, _E), 
   'minecraft:chiseled_sandstone': (
                                  2400.0, 0.6, _E), 
   'minecraft:smooth_sandstone': (
                                2400.0, 0.5, _E), 
   'minecraft:smooth_sandstone_stairs': (
                                       1800.0, 0.5, _E), 
   'minecraft:smooth_sandstone_slab': (
                                     1200.0, 0.5, _E), 
   'minecraft:cut_sandstone': (
                             2400.0, 0.6, _E), 
   'minecraft:cut_sandstone_slab': (
                                  1200.0, 0.6, _E), 
   'minecraft:red_sandstone': (
                             2400.0, 0.6, _E), 
   'minecraft:red_sandstone_stairs': (
                                    1800.0, 0.6, _E), 
   'minecraft:red_sandstone_slab': (
                                  1200.0, 0.6, _E), 
   'minecraft:red_sandstone_wall': (
                                  1200.0, 0.6, _E), 
   'minecraft:chiseled_red_sandstone': (
                                      2400.0, 0.6, _E), 
   'minecraft:smooth_red_sandstone': (
                                    2400.0, 0.4, _E), 
   'minecraft:smooth_red_sandstone_stairs': (
                                           1800.0, 0.5, _E), 
   'minecraft:smooth_red_sandstone_slab': (
                                         1200.0, 0.5, _E), 
   'minecraft:cut_red_sandstone': (
                                 2400.0, 0.6, _E), 
   'minecraft:cut_red_sandstone_slab': (
                                      1200.0, 0.6, _E), 
   'minecraft:crafting_table': (
                              800.0, 0.6, _E), 
   'minecraft:stonecutter_block': (
                                 2000.0, 0.5, _E), 
   'minecraft:stonecutter': (
                           2000.0, 0.5, _E), 
   'minecraft:cartography_table': (
                                 800.0, 0.5, _E), 
   'minecraft:fletching_table': (
                               900.0, 0.6, _E), 
   'minecraft:smithing_table': (
                              1800.0, 0.6, _E), 
   'minecraft:grindstone': (
                          1500.0, 0.2, _E), 
   'minecraft:loom': (
                    400.0, _F, _E), 
   'minecraft:furnace': (
                       2800.0, 0.5, _E), 
   'minecraft:lit_furnace': (
                           2800.0, 0.5, _E), 
   'minecraft:smoker': (
                      2800.0, 0.5, _E), 
   'minecraft:lit_smoker': (
                          2800.0, 0.5, _E), 
   'minecraft:blast_furnace': (
                             3000.0, 0.5, _E), 
   'minecraft:lit_blast_furnace': (
                                 3000.0, 0.5, _E), 
   'minecraft:campfire': (
                        600.0, _F, _E), 
   'minecraft:soul_campfire': (
                             600.0, _F, _E), 
   'minecraft:anvil': (
                     7000.0, 0.2, _E), 
   'minecraft:chipped_anvil': (
                             7000.0, 0.2, _E), 
   'minecraft:damaged_anvil': (
                             7000.0, 0.2, _E), 
   'minecraft:enchanting_table': (
                                1600.0, _F, _E), 
   'minecraft:brewing_stand': (
                             800.0, _F, _E), 
   'minecraft:torch': (
                     5.0, _F, _E), 
   'minecraft:soul_torch': (
                          5.0, _F, _E), 
   'minecraft:lantern': (
                       25.0, _F, _E), 
   'minecraft:soul_lantern': (
                            25.0, _F, _E), 
   'minecraft:end_rod': (
                       100.0, 0.1, _E), 
   'minecraft:glowstone': (
                         1000.0, 0.7, _E), 
   'minecraft:shroomlight': (
                           800.0, _F, _E), 
   'minecraft:ochre_froglight': (800.0, 0.07, 0.8), 
   'minecraft:verdant_froglight': (800.0, 0.07, 0.8), 
   'minecraft:pearlescent_froglight': (800.0, 0.07, 0.8), 
   'minecraft:crying_obsidian': (
                               5000.0, 0.8, _E), 
   'minecraft:glow_lichen': (
                           1.0, _F, _E), 
   'minecraft:magma': (
                     3000.0, 0.4, _E), 
   'minecraft:flower_pot': (
                          50.0, _F, _E), 
   'minecraft:decorated_pot': (
                             250.0, 0.35, _E), 
   'minecraft:bookshelf': (
                         800.0, 0.5, _E), 
   'minecraft:chiseled_bookshelf': (
                                  800.0, 0.5, _E), 
   'minecraft:skeleton_skull': (
                              25.0, 0.2, _E), 
   'minecraft:wither_skeleton_skull': (
                                     25.0, 0.2, _E), 
   'minecraft:zombie_head': (
                           50.0, _F, _E), 
   'minecraft:player_head': (
                           50.0, _F, _E), 
   'minecraft:creeper_head': (
                            50.0, _F, _E), 
   'minecraft:dragon_head': (
                           75.0, _F, _E), 
   'minecraft:piglin_head': (
                           50.0, _F, _E), 
   'minecraft:dragon_egg': (
                          5000.0, 0.8, _E), 
   'minecraft:carved_pumpkin': (
                              100.0, 0.3, _E), 
   'minecraft:lit_pumpkin': (
                           105.0, 0.3, _E), 
   'minecraft:hay_block': (200.0, 0.6, 0.3), 
   'minecraft:beacon': (
                      4000.0, 0.2, _E), 
   'minecraft:conduit': (
                       750.0, _F, _E), 
   'minecraft:lodestone': (
                         4450.0, 0.5, _E), 
   'minecraft:ladder': (
                      50.0, _F, _E), 
   'minecraft:scaffolding': (
                           50.0, _F, _E), 
   'minecraft:bee_nest': (
                        400.0, 0.5, _E), 
   'minecraft:beehive': (
                       400.0, 0.4, _E), 
   'minecraft:suspicious_sand': (
                               1600.0, 0.4, _E), 
   'minecraft:suspicious_gravel': (
                                 1600.0, 0.7, _E), 
   'minecraft:ender_chest': (
                           1000.0, 0.4, _E), 
   'minecraft:respawn_anchor': (
                              2000.0, 0.7, _E), 
   'minecraft:infested_stone': (
                              2750.0, 0.6, _E), 
   'minecraft:infested_cobblestone': (
                                    2750.0, 0.8, _E), 
   'minecraft:infested_stone_bricks': (
                                     2750.0, 0.5, _E), 
   'minecraft:infested_mossy_stone_bricks': (
                                           2750.0, 0.3, _E), 
   'minecraft:infested_cracked_stone_bricks': (
                                             2750.0, 0.6, _E), 
   'minecraft:infested_chiseled_stone_bricks': (
                                              2750.0, 0.6, _E), 
   'minecraft:infested_deepslate': (
                                  3050.0, 0.5, _E), 
   'minecraft:end_portal_frame': (
                                3000.0, 0.4, _E), 
   'minecraft:cake': (
                    50.0, 0.1, _E), 
   'minecraft:sponge': (150.0, 0.6, 0.2), 
   'minecraft:wet_sponge': (1150.0, 0.3, 0.6), 
   'minecraft:web': (
                   0.1, 1.0, _E), 
   'minecraft:grass_block': (
                           1250.0, 0.5, _E), 
   'minecraft:podzol': (
                      1250.0, 0.6, _E), 
   'minecraft:mycelium': (
                        1250.0, 0.5, _E), 
   'minecraft:grass_path': (
                          1150.0, 0.5, _E), 
   'minecraft:dirt': (
                    1250.0, 0.6, _E), 
   'minecraft:coarse_dirt': (
                           1500.0, 0.7, _E), 
   'minecraft:dirt_with_roots': (
                               1200.0, 0.7, _E), 
   'minecraft:farmland': (
                        1250.0, 0.6, _E), 
   'minecraft:coal_ore': (
                        2450.0, 0.6, _E), 
   'minecraft:deepslate_coal_ore': (
                                  2715.0, 0.5, _E), 
   'minecraft:iron_ore': (
                        3150.0, 0.6, _E), 
   'minecraft:deepslate_iron_ore': (
                                  3450.0, 0.5, _E), 
   'minecraft:copper_ore': (
                          3250.0, 0.6, _E), 
   'minecraft:deepslate_copper_ore': (
                                    3550.0, 0.5, _E), 
   'minecraft:gold_ore': (
                        4450.0, 0.6, _E), 
   'minecraft:deepslate_gold_ore': (
                                  4700.0, 0.5, _E), 
   'minecraft:redstone_ore': (
                            1950.0, 0.6, _E), 
   'minecraft:lit_redstone_ore': (
                                1950.0, 0.6, _E), 
   'minecraft:deepslate_redstone_ore': (
                                      2225.0, 0.5, _E), 
   'minecraft:lit_deepslate_redstone_ore': (
                                          2225.0, 0.5, _E), 
   'minecraft:emerald_ore': (
                           2600.0, 0.6, _E), 
   'minecraft:deepslate_emerald_ore': (
                                     2855.0, 0.5, _E), 
   'minecraft:lapis_ore': (
                         2700.0, 0.6, _E), 
   'minecraft:deepslate_lapis_ore': (
                                   2950.0, 0.5, _E), 
   'minecraft:diamond_ore': (
                           2700.0, 0.6, _E), 
   'minecraft:deepslate_diamond_ore': (
                                     2950.0, 0.5, _E), 
   'minecraft:nether_gold_ore': (
                               2250.0, 0.4, _E), 
   'minecraft:quartz_ore': (
                          1500.0, 0.4, _E), 
   'minecraft:ancient_debris': (
                              3150.0, 0.8, _E), 
   'minecraft:raw_iron_block': (
                              7850.0, 0.8, _E), 
   'minecraft:raw_copper_block': (
                                9000.0, 0.8, _E), 
   'minecraft:raw_gold_block': (
                              19300.0, 0.8, _E), 
   'minecraft:short_grass': (
                           20.0, _F, _E), 
   'minecraft:tall_grass': (
                          20.0, _F, _E), 
   'minecraft:fern': (
                    20.0, _F, _E), 
   'minecraft:large_fern': (
                          20.0, _F, _E), 
   'minecraft:waterlily': (
                         20.0, _F, _E), 
   'minecraft:vine': (
                    20.0, _F, _E), 
   'minecraft:cocoa': (
                     50.0, _F, _E), 
   'minecraft:wheat': (
                     20.0, _F, _E), 
   'minecraft:beetroot': (
                        20.0, _F, _E), 
   'minecraft:carrots': (
                       20.0, _F, _E), 
   'minecraft:potatoes': (
                        20.0, _F, _E), 
   'minecraft:sweet_berry_bush': (
                                50.0, _F, _E), 
   'minecraft:reeds': (
                     100.0, _F, _E), 
   'minecraft:bamboo_sapling': (
                              20.0, _F, _E), 
   'minecraft:bamboo': (
                      50.0, _F, _E), 
   'minecraft:kelp': (
                    20.0, _F, _E), 
   'minecraft:seagrass': (
                        50.0, _F, _E), 
   'minecraft:sea_pickle': (
                          20.0, _F, 0.1), 
   'minecraft:deadbush': (
                        100.0, _F, _E), 
   'minecraft:cactus': (
                      600.0, _F, _E), 
   'minecraft:melon_stem': (
                          20.0, _F, _E), 
   'minecraft:melon_block': (
                           1000.0, 0.2, _E), 
   'minecraft:pumpkin_stem': (
                            20.0, _F, _E), 
   'minecraft:pumpkin': (
                       800.0, 0.3, _E), 
   'minecraft:warped_fungus': (
                             20.0, _F, _E), 
   'minecraft:nether_sprouts': (
                              10.0, _F, _E), 
   'minecraft:warped_roots': (
                            20.0, _F, _E), 
   'minecraft:twisting_vines': (
                              50.0, _F, _E), 
   'minecraft:crimson_fungus': (
                              20.0, _F, _E), 
   'minecraft:nether_wart': (
                           20.0, _F, _E), 
   'minecraft:crimson_roots': (
                             20.0, _F, _E), 
   'minecraft:weeping_vines': (
                             20.0, _F, _E), 
   'minecraft:nether_wart_block': (
                                 600.0, _F, 0.1), 
   'minecraft:warped_wart_block': (
                                 600.0, _F, 0.1), 
   'minecraft:chorus_plant': (
                            300.0, 0.6, _E), 
   'minecraft:chorus_flower': (
                             500.0, 0.4, _E), 
   'minecraft:brown_mushroom_block': (400.0, 0.2, 0.1), 
   'minecraft:red_mushroom_block': (400.0, 0.2, 0.1), 
   'minecraft:brown_mushroom': (
                              10.0, _F, _E), 
   'minecraft:red_mushroom': (
                            10.0, _F, _E), 
   'minecraft:azalea': (
                      120.0, _F, 0.1), 
   'minecraft:flowering_azalea': (
                                120.0, _F, 0.1), 
   'minecraft:big_dripleaf': (8.0, 0.3, 0.3), 
   'minecraft:small_dripleaf_block': (
                                    3.0, _F, _E), 
   'minecraft:cave_vines': (
                          20.0, _F, _E), 
   'minecraft:cave_vines_body_with_berries': (
                                            20.0, _F, _E), 
   'minecraft:cave_vines_head_with_berries': (
                                            20.0, _F, _E), 
   'minecraft:spore_blossom': (
                             12.0, _F, _E), 
   'minecraft:moss_block': (250.0, 0.5, 0.05), 
   'minecraft:moss_carpet': (
                           15.0, 0.5, _E), 
   'minecraft:hanging_roots': (
                             4.0, _F, _E), 
   'minecraft:pink_petals': (
                           1.0, _F, _E), 
   'minecraft:torchflower_crop': (
                                20.0, _F, _E), 
   'minecraft:pitcher_crop': (
                            20.0, _F, _E), 
   'minecraft:clay': (
                    1500.0, 0.4, _E), 
   'minecraft:sand': (
                    1500.0, 0.4, _E), 
   'minecraft:red_sand': (
                        1500.0, 0.4, _E), 
   'minecraft:gravel': (
                      1500.0, 0.7, _E), 
   'minecraft:tuff': (
                    1800.0, 0.7, _E), 
   'minecraft:calcite': (
                       2700.0, 0.5, _E), 
   'minecraft:obsidian': (
                        5000.0, 0.8, _E), 
   'minecraft:dripstone_block': (
                               2700.0, 0.5, _E), 
   'minecraft:pointed_dripstone': (
                                 1900.0, 0.5, _E), 
   'minecraft:budding_amethyst': (
                                2650.0, 1.0, _E), 
   'minecraft:ice': (
                   800.0, 0.05, _E), 
   'minecraft:packed_ice': (
                          900.0, 0.02, _E), 
   'minecraft:blue_ice': (
                        1000.0, 0.0, _E), 
   'minecraft:snow_layer': (
                          25.0, 0.2, _E), 
   'minecraft:snow': (
                    250.0, 0.2, _E), 
   'minecraft:crimson_nylium': (
                              1180.0, 0.5, _E), 
   'minecraft:warped_nylium': (
                             1180.0, 0.5, _E), 
   'minecraft:soul_sand': (
                         1000.0, 0.9, _E), 
   'minecraft:soul_soil': (
                         1000.0, 0.8, _E), 
   'minecraft:bone_block': (
                          2000.0, 0.2, _E), 
   'minecraft:small_amethyst_bud': (
                                  100.0, 0.7, _E), 
   'minecraft:medium_amethyst_bud': (
                                   300.0, 0.8, _E), 
   'minecraft:large_amethyst_bud': (
                                  600.0, 0.9, _E), 
   'minecraft:amethyst_cluster': (
                                900.0, 0.9, _E), 
   'minecraft:frog_spawn': (
                          10.0, 0.03, _E), 
   'minecraft:sculk_catalyst': (
                              500.0, 0.2, _E), 
   'minecraft:sculk_vein': (50.0, 0.2, 0.03), 
   'minecraft:sculk': (250.0, 0.2, 0.3), 
   'minecraft:sniffer_egg': (
                           950.0, 0.1, _E), 
   'minecraft:dried_kelp_block': (400.0, 0.6, 0.3), 
   'minecraft:honeycomb_block': (
                               900.0, 0.8, _E), 
   'minecraft:turtle_egg': (
                          10.0, _F, _E), 
   'minecraft:mangrove_roots': (
                              500.0, 0.8, _E), 
   'minecraft:muddy_mangrove_roots': (
                                    1500.0, 0.8, _E), 
   'minecraft:mushroom_stem': (600.0, 0.2, 0.1), 
   'minecraft:target': (
                      200.0, _F, 0.3), 
   'minecraft:calibrated_sculk_sensor': (250.0, 0.9, 0.3), 
   'minecraft:sculk_shrieker': (500.0, 0.2, 0.3), 
   'minecraft:lectern': (
                       150.0, _F, _E), 
   'minecraft:daylight_detector': (
                                 1250.0, 0.2, _E), 
   'minecraft:daylight_detector_inverted': (
                                          1250.0, 0.2, _E), 
   'minecraft:lightning_rod': (
                             1800.0, 0.2, _E), 
   'minecraft:piston': (
                      2500.0, 0.5, _E), 
   'minecraft:sticky_piston': (
                             2500.0, 0.5, _E), 
   'minecraft:slime': (500.0, 1.0, 1.0), 
   'minecraft:honey_block': (
                           500.0, 1.0, _E), 
   'minecraft:dispenser': (
                         2500.0, 0.5, _E), 
   'minecraft:dropper': (
                       2500.0, 0.5, _E), 
   'minecraft:hopper': (
                      1000.0, 0.3, _E), 
   'minecraft:chest': (
                     1000.0, 0.4, _E), 
   'minecraft:barrel': (
                      400.0, 0.4, _E), 
   'minecraft:trapped_chest': (
                             1050.0, _F, _E), 
   'minecraft:jukebox': (
                       800.0, 0.6, _E), 
   'minecraft:observer': (
                        2500.0, 0.5, _E), 
   'minecraft:noteblock': (
                         1000.0, 0.6, _E), 
   'minecraft:composter': (
                         350.0, 0.5, _E), 
   'minecraft:cauldron': (
                        5400.0, 0.2, _E), 
   'minecraft:rail': (
                    350.0, 0.7, _E), 
   'minecraft:golden_rail': (
                           800.0, 0.7, _E), 
   'minecraft:detector_rail': (
                             400.0, 0.7, _E), 
   'minecraft:activator_rail': (
                              350.0, 0.7, _E), 
   'minecraft:tnt': (
                   1250.0, _F, _E), 
   'minecraft:redstone_lamp': (
                             1250.0, 0.2, _E), 
   'minecraft:lit_redstone_lamp': (
                                 1250.0, 0.2, _E), 
   'minecraft:bell': (
                    500.0, 0.2, _E), 
   'minecraft:redstone_wire': (
                             5.0, _F, _E), 
   'minecraft:redstone_torch': (
                              5.0, _F, _E), 
   'minecraft:unlit_redstone_torch': (
                                    5.0, _F, _E), 
   'minecraft:unpowered_repeater': (
                                  200.0, 0.3, _E), 
   'minecraft:powered_repeater': (
                                200.0, 0.3, _E), 
   'minecraft:unpowered_comparator': (
                                    200.0, 0.3, _E), 
   'minecraft:powered_comparator': (
                                  200.0, 0.3, _E), 
   'minecraft:lever': (
                     10.0, _F, _E), 
   'minecraft:tripwire_hook': (
                             5.0, _F, _E), 
   'minecraft:trip_wire': (
                         1.0, _F, _E), 
   'minecraft:tinted_glass': (
                            2200.0, 0.2, _E), 
   'minecraft:glass': (
                     2000.0, 0.2, _E), 
   'minecraft:glass_pane': (
                          250.0, 0.2, _E)}
for _i in range(16):
    _BLOCK_MASS_TABLE[('minecraft:light_block_{}').format(_i)] = (
     0.1, _F, _E)

# _COPPER_CUT_STAGES = [
#
#  727, 728, 729, 730,
#  731, 732,
#  733, 734]
# for _prefix, _fric in _COPPER_CUT_STAGES:
#     _BLOCK_MASS_TABLE[('minecraft:{}cut_copper').format(_prefix)] = (2250.0, _fric, _E)
#     _BLOCK_MASS_TABLE[('minecraft:{}cut_copper_stairs').format(_prefix)] = (1687.5, _fric, _E)
#     _BLOCK_MASS_TABLE[('minecraft:{}cut_copper_slab').format(_prefix)] = (1125.0, _fric, _E)

for _c in _COLORS:
    _BLOCK_MASS_TABLE[('minecraft:{}_wool').format(_c)] = (500.0, 0.6, 0.5)
    _BLOCK_MASS_TABLE[('minecraft:{}_carpet').format(_c)] = (20.0, 0.6, 0.05)
    _BLOCK_MASS_TABLE[('minecraft:{}_terracotta').format(_c)] = (
     2000.0, 0.6, _E)
    _BLOCK_MASS_TABLE[('minecraft:{}_concrete').format(_c)] = (
     2400.0, 0.4, _E)
    _BLOCK_MASS_TABLE[('minecraft:{}_concrete_powder').format(_c)] = (
     2200.0, 0.6, _E)
    _BLOCK_MASS_TABLE[('minecraft:{}_stained_glass').format(_c)] = (
     2000.0, 0.2, _E)
    _BLOCK_MASS_TABLE[('minecraft:{}_stained_glass_pane').format(_c)] = (
     250.0, 0.2, _E)
    _BLOCK_MASS_TABLE[('minecraft:{}_candle').format(_c)] = (
     2.0, 0.1, _E)
    _BLOCK_MASS_TABLE[('minecraft:{}_candle_cake').format(_c)] = (
     60.0, 0.1, _E)
    _BLOCK_MASS_TABLE[('minecraft:{}_shulker_box').format(_c)] = (
     500.0, 0.1, _E)

_BLOCK_MASS_TABLE['minecraft:candle'] = (
 2.0, 0.1, _E)
_BLOCK_MASS_TABLE['minecraft:candle_cake'] = (60.0, 0.1, _E)
_BLOCK_MASS_TABLE['minecraft:hardened_clay'] = (
 2000.0, 0.6, _E)
_BLOCK_MASS_TABLE['minecraft:undyed_shulker_box'] = (
 500.0, 0.1, _E)
_GLAZED_COLORS = [
 4, 5, 6, 7, 8, 9, 
 10, 11, 590, 13, 14, 15, 
 16, 17, 18, 19]
for _c in _GLAZED_COLORS:
    _BLOCK_MASS_TABLE[('minecraft:{}_glazed_terracotta').format(_c)] = (2000.0, 0.2, _E)

_BLOCK_MASS_TABLE['minecraft:bed'] = (250.0, 0.6, 0.5)
_BLOCK_MASS_TABLE['minecraft:standing_banner'] = (
 30.0, _F, _E)
_BLOCK_MASS_TABLE['minecraft:wall_banner'] = (30.0, _F, _E)
for _w in _OVERWORLD_WOODS:
    _BLOCK_MASS_TABLE[('minecraft:{}_log').format(_w)] = (
     800.0, 0.6, _E)
    _BLOCK_MASS_TABLE[('minecraft:{}_wood').format(_w)] = (800.0, 0.6, _E)
    _BLOCK_MASS_TABLE[('minecraft:stripped_{}_log').format(_w)] = (800.0, 0.4, _E)
    _BLOCK_MASS_TABLE[('minecraft:stripped_{}_wood').format(_w)] = (800.0, 0.4, _E)
    _BLOCK_MASS_TABLE[('minecraft:{}_planks').format(_w)] = (500.0, 0.5, _E)
    _BLOCK_MASS_TABLE[('minecraft:{}_stairs').format(_w)] = (375.0, 0.5, _E)
    _BLOCK_MASS_TABLE[('minecraft:{}_slab').format(_w)] = (250.0, 0.5, _E)

for _w in _NETHER_WOODS:
    _BLOCK_MASS_TABLE[('minecraft:{}_stem').format(_w)] = (800.0, 0.6, _E)
    _BLOCK_MASS_TABLE[('minecraft:{}_hyphae').format(_w)] = (800.0, 0.6, _E)
    _BLOCK_MASS_TABLE[('minecraft:stripped_{}_stem').format(_w)] = (800.0, 0.4, _E)
    _BLOCK_MASS_TABLE[('minecraft:stripped_{}_hyphae').format(_w)] = (800.0, 0.4, _E)
    _BLOCK_MASS_TABLE[('minecraft:{}_planks').format(_w)] = (500.0, 0.5, _E)
    _BLOCK_MASS_TABLE[('minecraft:{}_stairs').format(_w)] = (375.0, 0.5, _E)
    _BLOCK_MASS_TABLE[('minecraft:{}_slab').format(_w)] = (250.0, 0.5, _E)

_BLOCK_MASS_TABLE['minecraft:bamboo_block'] = (
 800.0, 0.6, _E)
_BLOCK_MASS_TABLE['minecraft:stripped_bamboo_block'] = (800.0, 0.4, _E)
_BLOCK_MASS_TABLE['minecraft:bamboo_planks'] = (400.0, 0.5, _E)
_BLOCK_MASS_TABLE['minecraft:bamboo_stairs'] = (300.0, 0.5, _E)
_BLOCK_MASS_TABLE['minecraft:bamboo_slab'] = (200.0, 0.5, _E)
_BLOCK_MASS_TABLE['minecraft:bamboo_mosaic'] = (400.0, 0.5, _E)
_BLOCK_MASS_TABLE['minecraft:bamboo_mosaic_stairs'] = (300.0, 0.5, _E)
_BLOCK_MASS_TABLE['minecraft:bamboo_mosaic_slab'] = (200.0, 0.5, _E)
_BLOCK_MASS_TABLE['minecraft:wooden_door'] = (
 100.0, _F, _E)
for _w in _ALL_WOOD_NAMES:
    if _w != 'oak':
        _BLOCK_MASS_TABLE[('minecraft:{}_door').format(_w)] = (
         100.0, _F, _E)

_BLOCK_MASS_TABLE['minecraft:copper_door'] = (
 750.0, 0.35, _E)
_BLOCK_MASS_TABLE['minecraft:trapdoor'] = (
 100.0, _F, _E)
for _w in _ALL_WOOD_NAMES:
    if _w != 'oak':
        _BLOCK_MASS_TABLE[('minecraft:{}_trapdoor').format(_w)] = (
         100.0, _F, _E)

_BLOCK_MASS_TABLE['minecraft:copper_trapdoor'] = (
 1000.0, 0.35, _E)
# for _prefix, _fric in _COPPER_CUT_STAGES:
#     if _prefix:
#         _BLOCK_MASS_TABLE[('minecraft:{}copper_trapdoor').format(_prefix)] = (
#          1000.0, 0.35, _E)
#         _BLOCK_MASS_TABLE[('minecraft:{}copper_door').format(_prefix)] = (750.0, 0.35, _E)

_BLOCK_MASS_TABLE['minecraft:fence_gate'] = (100.0, _F, _E)
for _w in _ALL_WOOD_NAMES:
    if _w != 'oak':
        _BLOCK_MASS_TABLE[('minecraft:{}_fence_gate').format(_w)] = (
         100.0, _F, _E)

for _w in _ALL_WOOD_NAMES:
    _BLOCK_MASS_TABLE[('minecraft:{}_fence').format(_w)] = (
     100.0, _F, _E)

_BLOCK_MASS_TABLE['minecraft:wooden_pressure_plate'] = (
 50.0, _F, _E)
for _w in _ALL_WOOD_NAMES:
    if _w != 'oak':
        _BLOCK_MASS_TABLE[('minecraft:{}_pressure_plate').format(_w)] = (
         50.0, _F, _E)

_BLOCK_MASS_TABLE['minecraft:wooden_button'] = (2.5, _F, _E)
for _w in _ALL_WOOD_NAMES:
    if _w != 'oak':
        _BLOCK_MASS_TABLE[('minecraft:{}_button').format(_w)] = (
         2.5, _F, _E)

_STANDING_SIGNS = [
 631, 
 632, 633, 634, 
 635, 636, 
 637, 638, 
 639, 640, 
 641, 
 642]
for _s in _STANDING_SIGNS:
    _BLOCK_MASS_TABLE[('minecraft:{}').format(_s)] = (50.0, _F, _E)

_WALL_SIGNS = [
 644, 
 645, 646, 647, 
 648, 649, 
 650, 651, 
 652, 653, 
 654, 
 655]
for _s in _WALL_SIGNS:
    _BLOCK_MASS_TABLE[('minecraft:{}').format(_s)] = (50.0, _F, _E)

for _w in _ALL_WOOD_NAMES:
    _BLOCK_MASS_TABLE[('minecraft:{}_hanging_sign').format(_w)] = (100.0, 0.5, _E)

_LEAF_TYPES = [
 657, 658, 659, 660, 
 661, 662, 663, 664, 
 665, 666, 667]
for _leaf in _LEAF_TYPES:
    _BLOCK_MASS_TABLE[('minecraft:{}').format(_leaf)] = (200.0, _F, 0.15)

_SAPLING_TYPES = [
 668, 669, 670, 671, 
 672, 673, 674, 
 675, 676]
for _sap in _SAPLING_TYPES:
    _BLOCK_MASS_TABLE[('minecraft:{}').format(_sap)] = (150.0, _F, _E)

_SMALL_FLOWERS = [
 677, 678, 679, 680, 681, 
 682, 683, 684, 685, 
 686, 687, 688, 
 689, 
 690]
for _f in _SMALL_FLOWERS:
    _BLOCK_MASS_TABLE[('minecraft:{}').format(_f)] = (10.0, _F, _E)

_TALL_FLOWERS = [
 691, 692, 693, 694, 695]
for _f in _TALL_FLOWERS:
    _BLOCK_MASS_TABLE[('minecraft:{}').format(_f)] = (
     20.0, _F, _E)

_CORAL_TYPES = [
 696, 697, 698, 699, 700]
for _ct in _CORAL_TYPES:
    _BLOCK_MASS_TABLE[('minecraft:{}_coral_block').format(_ct)] = (
     150.0, 0.7, _E)
    _BLOCK_MASS_TABLE[('minecraft:{}_coral').format(_ct)] = (50.0, 0.7, _E)

_BLOCK_MASS_TABLE['valkyrien_be:valkyrien_be_balloon'] = (50.0, 0.3, 0.5)
_custom_mass_overrides = {}

def set_custom_mass(block_name, mass_kg):
    """
    设置方块的自定义质量覆盖值。
    @param block_name: str 方块名（如 "minecraft:stone"）
    @param mass_kg: float 自定义质量(kg)
    """
    _custom_mass_overrides[block_name] = float(mass_kg)
    return


def remove_custom_mass(block_name):
    """移除方块的自定义质量覆盖，恢复为默认值"""
    _custom_mass_overrides.pop(block_name, None)
    return


def get_custom_mass_overrides():
    """返回当前所有自定义质量覆盖（用于序列化保存）"""
    return dict(_custom_mass_overrides)


def load_custom_mass_overrides(data_dict):
    """
    从存档数据批量加载自定义质量覆盖。
    @param data_dict: dict {block_name: mass_kg}
    """
    _custom_mass_overrides.clear()
    if data_dict and isinstance(data_dict, dict):
        for k, v in data_dict.items():
            _custom_mass_overrides[str(k)] = float(v)

    return


def get_block_mass_info(block_name):
    """
    查询方块的质量物理参数。
    优先返回自定义覆盖值，未命中则查默认表。

    Args:
        block_name: str, 方块名（如 "minecraft:stone"）

    Returns:
        tuple (mass, friction, elasticity):
            - mass: float, 质量(kg)
            - friction: float, 摩擦系数（用于静摩擦和动摩擦）
            - elasticity: float, 弹性系数（用作 restitution）
    """
    custom_mass = _custom_mass_overrides.get(block_name)
    if custom_mass is not None:
        entry = _BLOCK_MASS_TABLE.get(block_name)
        if entry:
            return (custom_mass, entry[1], entry[2])
        return (custom_mass, DEFAULT_BLOCK_FRICTION, DEFAULT_BLOCK_ELASTICITY)
    else:
        entry = _BLOCK_MASS_TABLE.get(block_name)
        if entry:
            return entry
        if '_double_slab' in block_name:
            slab_name = block_name.replace('_double_slab', '_slab')
            entry = _BLOCK_MASS_TABLE.get(slab_name)
            if entry:
                return (entry[0] * 2.0, entry[1], entry[2])
        return (
         DEFAULT_BLOCK_MASS, DEFAULT_BLOCK_FRICTION, DEFAULT_BLOCK_ELASTICITY)

