# McAgentCore：现代 Minecraft 智能问答助手核心架构（Java + Python 双栈）

针对 Minecraft 1.20.x ~ 1.21.x（Fabric / NeoForge / Paper）模组与服务端开发设计的非阻塞、防幻觉、交互式 AI 问答引擎。

---

## 🌟 核心特性（v1.5.0）

1. **全功能游戏内指令路由与公屏触发器 (`CommandRouter`)**：
   - 统一分发 `/hoshi` 与 `/ai` 斜杠指令：
     - `/hoshi ask <问题>`：交互式咨询游戏机制或红石攻略；
     - `/hoshi page <页码>`：无缝翻阅长篇蓝图或攻略下一页；
     - `/hoshi bom <方案> [数量]`：快速生成红石构件材料清单与生存堆叠折算；
     - `/hoshi nether [x y z]`：转换下界/主界传送门对应坐标（省略坐标时自动调用玩家当前快照）；
     - `/hoshi stats`：实时查看服务端缓存命中率、吞吐量与活跃会话数；
     - `/hoshi clear`：清空玩家个人会话记忆与翻页缓存；
     - `/hoshi help`：交互式指令帮助面板（包含可点击的建议指令）。
   - 公屏聊天自动唤醒触发：支持 `!问题`、`?问题`、`@ai 问题`、`@hoshi 问题` 原生提取与路由。

2. **玩家多轮会话记忆与生命周期管理 (`PlayerSessionManager` & `PlayerSession`)**：
   - 为每位玩家维护独立的有界滑动窗口对话记忆（默认 5 轮，杜绝多人服务器内存膨胀）；
   - 维护玩家活跃的 `PagedResult` 上下文，彻底打通 `/tellraw` 点击交互与 `/hoshi page <n>` 翻页链路；
   - 追踪活跃主题与时间戳，支持 TTL 自动过期与无锁清理。

3. **生存红石材料清单 (BOM) 与堆叠折算器 (`MaterialCalculator` & `BlueprintBOM`)**：
   - 覆盖 6 大经典生存与红石自动化蓝图（甘蔗机、南瓜机、1~4 级信标金字塔、安全刷石机、22 项物品分类机、Etho 漏斗时钟）；
   - 自动化 Minecraft 堆叠换算：将大额方块数量智能折算为“组 + 个”（例如 `164 矿物块 = 2 组 + 36 个`，原料折算 `1476 铁锭 = 23 组 + 4 个`）；
   - 一键生成 Vanilla Tellraw JSON，点击构件即可在聊天框填入对应的 `/give @s <itemId> <count>` 获取指令。

4. **本地确定性快速通路（0ms 响应、0 Token 消耗，全覆盖 30 大核心主题）**：
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
     - Java 版 vs 基岩版 (Bedrock) 差异：攻击 CD 与横扫之刃、全能副手 vs 受限副手、准连接性 (QC) 与吐方块；
     - 全自动甘蔗/竹子机 (SUGAR_CANE_FARM)：底层水槽+泥土/沙子、中层活塞、顶层侦测器（注视第 3 格）；
     - 高效安全造石机与刷石力学 (STONE_GENERATOR)：4 大流体生成法则、水流落差深坑防灭大忌；
     - 经典红石时钟与高频脉冲器 (REDSTONE_CLOCKS)：比较器减法自激振荡极速脉冲、Etho 双漏斗长周期时钟；
     - 全自动南瓜/西瓜机 (PUMPKIN_MELON_FARM)：湿润耕地结瓜动力学、Block State 状态更新侦测、底层漏斗矿车穿透吸物；
     - **v1.5.0 新增核心主题**：
       - **村民繁殖与有效床位动力学 (VILLAGER_BREEDING)**：床头正上方必须有至少 2 格完整透明/空气高度（小村民跳床寻路判定）、3 面包/12 胡萝卜意愿度消耗、幼年 20 分钟（24000 ticks）成年；
       - **全自动村民农田机制 (VILLAGER_CROP_FARM)**：棕袍农民 AI、入场前投喂 8 组单一作物背包防杂物堵死、隔墙栅栏投喂漏斗拦截法与漏斗矿车穿透吸物；
       - **高能自动化燃料与熔炼动力学 (SMELTING_FUEL_EFFICIENCY)**：200 ticks (10.0 秒) 标准熔炼时钟、岩浆桶 (100 个返还铁桶)、煤炭块 (80 个)、干海带块 (20 个可再生首选)、熔炉阵列双漏斗推流。

5. **交互式 Chat 分页器与 Tellraw JSON 序列化器**：
   - `ChatPaginator`：针对 Minecraft 聊天窗口高度限制，自动将多行蓝图与攻略按页拆分，动态追加交互式翻页控制条 `§8[ §b◀ 上一页 §8] §7[ §e第 1/3 页 §7] §8[ §b下一页 ▶ §8]`；
   - `TellrawJsonBuilder`：0 依赖标准 Minecraft `/tellraw` JSON 序列化器，原生映射 `clickEvent` (`RUN_COMMAND`, `SUGGEST_COMMAND`) 与 `hoverEvent` (`show_text`)，可直接对接 Console、RCON 或 Fabric `ServerPlayer.sendSystemMessage()`。

6. **安全与性能工程底座**：
   - `PlayerRateLimiter`：基于令牌桶（Token Bucket）的玩家级防刷屏与配额管理器，支持突发容量（Burst）、冷却平滑回血与每日使用上限，返回平滑的倒计时警告 `§c[Hoshi] 提问过快！请等待 1.8 秒后再试。`；
   - `QueryCache`：线程安全的 LRU 内存缓存与 TTL 自动失效，高频重复问题 0ms 直接返回，内置完整的命中率与吞吐指标追踪；
   - `PromptSafetyFence`：防范多人聊天中的提示词越权攻击与伪造分隔符，系统提示词全量注入 30 大 Minecraft 地面真实规则 `<canonical_rules>`。

---

## 📂 项目结构

```
mc-agent-core/
├── build.gradle / settings.gradle
├── src/main/java/hoshi/mcagent/
│   ├── context/                         # 玩家与目标方块不可变快照
│   ├── engine/
│   │   ├── LocalGameRules.java          # 30 大核心主题 Ground Truth
│   │   ├── FastPathResolver.java        # Java 确定性快速求解器（30 类主题）
│   │   └── PromptSafetyFence.java       # 提示词清洗与防注入围栏
│   ├── format/
│   │   ├── MinecraftTextFormatter.java  # Markdown 转 § 格式化与坐标识别
│   │   ├── TellrawJsonBuilder.java      # 原生 Vanilla /tellraw JSON 构造器
│   │   └── ChatPaginator.java           # 多页分页器与交互式按钮
│   ├── cache/
│   │   └── QueryCache.java              # 线程安全 LRU + TTL 查询缓存
│   ├── security/
│   │   └── PlayerRateLimiter.java       # 玩家级令牌桶冷却限流器
│   ├── session/                         # v1.5.0 玩家会话与多轮记忆
│   │   ├── PlayerSession.java           # 单玩家滑动窗口与翻页上下文
│   │   └── PlayerSessionManager.java    # 线程安全会话注册与 TTL 管理
│   ├── bom/                             # v1.5.0 生存红石材料与堆叠计算
│   │   ├── ItemStack.java               # 物品数量与 Minecraft 组数折算
│   │   ├── BlueprintBOM.java            # 机器材料清单与 Tellraw 序列化
│   │   └── MaterialCalculator.java      # 确定性 BOM 计算与自然语言匹配
│   ├── command/                         # v1.5.0 游戏内指令与聊天触发器
│   │   ├── CommandResult.java           # 统一指令执行响应对象
│   │   └── CommandRouter.java           # /hoshi 指令分发与公屏前缀捕获
│   ├── async/
│   │   └── AsyncQueryDispatcher.java    # 整合缓存与限流的非阻塞异步分发器
│   └── McAgentCore.java                 # 统一门面 Facade 入口
├── src/test/java/hoshi/mcagent/
│   └── McAgentCoreTest.java             # Java 270 项全绿自动化回归测试
├── mc_agent_core/                       # Python 仿真套件与原型（全模块 100% 对齐）
│   ├── bom.py                           # Python 版材料清单与堆叠计算
│   ├── session.py                       # Python 版玩家会话与记忆
│   ├── command.py                       # Python 版指令路由与触发器
│   └── ...
└── tests/test_mc_agent_core.py          # Python 33 项端到端测试
```

---

## 🧪 自动化测试套件

### Java 参考实现
```bash
javac -encoding UTF-8 -d bin $(find src/main/java src/test/java -name '*.java')
java -cp bin hoshi.mcagent.McAgentCoreTest
# 🎉 All 270/270 Java tests passed successfully!
```

### Python 仿真套件
```bash
PYTHONPATH=. uv run --with pytest pytest tests/ -v
# 33 passed in 0.15s
```
