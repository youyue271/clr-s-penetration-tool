# modules/base_module.py
import abc
import logging
from typing import Dict, Any, Optional, List

import yaml

from core.message_bus import MessageBus
from core.state import StateModule, ModuleState
from core.thread_manager import ThreadManager


class BaseModule(metaclass=abc.ABCMeta):
    """所有功能模块必须继承的抽象基类"""

    def __init__(self,
                 step,
                 name,
                 inputChannel: List[str],
                 message_bus: MessageBus,
                 thread_manager:ThreadManager,
                 context: Optional[Dict[str, Any]] = None,
                 ):
        """
        初始化模块
        :param name: Module name
        :param inputChannel: 等待的消息通道名称
        :param message_bus: 消息总线实例
        :param context: 全局上下文数据
        """
        # 基础属性
        self.name = name
        self.step = step
        self.state = StateModule()
        self.messages = None
        self.data = None
        self.inputChannel = inputChannel
        self._config = self._load_module_config(self.step, self.name)
        self._message_bus: MessageBus = message_bus
        self._context = context or {}
        self.thread_manager:ThreadManager = thread_manager
        # self._last_error = None

    def waitMessage(self) -> bool:
        """等待消息逻辑（必须实现）"""
        messages = self.subscribe_messages(self.inputChannel)
        if messages is not None:
            self.messages = messages
            self.data = messages.get('data', {})
            return True
        return False

    @abc.abstractmethod
    def waitOutput(self) -> None:
        """资源清理操作（必须实现）"""
        pass

    # @property
    # def module_meta(self) -> Dict:
    #     """模块元数据"""
    #     return {
    #         'name': self.name,
    #         'version': '1.0.0',
    #         'description': 'Base module implementation'
    #     }

    @abc.abstractmethod
    def execute(self) -> None:
        """执行模块核心功能（必须实现）
        :param inputs: 来自消息总线的输入数据
        :return: 更新后的上下文数据
        """
        pass

    @abc.abstractmethod
    def cleanup(self) -> None:
        """资源清理操作（必须实现）"""
        pass

    def ready(self) -> bool:
        """检查模块是否就绪（可重写）"""
        # return not self._last_error

    # region 消息总线操作
    def publish_message(self,
                        channel: str,
                        data: Dict,
                        priority: int = 0) -> None:
        """发布消息到总线"""
        if self._message_bus:
            try:
                self._message_bus.publish(
                    channel=channel,
                    message={
                        'module': self.name,
                        'data': data
                    },
                    priority=priority
                )
                print(f"消息发布到 {channel}: {data.values()}")
            except Exception as e:
                print(f"发布消息失败: {str(e)}")
                # self._last_error = e

    def subscribe_messages(self,
                           channels: List[str],
                           timeout: int = 5)-> Dict:
        """从总线订阅消息"""
        collected = []
        for channel in channels:
            msg = self._message_bus.subscribe(channel, timeout)
            if msg:
                return msg

    # endregion

    # region 工具方法
    @staticmethod
    def _load_module_config(tool_step:str, tool_name: str) -> Dict:
        """获取工具适配器配置"""
        with open("config/config.yaml", encoding='utf-8') as f:
            config = yaml.safe_load(f)

        modules = config['modules'].get(tool_step, {})

        return modules.get(tool_name, {})




    def update_context(self, new_data: Dict) -> None:
        """安全更新全局上下文"""
        self._context.update(new_data)
        print(f"上下文更新: {list(new_data.keys())}")

    def handle_error(self,
                     error: Exception,
                     critical: bool = False) -> None:
        """统一错误处理"""
        # self._last_error = error
        error_msg = f"{self.name} 错误: {str(error)}"

        print(error_msg)
        self.publish_message(
            channel="module_errors",
            data={
                'module': self.name,
                'error': error_msg,
                'critical': critical
            },
            priority=2  # 最高优先级
        )

        if critical:
            self.cleanup()
            raise RuntimeError(error_msg)

        self.state.transition(ModuleState.ERROR)

    # endregion

    # region 生命周期管理
    def __enter__(self):
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
    # endregion
