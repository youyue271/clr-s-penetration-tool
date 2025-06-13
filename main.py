from core.engine import PentestEngine
from core.state import EngineState


def main():
    # 初始化引擎
    engine = PentestEngine(config_path="config/config.yaml")

    engine.message_bus.publish("scan_target", {
        "ip": "39.99.240.195",
    })

    # 运行引擎
    try:
        engine.run()
    except KeyboardInterrupt:
        engine._state = EngineState.COMPLETED
        print("\n渗透测试已中止")


if __name__ == "__main__":
    main()