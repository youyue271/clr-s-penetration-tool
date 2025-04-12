import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List

from adapters.base_adapter import BaseAdapter


class NmapAdapter(BaseAdapter):
    def __init__(self, config: dict):
        super().__init__("nmap", config)
        self.binary = self.tool_config['path']
        self.timeout = self.tool_config['timeout']
        if config is not None:
            self.default_params = self._config['params']

    @staticmethod
    def _parse_xml(xml_output: str) -> Dict:
        """解析Nmap XML输出"""
        root = ET.fromstring(xml_output)
        result = {'target': '', 'ports': []}

        # 解析目标信息
        host = root.find('host')
        if host is not None:
            address = host.find('address')
            if address is not None:
                result['target'] = address.get('addr', '')

            # 解析端口信息
            ports = host.find('ports')
            if ports is not None:
                for port in ports.findall('port'):
                    port_data = {
                        'port': port.get('portid'),
                        'protocol': port.get('protocol'),
                        'state': port.find('state').get('state'),
                        'service': port.find('service').get('name'),
                        'version': port.find('service').get('product'),
                        'scripts': []
                    }

                    # 解析脚本输出
                    scripts = port.findall('script')
                    for script in scripts:
                        script_data = {
                            'id': script.get('id'),
                            'output': script.get('output')
                        }
                        port_data['scripts'].append(script_data)

                    result['ports'].append(port_data)
        return result

    def scan(self, target: str, output_path: str, params: dict = None) -> None:
        """执行Nmap扫描"""
        # 合并默认参数和自定义参数
        scan_params = {**self.default_params, **(params or {})}

        # 构建命令
        cmd = [
            self.binary,
            # '-Pn',
            # '-sV',
            # f"-T{scan_params['timing']}",
            # f"-p {scan_params['ports']}",
            # f"--script={scan_params['script']}",
            # '-oX', '-',  # 输出到标准输出
            target,
        ]

        print(" ".join(cmd))

        # 执行扫描
        try:
            with open(output_path, "w") as f:
                subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    timeout=self.timeout,
                    text=True,
                    check=True
                )
            return

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Nmap扫描失败: {e.stderr}") from e
        except subprocess.TimeoutExpired:
            raise RuntimeError("扫描超时，请调整timeout设置")
