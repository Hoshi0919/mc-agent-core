# McAgentCore: 现代 Minecraft 智能问答助手核心架构 (Java + Python 双栈)

针对 Minecraft 1.20.x ~ 1.21.x (Fabric / NeoForge) 模组开发设计的非阻塞、防幻觉、交互式 AI 问答引擎。

---

## 🌟 核心特性 (v1.1.0)

1. **严格 50ms Tick 保护 (零卡顿)**：
   - 提取主线程不可变空间快照（坐标、视线射线检测、方块光照、生物群系），耗时 `< 0.2ms`；
   - 所有提示词清洗、规则匹对、网络 HTTP I/O 完全移交异步工作线程池；
   - 结果通过 `client.execute()` 或 `server.execute()` 安全切回主线程进行渲染和音效反馈。

2. **本地确定性快速通路 (0ms 响应、0 Token 消耗、零幻觉)**：
   - **地狱传送门换算**：精准计算 8:1 对应坐标（向下取整与负坐标换算）；
   - **1.18+ 矿石层数查表**：精准输出钻石（Y=-58）、铁矿（Y=16/232 双峰）、煤炭（Y=0 以上）等权威分布；
   - **刷怪光照判定**：基于玩家十字准星方块的 `block_light` 进行实时判定（1.18+ 方块光照必须严格为 0）；
   - **1.20+ 锻造模板**：提示必须使用下界合金升级锻造模板与 7 钻石复制技巧；
   - **1.21 试炼密室**：重锤（重型核心 + 旋风棒）、自动合成器（红石脉冲触发）等核心机制；
   - **附魔互斥与冲突**：弓箭【经验修补】与【无限】互斥、近战伤害附魔（锋利/亡灵/节肢）互斥、重锤【致密】与【破甲】互斥、防具减伤互斥、精准采集与时运互斥；
   - **村民锁交易与职业**：一旦产生首次交易即永久锁定职业与交易项；讲台重置刷新经验修补书核心机制；
   - **信标金字塔规格**：1~4 层（9, 34, 83, 164 矿物块）精准计算，解锁【急迫 II】秒挖深板岩特权；
   - **1.21 不祥之瓶与试炼预兆**：击杀队长掉落不祥之瓶，喝下转化为试炼预兆，开启不祥宝库获取重型核心；
   - **循声守卫与潜声体**：4 次激活钻地召唤、羊毛/地毯隔绝声音振动、500 点 HP 属性预警；
   - **铜块氧化与打蜡除锈**：4 阶段氧化、蜜脾打蜡保色、斧头除锈削蜡、引雷针雷击除锈。

3. **提示词防注入围栏 (Prompt Safety Fence)**：
   - 防范恶意玩家在多人聊天中的提示词越权攻击（`ignore previous instructions`、`/op` 注入等）；
   - 自动在系统提示词中注入权威游戏力学规则（Ground Truth），杜绝大模型版本漂移幻觉。

4. **游戏内富文本与交互动作 (Minecraft Clickable Components)**：
   - 坐标自动高亮为金色可点击组件，点击自动将 `/tp X Y Z` 填入聊天框；
   - 包含悬浮提示（HoverEvent）与快捷指令推荐按钮。

5. **Gradle 构建与 Fabric / NeoForge 快速接入**：
   - 提供标准 `build.gradle` 与 `settings.gradle`，支持作为子模块或依赖库直接引入模组工程。

---

## 📂 项目结构

```
mc-agent-core/
├── build.gradle                      # Gradle 标准构建配置 (Java 21 toolchain)
├── settings.gradle
├── src/main/java/hoshi/mcagent/       # Java 21 生产级参考实现 (适用于 Fabric / NeoForge)
│   ├── context/
│   │   ├── TargetBlock.java          # 视线光线投射目标方块
│   │   └── ContextSnapshot.java      # 玩家空间环境快照
│   ├── engine/
│   │   ├── LocalGameRules.java       # 1.18~1.21 权威力学规则 (附魔/村民/信标/试炼/守卫/铜)
│   │   ├── FastPathResolver.java     # 0ms 本地确定性求解器 (12 大高频领域)
│   │   └── PromptSafetyFence.java    # 提示词清洗与防注入围栏
│   ├── format/
│   │   └── MinecraftTextFormatter.java # 聊天组件解析与 Click/Hover 事件
│   ├── async/
│   │   └── AsyncQueryDispatcher.java # CompletableFuture 异步线程调度
│   └── McAgentCore.java              # 门面核心入口
│
├── src/test/java/hoshi/mcagent/      # Java 单元测试集
│   └── McAgentCoreTest.java          # 90 项严密断言全部通过
│
├── mc_agent_core/                    # Python 原型与仿真测试包
│   ├── __init__.py
│   ├── context.py
│   ├── rules.py
│   ├── fast_path.py
│   ├── fence.py
│   ├── formatter.py
│   └── dispatcher.py
│
└── tests/                            # pytest 自动化测试套件
    └── test_mc_agent_core.py         # 16 项端到端测试用例
```

---

## 🧪 验证与运行

### 1. Java 21 编译与测试 (90 项严密断言)
```bash
javac -d bin $(find src -name "*.java")
java -cp bin hoshi.mcagent.McAgentCoreTest
# 🎉 All 90/90 Java tests passed successfully!
```

### 2. Python 仿真套件运行 (16 项测试)
```bash
PYTHONPATH=. uv run --with pytest pytest tests/test_mc_agent_core.py -v
# 16 passed in 0.07s
```
