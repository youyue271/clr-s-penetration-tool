from core.engine import PentestEngine
from core.message_bus import MessageBus


def main():
    # 初始化引擎
    engine = PentestEngine(config_path="config/config.yaml")

    # 手动设置目标（实际可从命令行获取）
    initial_context = {
        "targets": ["192.168.1.105"],
        "scan_type": "full"
    }

    engine.message_bus.publish("scan_target", {
        "ip": "192.168.1.105",
    })

    # # 创建消息总线监听器
    # def scan_result_listener():
    #     while True:
    #         result = engine.message_bus.subscribe("scan_results")
    #         if result:
    #             print("\n[扫描结果]")
    #             print(f"目标: {result['data']['target']}")
    #             for port in result['data']['ports']:
    #                 print(f"端口 {port['port']}/{port['protocol']} - {port['state']}")
    #                 if port['scripts']:
    #                     print(f"检测到漏洞: {len(port['scripts'])} 个")
    #
    # # 启动监听线程
    # import threading
    # listener_thread = threading.Thread(target=scan_result_listener, daemon=True)
    # listener_thread.start()

    # 运行引擎
    try:
        engine.run()
    except KeyboardInterrupt:
        engine._state = "COMPLETED"
        print("\n扫描已中止")


if __name__ == "__main__":
    main()