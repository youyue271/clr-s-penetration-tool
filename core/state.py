# core/states.py
from enum import Enum, auto


class EngineState(Enum):
    INIT = auto()
    RUNNING = auto()
    PAUSED = auto()
    ERROR = auto()
    COMPLETED = auto()


class StateMachine:
    _transitions = {
        EngineState.INIT: [EngineState.RUNNING, EngineState.ERROR],
        EngineState.RUNNING: [EngineState.PAUSED, EngineState.ERROR, EngineState.COMPLETED],
        EngineState.PAUSED: [EngineState.RUNNING, EngineState.ERROR],
        EngineState.ERROR: [EngineState.INIT],
        EngineState.COMPLETED: []
    }

    def __init__(self):
        self.current = EngineState.INIT

    def transition(self, new_state):
        if new_state in self._transitions[self.current]:
            self.current = new_state
            return True
        return False


class ModuleState(Enum):
    READY = auto()
    WAITING = auto()  # 等待可用输入
    RUNNING = auto()  # 运行可用输入
    ERROR = auto()  # 超时等
    COMPLETED = auto()  # 结束


class StateModule:
    _transitions = {
        ModuleState.WAITING: [ModuleState.READY, ModuleState.ERROR],
        ModuleState.READY: [ModuleState.RUNNING, ModuleState.ERROR],
        ModuleState.RUNNING: [ModuleState.WAITING, ModuleState.ERROR, ModuleState.COMPLETED],
        ModuleState.ERROR: [],
        ModuleState.COMPLETED: []
    }

    def __init__(self):
        self.current = ModuleState.WAITING

    def transition(self, new_state):
        if new_state in self._transitions[self.current]:
            self.current = new_state
            return True
        return False
