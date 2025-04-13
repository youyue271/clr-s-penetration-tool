# core/engine.py
import importlib
import time

import yaml
from typing import Dict, List

from core.message_bus import MessageBus
from core.state import StateMachine, EngineState, ModuleState
from core.thread_manager import ThreadManager
from modules.base_module import BaseModule


class PentestEngine:
    def __init__(self, config_path="config/config.yaml"):
        self.config_path = config_path
        self.modules: List[BaseModule] = []
        self.message_bus = MessageBus()
        self.current_context: Dict = {}
        self._state = StateMachine()
        self.thread_manager = ThreadManager()

    def _load_config(self, config_path):
        with open(config_path, encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        # 动态加载模块
        for module_dir, module_contents in self.config["modules"].items():
            for module_name, module_config in module_contents.items():
                if module_config.get('enable', False):
                    module = self._load_module(module_dir, module_name)
                    if module is not None:
                        self.modules.append(module)

    def _load_module(self, module_dir, module_name):
        try:
            # 动态导入模块（例如：modules.scanner）
            module = importlib.import_module(f"modules.{module_dir}.{module_name}")
            # 调用模块的工厂方法
            return module.create(self.message_bus, self.thread_manager)
        except (ImportError, AttributeError) as e:
            self._handle_error(f"模块加载失败: {module_name} - {str(e)}")

    def _handle_error(self, message):
        # 将错误信息发布到消息总线
        self.message_bus.publish("system_errors", {
            "type": "ENGINE_ERROR",
            "message": message,
            "timestamp": time.time()
        })
        self._state.transition(EngineState.ERROR)

    def run(self):

        while True:
            current_state = self._state.current

            if current_state == EngineState.INIT:
                self._load_config(self.config_path)
                self._state.transition(EngineState.RUNNING)
            elif current_state == EngineState.RUNNING:

                for module in self.modules:
                    module_state = module.state.current

                    if module_state == ModuleState.WAITING:
                        if module.waitMessage():
                            module.state.transition(ModuleState.READY)
                    elif module_state == ModuleState.READY:
                        if module.execute():
                            module.state.transition(ModuleState.RUNNING)
                    elif module_state == ModuleState.RUNNING:
                        if module.waitOutput():
                            module.state.transition(ModuleState.WAITING)
                    elif module_state == ModuleState.ERROR:
                        self._state.transition(EngineState.ERROR)

                    # if module.ready():
                    #     # 通过消息总线获取输入
                    #     input_data = self.message_bus.get_module_input(module.name)
                    #     # 执行模块逻辑
                    #     output = module.execute(self.current_context, input_data)
                    #     # 更新上下文
                    #     self.current_context.update(output)
                    #     # 发布结果到总线
                    #     self._publish_results(module.name, output)

                # 检查终止条件
                if self._check_termination():
                    self._state.transition(EngineState.COMPLETED)



            elif current_state == EngineState.ERROR:
                error_message = self.message_bus.subscribe("system_errors")['data']
                print(f"{error_message['type']}: {error_message['message']}")
                self._cleanup()
                return

            elif current_state == EngineState.COMPLETED:
                self._cleanup()
                return

    def _publish_results(self, module_name, data):
        # 自动路由到预设的通道
        channel_map = {
            "scanner": "scan_results",
            "vuln_detection": "vuln_alerts",
            "llm_advisor": "llm_commands"
        }
        self.message_bus.publish(channel_map.get(module_name, "default"), data)

    def _check_termination(self):
        # 实现自定义的终止条件判断逻辑

        # 如果都跑完了就完成了
        if len(self.modules) == 0:
            return True

        return False

    def _cleanup(self):
        for module in reversed(self.modules):
            module.cleanup()
