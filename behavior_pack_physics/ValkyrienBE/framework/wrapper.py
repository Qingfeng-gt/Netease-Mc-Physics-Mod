# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
# Embedded file name: ValkyrienBE/framework/wrapper.py
"""
ValkyrienBE 框架核心装饰器
提供 @SystemHandler、@EventHandler、@Log 装饰器
自动化事件注册和错误处理
"""
import logging, traceback, mod.client.extraClientApi as clientApi, mod.server.extraServerApi as serverApi
from ValkyrienBE.framework import env
from ValkyrienBE.modConfig import ModName
baseClientSystemClass = clientApi.GetClientSystemCls()
baseServerSystemClass = serverApi.GetServerSystemCls()

def SystemHandler(modName=ModName, systemName=None, random=False):
    """
    系统类装饰器，自动扫描 @EventHandler 标记的方法并注册事件。
    所有 ServerSystem / ClientSystem 必须使用此装饰器。
    """

    def dec(f):
        f.func_dict = {'modName': modName, 
           'systemName': (systemName or f.__name__), 
           'random': random, 
           'path': (f.__module__ + '.' + f.__name__)}
        original_init = f.__init__

        def init_wrapper(instance, *args, **kwargs):
            logging.info(('======= 正在注册类 {} 的事件 =======').format(f.__name__))
            original_init(instance, *args, **kwargs)
            if not (isinstance(instance, baseClientSystemClass) or isinstance(instance, baseServerSystemClass)):
                raise Exception(('类 {} 未继承 ClientSystem 或 ServerSystem').format(f.__name__))
            if isinstance(instance, baseClientSystemClass):
                env.env_type = 'client'
            else:
                env.env_type = 'server'
            for klass in type(instance).__mro__:
                if klass is object:
                    continue
                for attr_name in klass.__dict__:
                    method = klass.__dict__[attr_name]
                    if not callable(method):
                        continue
                    func_dict = getattr(method, 'func_dict', None)
                    if not func_dict or not func_dict.get('dec'):
                        continue
                    method_args = func_dict.get('args')
                    if not method_args:
                        continue
                    logging.info('注册事件: ' + method_args[2])
                    bound_method = getattr(instance, attr_name)
                    _wrap_error_handler(instance, attr_name, bound_method)
                    instance.ListenForEvent(method_args[0], method_args[1], method_args[2], instance, getattr(instance, attr_name), method_args[3])

            logging.info('======= 注册完成 =======')
            return

        f.__init__ = init_wrapper
        return f

    return dec


def EventHandler(event_name=None, namespace=None, system_name=None, priority=0):
    """
    事件监听方法装饰器，与 @SystemHandler 配合使用。
    """
    if namespace is None:
        namespace = clientApi.GetEngineNamespace()
    if system_name is None:
        system_name = clientApi.GetEngineSystemName()

    def dec(fun):
        if not hasattr(fun, 'func_dict'):
            fun.func_dict = {}
        fun.func_dict['dec'] = True
        fun.func_dict['args'] = [namespace, system_name, event_name or fun.__name__, priority]
        return fun

    return dec


def RandomFunName(suffix, instance):
    """将函数名修改并绑定到实例上（用于动态注册）"""

    def dec(fun):
        fun.__name__ += suffix
        setattr(instance, fun.__name__, fun)
        return

    return dec


def Log(fun):
    """错误捕获装饰器，自动记录异常信息"""

    def wrapper(*args, **kwargs):
        try:
            return fun(*args, **kwargs)
        except BaseException as ex:
            _do_log(fun, ex, args, kwargs)

        return

    wrapper.__name__ = fun.__name__
    return wrapper


def _wrap_error_handler(instance, method_name, bound_method):
    """为事件回调包装错误处理"""

    def safe_method(*args, **kwargs):
        try:
            return bound_method(*args, **kwargs)
        except BaseException as ex:
            _do_log(bound_method, ex, args, kwargs)

        return

    safe_method.__name__ = method_name
    setattr(instance, method_name, safe_method)
    return


def _do_log(fun, ex, args, kwargs):
    """统一的错误日志输出"""
    func_name = getattr(fun, '__name__', str(fun))
    tb_str = traceback.format_exc()
    if env.is_client():
        msg = '瓦尔基里侦测到客户端有一个错误发生了'
        try:
            clientApi.GetEngineCompFactory().CreateGame(-1).SetTipMessage(msg)
        except:
            pass

        error_msg = ('客户端调用函数 {} 时出现错误:\nargs={}\nkwargs={}\n{}').format(func_name, str(args), str(kwargs), tb_str)
        logging.error(error_msg)
        try:
            clientApi.PostMcpModDump(error_msg, exc_info=ex)
        except:
            pass

    else:
        msg = '瓦尔基里侦测到服务端有一个错误发生了'
        try:
            serverApi.GetEngineCompFactory().CreateGame(-1).SetTipMessage(msg)
        except:
            pass

        error_msg = ('服务端调用函数 {} 时出现错误:\nargs={}\nkwargs={}\n{}').format(func_name, str(args), str(kwargs), tb_str)
        logging.error(error_msg)
    return


