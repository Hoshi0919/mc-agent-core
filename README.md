# McAgentCore：现代 Minecraft 智能问答助手核心架构（Java + Python 双栈）

针对 Minecraft 1.20.x ~ 1.21.x（Fabric / NeoForge / Paper）模组与服务端开发设计的非阻塞、防幻觉、全维游戏感知与交互式 AI 问答引擎。

---

## 🌟 核心特性（v1.6.0）

1. **全维游戏上下文感知系统 (Fine-Grained Context Awareness)**：
   - **`InventorySnapshot` & `ItemInstance`**：
     - 细粒度感知玩家主手、副手、四件套防具（头盔、胸甲、护腿、靴子）以及 36 格背包（快捷栏 0~8 格与主背包 9~35 格）；
     - 智能查询接口：`countItem(id)` 全槽位统计、`findHotbarSlot(id)` 快捷栏定位、`findHotbarTool(type, tier)` 挖掘工具搜寻、`totalArmorPoints()` 护甲点数精确估算、`isWearingGoldArmor()` 穿戴黄金护甲判定；
   - **`TargetBlock` 挖掘与掉落安全性评估**：
     - 解析准星注视方块的所需工具类型（镐、斧、铲、锄）与采掘等级（0=空手，1=木/金，2=石，3=铁，4=钻/合金）；
     - 实时比对玩家手持工具与背包快捷栏，在工具等级不足时输出**严重防损警告**（例如手持铁镐挖远古残骸或黑曜石将无法产生掉落），并明确提示按键切换至快捷栏第几格的可用工具；
   - **`TargetEntity` 准星生物多维感知与交互指引**：
     - 识别准星对准的实体类型（僵尸村民、猪灵、猪灵蛮兵、铁傀儡、犰狳、循声守卫等）；
     - 结合玩家当前背包物品输出针对性战术方案（例如注视僵尸村民时检查是否持有金苹果与虚弱药水；注视猪灵时检查是否穿金防仇恨；注视犰狳时提示使用刷子刷取狼铠鳞甲；注视铁傀儡提示手持铁锭右键修复裂纹与生命）。

2. **背包材料合成充盈度计算器 (`CraftingReadinessChecker`)**：
   - 内置 17 种现代 Minecraft 生存与红石核心配方（漏斗、活塞、粘性活塞、侦测器、红石比较器、红石中继器、附魔台、信标、酿造台、潮涌核心、铁砧、盾牌、弓、弩、避雷针、TNT、发射器）；
   - 自动扫描背包原料，精确输出当前原料最多可连续合成数量或缺失材料清单（例如 `缺少 2 个铁锭 (当前 3/5)`），并给出合成避坑专家提示；
   - 支持自然语言模糊提问（例如 `我包里的材料够做漏斗吗？`）与游戏内指令 `/hoshi craft <物品>`。

3. **全功能游戏内指令路由与公屏触发器 (`CommandRouter`)**：
   - 统一分发 `/hoshi` 与 `/ai` 斜杠指令：
     - `/hoshi inspect`：全维扫描当前准星注视方块与实体，评估挖掘工具与掉落安全性；
     - `/hoshi craft <物品>`：评估当前背包原料是否满足合成条件及缺失数量；
     - `/hoshi ask <问题>`：交互式咨询游戏机制或红石攻略；
     - `/hoshi page <页码>`：无缝翻阅长篇蓝图或攻略下一页；
     - `/hoshi bom <方案> [数量]`：快速生成红石构件材料清单与生存堆叠折算；
     - `/hoshi nether [x y z]`：转换下界/主界传送门对应坐标（省略坐标时自动调用玩家当前快照）；
     - `/hoshi stats`：实时查看服务端缓存命中率、吞吐量与活跃会话数；
     - `/hoshi clear`：清空玩家个人会话记忆与翻页缓存；
     - `/hoshi help`：交互式指令帮助面板（包含可点击的建议指令）。
   - 公屏聊天自动唤醒触发：支持 `!问题`、`?问题`、`@ai 问题`、`@hoshi 问题` 原生提取与路由。

4. **玩家多轮会话记忆与生命周期管理 (`PlayerSessionManager` & `PlayerSession`)**：
   - 为每位玩家维护独立的有界滑动窗口对话记忆（默认 5 轮，杜绝多人服务器内存膨胀）；
   - 维护玩家活跃的 `PagedResult` 上下文，彻底打通 `/tellraw` 点击交互与 `/hoshi page <n>` 翻页链路；
   - 追踪活跃主题与时间戳，支持 TTL 自动过期与无锁清理。

5. **生存红石材料清单 (BOM) 与堆叠折算器 (`MaterialCalculator` & `BlueprintBOM`)**：
   - 覆盖 6 大经典生存与红石自动化蓝图（甘蔗机、南瓜机、1~4 级信标金字塔、安全刷石机、22 项物品分类机、Etho 漏斗时钟）；
   - 自动化 Minecraft 堆叠换算：将大额方块数量智能折算为“组 + 个”（例如 `164 矿物块 = 2 组 + 36 个`，原料折算 `1476 铁锭 = 23 组 + 4 个`）；
   - 一键生成 Vanilla Tellraw JSON，点击构件即可在聊天框填入对应的 `/give @s <itemId> <count>` 获取指令。

6. **本地确定性快速通路（0ms 响应、0 Token 消耗，全覆盖 34 大核心主题）**：
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
     - 村民繁殖与有效床位动力学 (VILLAGER_BREEDING)：床头正上方必须有至少 2 格完整透明/空气高度（小村民跳床寻路判定）、3 面包/12 胡萝卜意愿度消耗、幼年 20 分钟（24000 ticks）成年；
     - 全自动村民农田机制 (VILLAGER_CROP_FARM)：棕袍农民 AI、入场前投喂 8 组单一作物背包防杂物堵死、隔墙栅栏投喂漏斗拦截法与漏斗矿车穿透吸物；
     - 高能自动化燃料与熔炼动力学 (SMELTING_FUEL_EFFICIENCY)：200 ticks (10.0 秒) 标准熔炼时钟、岩浆桶 (100 个返还铁桶)、煤炭块 (80 个)、干海带块 (20 个可再生首选)、熔炉阵列双漏斗推流；
     - **v1.6.0 新增核心力学主题**：
       - **僵尸村民治愈机制与永久交易折扣 (ZOMBIE_VILLAGER_CURE)**：喷溅虚弱药水 + 普通金苹果投喂，3~5 分钟 (3600~6000 ticks) 转化，周围铁栏杆与床加速，治愈后永久超低折扣；
       - **铁傀儡修复维护与村庄防卫动力学 (IRON_GOLEM_REPAIR)**：100 点生命值（50 颗心）与 4 阶段肉眼可见裂纹，手持铁锭右键每个恢复 25 点生命并消除裂纹，高额反击伤害与声望戒律；
       - **犰狳刷鳞与狼铠防御系统 (ARMADILLO_WOLF_ARMOR)**：热带草原与恶地生态、手持刷子 (Brush) 无损刷取犰狳鳞甲、6 枚鳞甲合成与染色狼铠、吸收 100% 针对驯服狼的直接伤害与原位修复；
       - **试炼密室刷怪笼与旋风人攻防动力学 (TRIAL_SPAWNER_BREEZE)**：动态弹性波次刷怪、旋风人强风气流 100% 反弹所有远程投射物、盾牌弹反风弹与近战克制。

7. **交互式 Chat 分页器与 Tellraw JSON 序列化器**：
   - `ChatPaginator`：针对 Minecraft 聊天窗口高度限制，自动将多行蓝图与攻略按页拆分，动态追加交互式翻页控制条 `§8[ §b◀ 上一页 §8] §7[ §e第 1/3 页 §7] §8[ §b下一页 ▶ §8]`；
   - `TellrawJsonBuilder`：0 依赖标准 Minecraft `/tellraw` JSON 序列化器，原生映射 `clickEvent` (`RUN_COMMAND`, `SUGGEST_COMMAND`) 与 `hoverEvent` (`show_text`)，可直接对接 Console、RCON 或 Fabric `ServerPlayer.sendSystemMessage()`。

8. **安全与性能工程底座**：
   - `PlayerRateLimiter`：基于令牌桶（Token Bucket）的玩家级防刷屏与配额管理器，支持突发容量（Burst）、冷却平滑回血与每日使用上限，返回平滑的倒计时警告 `§c[Hoshi] 提问过快！请等待 1.8 秒后再试。`；
   - `QueryCache`：线程安全的 LRU 内存缓存与 TTL 自动失效，高频重复问题 0ms 直接返回，内置完整的命中率与吞吐指标追踪；
   - `PromptSafetyFence`：防范多人聊天中的提示词越权攻击与伪造分隔符，系统提示词全量注入 34 大 Minecraft 地面真实规则 `<canonical_rules>`。

---

## 📂 项目结构

```
mc-agent-core/
├── build.gradle / settings.gradle
├── src/main/java/hoshi/mcagent/
│   ├── context/                         # 玩家、背包、注视方块与实体不可变快照
│   │   ├── ItemInstance.java            # 物品堆叠、耐久与采掘工具层级
│   │   ├── InventorySnapshot.java       # 背包/快捷栏/护甲点数与工具检索
│   │   ├── TargetBlock.java             # 准星方块、硬度与掉落兼容性评估
│   │   ├── TargetEntity.java            # 准星实体感知与上下文指引
│   │   └── ContextSnapshot.java         # 全维上下文不可变快照与 Builder
│   ├── crafting/                        # v1.6.0 配方与背包合成充盈度计算
│   │   ├── CraftingRecipe.java          # 配方标准数据结构
│   │   └── CraftingReadinessChecker.java # 背包原料扫描与充盈度计算
│   ├── engine/
│   │   ├── LocalGameRules.java          # 34 大核心主题 Ground Truth
│   │   ├── FastPathResolver.java        # Java 确定性快速求解器（34 类主题）
│   │   └── PromptSafetyFence.java       # 提示词清洗与防注入围栏
│   ├── format/
│   │   ├── MinecraftTextFormatter.java  # Markdown 转 § 格式化与坐标识别
│   │   ├── TellrawJsonBuilder.java      # 原生 Vanilla /tellraw JSON 构造器
│   │   └── ChatPaginator.java           # 多页分页器与交互式按钮
│   ├── cache/
│   │   └── QueryCache.java              # 线程安全 LRU + TTL 查询缓存
│   ├── security/
│   │   └── PlayerRateLimiter.java       # 玩家级令牌桶冷却限流器
│   ├── session/                         # 玩家会话与多轮记忆
│   │   ├── PlayerSession.java           # 单玩家滑动窗口与翻页上下文
│   │   └── PlayerSessionManager.java    # 线程安全会话注册与 TTL 管理
│   ├── bom/                             # 生存红石材料与堆叠计算
│   │   ├── ItemStack.java               # 物品数量与 Minecraft 组数折算
│   │   ├── BlueprintBOM.java            # 机器材料清单与 Tellraw 序列化
│   │   └── MaterialCalculator.java      # 确定性 BOM 计算与自然语言匹配
│   ├── command/                         # 游戏内指令与聊天触发器
│   │   ├── CommandResult.java           # 统一指令执行响应对象
│   │   └── CommandRouter.java           # /hoshi 指令分发与公屏前缀捕获
│   ├── async/
│   │   └── AsyncQueryDispatcher.java    # 整合缓存与限流的非阻塞异步分发器
│   └── McAgentCore.java                 # 统一门面 Facade 入口
├── src/test/java/hoshi/mcagent/
│   └── McAgentCoreTest.java             # Java 328 项全绿自动化回归测试
├── mc_agent_core/                       # Python 仿真套件与原型（全模块 100% 对齐）
│   ├── crafting.py                      # Python 版配方与合成充盈度
│   ├── context.py                       # Python 版全维上下文快照
│   └── ...
└── tests/test_mc_agent_core.py          # Python 39 项端到端测试
```

---

## 🧪 自动化测试套件

### Java 参考实现
```bash
javac -encoding UTF-8 -d bin $(find src/main/java src/test/java -name '*.java')
java -cp bin hoshi.mcagent.McAgentCoreTest
# 🎉 All 328/328 Java tests passed successfully!
```

### Python 仿真套件
```bash
PYTHONPATH=. uv run --with pytest pytest tests/ -v
# 39 passed in 0.18s
```
