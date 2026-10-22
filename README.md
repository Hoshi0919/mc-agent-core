# McAgentCore：现代 Minecraft 智能问答助手核心架构（Java + Python 双栈）

针对 Minecraft 1.20.x ~ 1.21.x（Fabric / NeoForge / Paper）模组与服务端开发设计的非阻塞、防幻觉、交互式 AI 问答引擎。

---

## 🌟 核心特性（v1.4.0）

1. **严格 50ms Tick 保护（零卡顿）**：
   - 提取主线程不可变空间快照（坐标、视线射线检测、方块光照、生物群系）；
   - 提示词清洗、规则匹配、网络 HTTP I/O 完全移交异步工作线程池；
   - 结果通过 `client.execute()` 或 `server.execute()` 安全切回主线程渲染。

2. **本地确定性快速通路（0ms 响应、0 Token 消耗，全覆盖 27 大核心主题）**：
   - **基础生存与维度换算**：
     - 地狱传送门换算：精准计算 8:1 对应坐标（含负坐标向下取整）；
     - 下界传送门精准对齐：3D 欧氏距离与 8:1 换算，杜绝多门重定向串门；
     - 1.18+ 矿石层数查表：钻石 Y=-58、铁矿 Y=16/232 双峰、煤炭 Y=0 以上等；
     - 刷怪光照判定：1.18+ 敌对生物生成要求方块光照为 0。
   - **版本机制与高危攻防**：
     - 1.20+ 下界合金锻造模板与 7 钻石复制技巧；
     - 1.21 重锤 (Mace)、坠落粉碎击、致密/破甲专属附魔；
     - 1.21 自动合成器 (Crafter) 红石脉冲与槽位锁定；
     - 1.21 不祥之瓶 (Ominous Bottle)、试炼预兆、不祥刷怪笼与不祥宝库；
     - 循声守卫 (Warden) 4 次潜声激活、500HP、羊毛隔音与潜行诱敌；
     - 铜块 4 阶氧化、蜜脾打蜡保色、斧头除锈与引雷针放电。
   - **红石、工程与生存进阶**：
     - 权威附魔互斥规则：经验修补 vs 无限、近战三选一、重锤致密 vs 破甲等；
     - 村民职业与锁交易机制：首次交易永久锁定、未交易破坏讲台无限洗经验修补书；
     - 信标金字塔搭建与效果规格：1~4 层（9、34、83、164 矿物块）精准计算，4 层解锁急迫 II 秒挖深板岩；
     - 红石比较器与分类机数学：22 物品分类漏斗 (18-1-1-1-1)、41 物品防串线、容器满度信号；
     - 铁砧最优附魔：Prior Work 指数惩罚 (2^n-1)、40 级上限死锁规避、二叉树分组合并；
     - 酿造台药水配方：粗制药水底药、主材料表、发酵蛛眼变异反转与时长/等级调节；
     - 铁傀儡与刷铁机力学：3 村民绑定、20 分钟内睡眠检测、僵尸恐慌态与 16×13×16 生成空间排查；
     - 末影龙复活、折跃门与鞘翅探索：4 个末影水晶基岩底座复活龙、1x1 基岩折跃门通往 1000 格外岛、鞘翅飞行推进动力；
     - 潮涌核心搭建与水下主宰力学：海洋之心 + 8 鹦鹉螺壳合成、水体中心 5×5 海晶石框架（16 块单环 32 格，42 块三环满级 96 格）；
     - 村庄突袭 (Raid) 机制与村庄英雄：突袭预兆 30 秒爆发、多波次精英怪、不死图腾掉落与村庄英雄超低折扣；
     - 猪灵以物易物与猪灵蛮兵权威力学：金装防仇恨、破坏容器激怒禁忌、金锭易物、猪灵蛮兵卡位克制；
     - 30 级附魔台几何摆放与经验洗炼：恰好 15 个书架、1 格空气严禁遮挡、砂轮洗附魔与重置种子；
     - Java 版 vs 基岩版 (Bedrock) 差异：攻击 CD 与横扫之刃、全能副手 vs 受限副手、准连接性 (QC) 与吐方块。
   - **v1.4.0 新增生存红石与自动化分层蓝图**：
     - **全自动甘蔗/竹子机 (SUGAR_CANE_FARM)**：底层水槽+泥土/沙子（生长速度一致辟谣）、中层活塞、顶层侦测器（脸朝前注视第 3 格生长，切勿装在第 2 格防止频繁空推）、后置实心方块+红石粉传导；
     - **高效安全造石机与刷石力学 (STONE_GENERATOR)**：4 大流体生成法则（流动水与流动岩浆平面对撞生圆石、岩浆自上而下注入水面生石头、水冲岩浆源灭顶生黑曜石、岩浆接触灵魂土加蓝冰生玄武岩）、水流落差深坑防灭大忌；
     - **经典红石时钟与高频脉冲器 (REDSTONE_CLOCKS)**：比较器减法自激振荡极速脉冲（1~2 tick 极速时钟）、Etho 双漏斗嘴对嘴长周期时钟（每个物品 0.4 秒精确延时控制）；
     - **全自动南瓜/西瓜机 (PUMPKIN_MELON_FARM)**：湿润耕地结瓜动力学、Block State 状态更新侦测、活塞击碎（西瓜出切片、南瓜出整方块）、底层漏斗矿车穿透泥土隔空吸物。

3. **交互式 Chat 分页器与 Tellraw JSON 序列化器 (v1.4.0 新增)**：
   - `ChatPaginator`：针对 Minecraft 聊天窗口高度限制，自动将多行蓝图与攻略按页拆分，动态追加交互式翻页控制条 `§8[ §b◀ 上一页 §8] §7[ §e第 1/3 页 §7] §8[ §b下一页 ▶ §8]`；
   - `TellrawJsonBuilder`：0 依赖标准 Minecraft `/tellraw` JSON 序列化器，原生映射 `clickEvent` (`RUN_COMMAND`, `SUGGEST_COMMAND`) 与 `hoverEvent` (`show_text`)，可直接对接 Console、RCON 或 Fabric `ServerPlayer.sendSystemMessage()`。

4. **安全与性能工程底座 (v1.4.0 新增)**：
   - `PlayerRateLimiter`：基于令牌桶（Token Bucket）的玩家级防刷屏与配额管理器，支持突发容量（Burst）、冷却平滑回血与每日使用上限，返回平滑的倒计时警告 `§c[Hoshi] 提问过快！请等待 1.8 秒后再试。`；
   - `QueryCache`：线程安全的 LRU 内存缓存与 TTL 自动失效，高频重复问题 0ms 直接返回，内置完整的命中率与吞吐指标追踪。

5. **提示词防注入围栏（Prompt Safety Fence）**：
   - 防范多人聊天中的提示词越权攻击与伪造分隔符；
   - 系统提示词全量注入 27 大 Minecraft 地面真实规则 `<canonical_rules>`，彻底规避模型幻觉与版本漂移。

---

## 📂 项目结构

```
mc-agent-core/
├── build.gradle / settings.gradle
├── src/main/java/hoshi/mcagent/
│   ├── context/                         # 玩家与目标方块不可变快照
│   ├── engine/
│   │   ├── LocalGameRules.java         # 27 大核心主题 Ground Truth
│   │   ├── FastPathResolver.java        # Java 确定性快速求解器（27 类主题）\n│   │   └── PromptSafetyFence.java       # 提示词清洗与防注入围栏
│   ├── format/
│   │   ├── MinecraftTextFormatter.java  # Markdown 转 § 格式化与坐标识别
│   │   ├── TellrawJsonBuilder.java      # 原生 Vanilla /tellraw JSON 构造器
│   │   └── ChatPaginator.java           # 多页分页器与交互式按钮
│   ├── cache/
│   │   └── QueryCache.java              # 线程安全 LRU + TTL 查询缓存
│   ├── security/
│   │   └── PlayerRateLimiter.java       # 玩家级令牌桶冷却限流器
│   ├── async/
│   │   └── AsyncQueryDispatcher.java    # 整合缓存与限流的非阻塞异步分发器
│   └── McAgentCore.java                 # 统一门面 Facade 入口
├── src/test/java/hoshi/mcagent/
│   └── McAgentCoreTest.java             # Java 203 项全绿自动化回归测试
├── mc_agent_core/                       # Python 仿真套件与原型（全模块对齐）
└── tests/test_mc_agent_core.py          # Python 27 项端到端测试
```

---

## 🧪 自动化测试套件

### Java 参考实现
```bash
javac -encoding UTF-8 -d bin $(find src/main/java src/test/java -name '*.java')
java -cp bin hoshi.mcagent.McAgentCoreTest
# 🎉 All 203/203 Java tests passed successfully!
```

### Python 仿真套件
```bash
PYTHONPATH=. uv run --with pytest pytest tests/ -v
# 27 passed in 0.11s
```
