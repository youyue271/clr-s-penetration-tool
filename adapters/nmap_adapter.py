import subprocess
from typing import Dict

from adapters.base_adapter import BaseAdapter


class NmapAdapter(BaseAdapter):
    def __init__(self, config: dict):
        super().__init__("nmap", config)
        self.binary = self.tool_config['path']
        self.timeout = self.tool_config['timeout']
        if config is not None:
            self.default_params = self._config['params']

    @staticmethod
    def parse_output(output: str) -> list[Dict]:
        """解析Nmap XML输出"""
        outputlist = output.split('SERVICE\n')[1].split('\n\n')[0].split('\n')
        dataList = []
        for outputData in outputlist:
            try:
                port, state, service = [data for data in outputData.split(' ') if data]
                dataList.append({'port': port, 'state': state, 'service': service})
            except ValueError:
                pass

        return dataList

    def scan(self, target: str, output_path: str, params: dict = None) -> None:
        """执行Nmap扫描"""
        # 合并默认参数和自定义参数
        scan_params = {**self.default_params, **(params or {})}

        # 构建命令
        # todo:参数的处理逻辑需要进一步细化
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
