# McAgentCore：现代 Minecraft 智能问答助手核心架构（Java + Python 双栈）

针对 Minecraft 1.20.x ~ 1.21.x（Fabric / NeoForge）模组开发设计的非阻塞、防幻觉、交互式 AI 问答引擎。

---

## 🌟 核心特性（v1.2.0-dev）

1. **严格 50ms Tick 保护（零卡顿）**：
   - 提取主线程不可变空间快照（坐标、视线射线检测、方块光照、生物群系）；
   - 提示词清洗、规则匹配、网络 HTTP I/O 完全移交异步工作线程池；
   - 结果通过 `client.execute()` 或 `server.execute()` 安全切回主线程渲染。

2. **本地确定性快速通路（0ms 响应、0 Token 消耗）**：
   - 地狱传送门换算：精准计算 8:1 对应坐标（含负坐标向下取整）；
   - 1.18+ 矿石层数查表：钻石 Y=-58、铁矿 Y=16/232 双峰、煤炭 Y=0 以上等；
   - 刷怪光照判定：1.18+ 敌对生物生成要求方块光照为 0；
   - 1.20+ 下界合金锻造模板与复制技巧；
   - 1.21 重锤、自动合成器、不祥之瓶、试炼预兆、循声守卫、铜块氧化与打蜡；
   - 附魔互斥、村民锁交易、信标金字塔等高频机制；
   - **红石比较器与分类机数学**：22 物品分类漏斗、41 物品防串线、容器满度信号；
   - **铁砧最优附魔**：Prior Work 指数惩罚、40 级上限、二叉树合并；
   - **酿造台药水配方**：底药、主材料、发酵蛛眼变异与时长/等级调节；
   - **铁傀儡与刷铁机**：村民、睡眠、恐慌和生成空间排查；
   - **下界传送门精准对齐**：8:1 坐标换算与多门串门修复。

3. **提示词防注入围栏（Prompt Safety Fence）**：
   - 防范多人聊天中的提示词越权攻击与伪造分隔符；
   - 系统提示词注入统一的 Minecraft 规则 Ground Truth，降低版本漂移。

4. **游戏内富文本与交互动作**：
   - 坐标自动高亮为可点击组件，支持填入 `/tp X Y Z`；
   - 包含悬浮提示与快捷指令推荐按钮。

5. **Gradle 构建配置**：
   - 提供 Java 21 Toolchain 与 Maven Publish 配置，支持作为 Fabric / NeoForge 子模块或依赖库接入。

---

## 📂 项目结构

```
mc-agent-core/
├── build.gradle / settings.gradle
├── src/main/java/hoshi/mcagent/
│   ├── context/                         # 玩家与目标方块快照
│   ├── engine/
│   │   ├── LocalGameRules.java         # 规则 Ground Truth（17 类主题）
│   │   ├── FastPathResolver.java        # Java 确定性快速求解器（17 类主题）
│   │   └── PromptSafetyFence.java       # 提示词清洗与防注入围栏
│   ├── format/                          # Minecraft Click/Hover 组件
│   ├── async/                           # CompletableFuture 异步调度
│   └── McAgentCore.java                 # 门面入口
├── src/test/java/hoshi/mcagent/
│   └── McAgentCoreTest.java             # Java 回归与新增主题测试
├── mc_agent_core/                       # Python 原型
└── tests/test_mc_agent_core.py          # Python 端到端测试
```

---

## 🧪 已执行验证

### Java 参考实现
```bash
javac -encoding UTF-8 -d bin $(find src/main/java src/test/java -name '*.java')
java -cp bin hoshi.mcagent.McAgentCoreTest
# 🎉 All 110/110 Java tests passed successfully!
```

### Python 仿真套件
```bash
PYTHONPATH=. uv run --with pytest pytest tests/
# 18 passed
```

> 当前环境没有 `gradle` 或 `gradlew`，所以未执行 Gradle task；上面的 `javac` 与 Java 主测试已实际通过。