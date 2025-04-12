# core/engine.py
import importlib
import yaml
from typing import Dict, List
from modules.base_module import BaseModule


class PentestEngine:
    def __init__(self, config_path="config/config.yaml"):
        self.modules: List[BaseModule] = []
        self.message_bus = MessageBus()
        self.current_context: Dict = {}
        self._load_config(config_path)
        self._state = "INIT"

    def _load_config(self, config_path):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        # 动态加载模块
        for module_name, module_config in self.config['modules'].items():
            if module_config.get('enable', False):
                module = self._load_module(module_name, module_config)
                self.modules.append(module)

    def _load_module(self, module_name, config):
        try:
            # 动态导入模块（例如：modules.scanner）
            module = importlib.import_module(f"modules.{module_name}")
            # 调用模块的工厂方法
            return module.create(config, self.message_bus)
        except (ImportError, AttributeError) as e:
            self._handle_error(f"模块加载失败: {module_name} - {str(e)}")

    def _handle_error(self, message):
        # 将错误信息发布到消息总线
        self.message_bus.publish("system_errors", {
            "type": "ENGINE_ERROR",
            "message": message,
            "timestamp": time.time()
        })
        self._state = "ERROR"

    def run(self):
        self._state = "RUNNING"
        try:
            # 初始化阶段
            for module in self.modules:
                module.initialize()

            # 执行流水线
            while self._state == "RUNNING":
                for module in self.modules:
                    if module.ready():
                        # 通过消息总线获取输入
                        input_data = self.message_bus.get_module_input(module.name)
                        # 执行模块逻辑
                        output = module.execute(self.current_context, input_data)
                        # 更新上下文
                        self.current_context.update(output)
                        # 发布结果到总线
                        self._publish_results(module.name, output)

                # 检查终止条件
                if self._check_termination():
                    self._state = "COMPLETED"

        finally:
            # 清理阶段
            self._cleanup()

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
        return False

    def _cleanup(self):
        for module in reversed(self.modules):
            module.cleanup()