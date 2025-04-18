# clr's penetration tool

## 框架思路

整个项目核心逻辑分为三个部分

* `./core/engine.py`中定义的整个底层循环逻辑
* `./module/`下定义的各个组件的逻辑
* `./adapters`目录下定义的外部工具的调用逻辑

底层循环有五种状态:

* `INIT`: 框架初始化
* `RUNNING`: 框架运行
* `PAUSED`: 暂停运行状态(暂时没有使用)
* `ERROR`: 错误处理, 处理总线中的错误信号
* `COMPLETED`: 运行结束(结束的检测逻辑还没写, 现在运行是死循环)

在`RUNNING`状态下, 框架会遍历已启用的module(在`config.yaml`中设置 `enable=True`启用), 并循环执行

对于每一个module也分为若干状态:

* `WAITING`: 等待输入channel传输数据(`self.inputChannel`在Module初始化时手动指定)
* `READY`: 等到了输入数据以后, 启用一个新的线程(防止阻塞), 执行命令或者外部程序
* `RUNNING`: 表示module正在跑程序, 直到检测到线程(`self.thread`)执行完毕, 重新回到 `WAITING` 状态
* `ERROR`: 错误处理, `self.handle_error()`会发布错误信号, 并修改至这个状态
* `COMPLETED`: module运行结束的状态(目前还没有使用到)

以上两个状态机的定义位于 `./core/state.py`中

此外还有两个重要的处理逻辑

一个是信息总线( `./core/messge_bus.py` ),message_bus在Pentest类中实例化, 会在module热加载的时候传递给module,方便module调用总线上的内容,
每个module可以在总线上**publish**以及**subscribe**, 将模块之间独立了出来，给各个module解耦,
在message_bus上存在若干channel, channel维护一个message队列, 此外还设计了一个简单的优先级逻辑, 详见代码
注意一下, publish并不会创建channel, 在添加新的module的时候, 需要创建一个新的channal, 我更倾向于全部在channal初始化的时候新建,
也就是直接在 `message_bus.py` 中新建, 而非外module中, 当然新建channel的方法做成了public, 逻辑上是可以在module中调用的

另一个需要注意的结构是线程管理模块(简单的实现了一下,`./core/thread_manager.py`), 对线程进行集中管理,
主要是为了方便中止哪些高资源占用或者高耗时低收益的函数,
同message_bus一样, 在Pentest初始化的时候实例化, 并作为参数传递给module, 此外, 在每个module内部, 除了公用thread_manager以外,
还定义了一个`self.thread`,
这个是方便module内部对自己新建的module进行逻辑控制或者信息处理

## 加入新的模块
### 添加新module

添加如下代码到 `./modules`
假如我要在扫描步骤中添加一个对端口扫描的处理逻辑

class MessageBus:
pass

```python
# modules/scanner/port_scanner.py 
from modules.base_module import BaseModule
from core.message_bus import MessageBus
from core.thread_manager import ThreadManager


def create(message_bus: MessageBus, thread_manager: ThreadManager):
    return PortScanner("scanner",
                       "port_scanner",
                       ["scan_target"],
                       message_bus,
                       thread_manager)


class PortScanner(BaseModule):
    def __init__(self, step, name, inputChannel, message_bus, thread_manager):
        super().__init__(step, name, inputChannel, message_bus, thread_manager)

    def waitOutput(self) -> None:
        pass

    def execute(self) -> None:
        pass

    def cleanup(self) -> None:
        pass
```

`BaseModule`作为基准类, 定义了若干Module能够使用的公共方法, 包括WAITING阶段的waitMessage函数,
因为接收某个特定channel的内容, 逻辑简单, 就在基准类中实现了, 需要在初始化的时候传递`inputChannel`参数
注意step和name分别对应你定义module的py文件上层文件夹名字以及py文件名, 为了统一, 在module文件中还需要包装一个`create`工厂函数

### 加入新的adapter

同module一样, 写了一个基准类 `BaseAdapter`, adapter的逻辑目前并不是特别完善, 暂时打算是处理两个部分
* 外部程序的调用, 包括参数包装等逻辑
* 外部程序输出的格式化, 输出统一存储为文件, 然后从文件中读取, 需要定义针对性的内容结构化函数

## TODO

1. [ ] logger的编写, 需要统一处理日志, 目前写了一部分, 但是还没有测试调用
2. [ ] 前台输出函数, 打算类似afl写一个`show_stat`函数定时更新状态,刷写在终端上
3. [ ] 具体的module还需要根据情况添加, 包括nmap这些还需要进一步细化逻辑
4. [ ] tools扫描, 检测存在的工具, 生成config.yaml
5. [ ] 有机会可以加入llm辅助处理
6. [ ] 处理结果的本地化存储, 可能会涉及使用database进行存储