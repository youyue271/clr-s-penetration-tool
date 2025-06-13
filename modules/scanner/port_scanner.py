# modules/scanner/port_scanner.py
import os

from adapters.nmap_adapter import NmapAdapter
from core.message_bus import MessageBus
from core.thread_manager import ThreadManager
from modules.base_module import BaseModule


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
        self.tmp_path = None
        self.thread = None

    def execute(self) -> bool:
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
            self.thread = self.thread_manager.addProcess(self.scanner.scan, "Nmap scanner", (self.data['ip'],self.tmp_path, self._config))

            print(f"端口扫描器初始化完成，开始扫描端口范围: {ports}")
            return True

        except Exception as e:
            self.handle_error(e, critical=True)
            return False

    def waitOutput(self, inputs=None):
        """执行端口扫描"""
        try:
            if self.thread.is_alive():
                return
            else:
                with open(self.tmp_path, "r") as f:
                    output = f.read()
                if len(output):
                    scan_results = self.scanner.parse_xml(output)
                    # 发布结果到总线
                    for scan_result in scan_results:
                        self.publish_message(
                            channel="scan_results",
                            data=scan_result,
                            priority=1
                        )
                    return True
                else:
                    print(self.tmp_path + "中没有内容")
                    return True

        except Exception as e:
            self.handle_error(e)
            return False

    def cleanup(self):
        """释放资源"""
        self.thread = None
        self.thread_manager.checkAlive()
        print("端口扫描资源已释放")


