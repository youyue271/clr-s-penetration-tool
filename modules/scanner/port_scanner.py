# modules/scanner/port_scanner.py
import os
import tempfile
import time

from core.message_bus import MessageBus
from core.state import ModuleState
from core.thread_manager import ThreadManager
from modules.base_module import BaseModule
from adapters.nmap_adapter import NmapAdapter


def create(message_bus: MessageBus, thread_manager: ThreadManager):
    return PortScanner("scanner",
                       "port_scanner",
                       ["scan_target"],
                       message_bus,
                       thread_manager)


class PortScanner(BaseModule):
    def getErrorMessage(self) -> str:
        pass

    def __init__(self, step, name, inputChannel, message_bus, thread_manager):
        super().__init__(step, name, inputChannel, message_bus, thread_manager)

        self.scanner = None
        self.current_target = None
        self.tmp_path = None

    def execute(self) -> None:
        """运行外部程序"""
        try:
            self.scanner = NmapAdapter(self._config)
            # 读取模块特定配置
            ports = self._config.get("ports", "1-1024")
            timeout = self._config.get("timeout", 300)
            tmp_dir = "./tmp/port_scanner/"
            if not os.path.exists(tmp_dir):
                os.makedirs(tmp_dir)
            self.tmp_path = tmp_dir + "nmap_scan.result"
            self.thread_manager.addProcess(self.scanner.scan, "Nmap scanner", ('127.0.0.1',self.tmp_path, self._config))

            print(f"端口扫描器初始化完成，扫描端口范围: {ports}")
            self.state.transition(ModuleState.RUNNING)

        except Exception as e:
            self.handle_error(e, critical=True)

    def waitOutput(self, inputs=None):
        """执行端口扫描"""
        try:
            # 获取扫描目标（多种来源）
            targets = self._resolve_targets(inputs)
            results = {}

            for target in targets:
                self.current_target = target
                print(f"开始扫描 {target}")

                # 调用适配器执行扫描
                scan_result = self.scanner.scan(
                    target=target,
                    ports=self.ports,
                    timeout=self.timeout
                )

                # 发布结果到总线
                self.publish_message(
                    channel="scan_results",
                    data=scan_result,
                    priority=1
                )

                # 更新上下文
                results[target] = scan_result
                self.update_context({"scan_results": results})

            return results

        except Exception as e:
            self.handle_error(e)
            return {}

    def cleanup(self):
        """释放资源"""
        if self.scanner:
            self.scanner.close()
        self.current_target = None
        print("端口扫描资源已释放")

    def _resolve_targets(self, inputs):
        """解析目标来源：优先级
        1. 直接输入
        2. 上下文中的目标
        3. 配置文件默认值"""
        if inputs:
            return [item.get("target") for item in inputs]
        return self._context.get("targets") or \
            self._config.get("default_targets")
