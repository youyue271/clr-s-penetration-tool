# adapters/base_adapter.py
import abc
import os
import subprocess
import shlex
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, Union

import yaml

from utils.logger import get_logger


class BaseAdapter(metaclass=abc.ABCMeta):
    """所有工具适配器的抽象基类"""

    def __init__(self,
                 tool_name: str,
                 config: Dict[str, Any] = None,
                 timeout: int = 600):
        """
        :param config: 全局配置字典
        :param tool_name: 工具名称（对应配置中的键）
        :param timeout: 默认执行超时时间（秒）
        """

        self._adapter_name = tool_name
        self._config = config

        self.logger = get_logger(f"Adapter.{self.__class__.__name__}")
        self.timeout = timeout

        # self.inputChannels = []
        # self.outputChannels = []


        # 加载工具配置
        self.tool_config = self._load_tool_config(self._adapter_name)

        # 验证必要配置项
        # self._validate_config()

        # 初始化状态
        self._process: Optional[subprocess.Popen] = None

    @staticmethod
    def _load_tool_config(tool_name: str) -> Dict:
        """获取工具适配器配置"""
        with open("config/config.yaml", encoding='utf-8') as f:
            config = yaml.safe_load(f)

        adapters = config['adapters']

        return adapters.get(tool_name, {})

    # @abc.abstractmethod
    # def _validate_config(self):
    #     """验证必要配置项（必须实现）"""
    #     pass

    # @property
    # @abc.abstractmethod
    # def binary_path(self) -> Path:
    #     """工具可执行文件路径（必须实现）"""
    #     pass

    # @abc.abstractmethod
    # def build_command(self, *args, **kwargs) -> list:
    #     """构建命令行参数（必须实现）
    #     返回示例: ["nmap", "-sV", "127.0.0.1"]
    #     """
    #     pass

    def pre_execute(self, *args, **kwargs) -> None:
        """命令执行前的准备工作（可选重写）"""
        pass

    def post_execute(self, result: Any) -> Any:
        """命令执行后的处理（可选重写）"""
        return result

    # @abc.abstractmethod
    # def parse_output(self, raw_output: str) -> Any:
    #     """解析工具原始输出（必须实现）"""
    #     pass

    def execute(self, *args, **kwargs) -> Tuple[bool, Union[Dict, str]]:
        """执行工具的完整流程"""

        try:
            # 1. 前置处理
            self.pre_execute(*args, **kwargs)

            # 2. 构建命令
            command = self.build_command(*args, **kwargs)
            self.logger.debug(f"执行命令: {self._safe_quote_command(command)}")

            # 3. 执行命令
            result = self._run_command(command)

            # 4. 解析输出
            parsed = self.parse_output(result.stdout)

            # 5. 后置处理
            final_result = self.post_execute(parsed)

            return True, final_result

        except subprocess.TimeoutExpired:
            error_msg = f"{self.tool_name} 执行超时（{self.timeout}s）"
            self.logger.error(error_msg)
            return False, {"error": error_msg}

        except Exception as e:
            error_msg = f"{self.tool_name} 执行失败: {str(e)}"
            self.logger.exception(error_msg)
            return False, {"error": error_msg}

        finally:
            self._cleanup_process()

    def _run_command(self, command: list) -> subprocess.CompletedProcess:
        """执行命令并返回结果"""
        self._process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )

        try:
            stdout, stderr = self._process.communicate(timeout=self.timeout)

            if self._process.returncode != 0:
                raise RuntimeError(
                    f"工具返回错误代码 {self._process.returncode}\n"
                    f"Stderr: {stderr.strip()}"
                )

            return subprocess.CompletedProcess(
                args=command,
                returncode=self._process.returncode,
                stdout=stdout,
                stderr=stderr
            )

        finally:
            self._cleanup_process()

    def _cleanup_process(self):
        """清理进程资源"""
        if self._process and self._process.poll() is None:
            self.logger.warning("强制终止运行中的进程...")
            self._process.kill()
            self._process.wait()
        self._process = None

    def _safe_quote_command(self, command: list) -> str:
        """安全转义命令用于日志记录"""
        return " ".join([shlex.quote(str(c)) for c in command])

    @classmethod
    def get_config_template(cls) -> Dict:
        """返回配置模板（供文档使用）"""
        return {
            "path": "/path/to/executable",
            "timeout": 600,
            "common_options": {
                "verbose": "-v",
                "output_format": "-oX"
            }
        }

    # 可能需要重写的方法
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cleanup_process()
