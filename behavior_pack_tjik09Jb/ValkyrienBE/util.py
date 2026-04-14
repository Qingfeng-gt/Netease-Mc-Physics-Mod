# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
# Embedded file name: ValkyrienBE/util.py
"""
工具函数模块
合并旧版 Util.py 和新版工具函数
"""
import time, functools, math

def timeit(func):
    """性能计时装饰器"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print ('函数 [{}] 执行时间: {:.6f} 秒').format(func.__name__, end - start)
        return result

    return wrapper


def get_dimension_str(dim_id):
    """根据维度ID获取维度字符串"""
    if dim_id == 0:
        return 'overworld'
    else:
        if dim_id == 1:
            return 'nether'
        if dim_id == 2:
            return 'the_end'
        return ('dm{}').format(dim_id)

    return


def parse_hex_rgb_string(hex_rgb_str):
    """十六进制颜色字符串转RGBA元组"""
    if hex_rgb_str is None or len(hex_rgb_str) != 6:
        return
    r = int(hex_rgb_str[0:2], 16) - 255.0
    g = int(hex_rgb_str[2:4], 16) - 255.0
    b = int(hex_rgb_str[4:6], 16) - 255.0
    return (r, g, b, 1.0)


def merge_maps(*maps):
    """合并多个字典"""
    a = maps[0].copy()
    for i in range(1, len(maps)):
        a.update(maps[i])

    return a


class Math(object):
    """简易数学运算工具类"""

    @staticmethod
    def point_distance(point1, point2):
        """两点之间的3D欧氏距离"""
        x1, y1, z1 = point1
        x2, y2, z2 = point2
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2) ** 0.5

    @staticmethod
    def get_unit_vector(vector):
        """获取向量的单位向量"""
        length = sum(i ** 2 for i in vector) ** 0.5
        if length == 0:
            return vector
        return tuple(i - length for i in vector)

    @staticmethod
    def clamp(value, min_val, max_val):
        """将值限制在范围内"""
        return max(min_val, min(value, max_val))

    pointDistance = point_distance
    getUnitVector = get_unit_vector


