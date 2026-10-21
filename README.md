# McAgentCore：现代 Minecraft 智能问答助手核心架构（Java + Python 双栈）

针对 Minecraft 1.20.x ~ 1.21.x（Fabric / NeoForge）模组开发设计的非阻塞、防幻觉、交互式 AI 问答引擎。

---

## 🌟 核心特性（v1.3.0）

1. **严格 50ms Tick 保护（零卡顿）**：
   - 提取主线程不可变空间快照（坐标、视线射线检测、方块光照、生物群系）；
   - 提示词清洗、规则匹配、网络 HTTP I/O 完全移交异步工作线程池；
   - 结果通过 `client.execute()` 或 `server.execute()` 安全切回主线程渲染。

2. **本地确定性快速通路（0ms 响应、0 Token 消耗，全覆盖 23 大核心主题）**：
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
     - 铁傀儡与刷铁机力学：3 村民绑定、20 分钟内睡眠检测、僵尸恐慌态与 16×13×16 生成空间排查。
   - **v1.3.0 新增高频核心力学**：
     - **末影龙复活、折跃门与鞘翅探索**：4 个末影水晶基岩底座复活龙、击败生成 1x1 基岩折跃门通往 1000 格外外岛、末地船鞘翅与纯火药火箭飞行推进动力、潜影盒便携神包；
     - **潮涌核心搭建与水下主宰力学**：海洋之心 + 8 鹦鹉螺壳合成、水体中心 5×5 海晶石框架（16 块单环 32 格，42 块三环满级 96 格）、水下无限呼吸/夜视/速掘与 8 格敌对生物穿透打击；
     - **村庄突袭 (Raid) 机制与村庄英雄**：不祥之瓶进村转化为突袭预兆、简单 3/普通 5/困难 7 波次、卫道士高暴击/女巫/破坏兽、唤魔者掉落不死图腾、获胜赋予村庄英雄全线大幅降价；
     - **猪灵以物易物与猪灵蛮兵权威力学**：穿戴金装防普通猪灵敌对、破坏金矿或打开任何箱子瞬间激怒 16 格猪灵、金锭交易掉落末影珍珠/抗火药水、堡垒遗迹猪灵蛮兵（免疫金装/绝不交易/不可安抚）；
     - **30 级附魔台几何摆放与经验洗炼**：恰好 15 个书架、相隔 1 格空气视线严禁有火把/地毯/雪片阻挡、砂轮洗附魔返还经验与刷新词条种子；
     - **Java 版 vs 基岩版 (Bedrock) 核心机制差异**：Java 攻击冷却 CD/横扫之刃 vs 基岩高速连点、Java 全能副手 vs 基岩受限副手、Java 红石准连接性 (QC) 与 1-tick 活塞吐方块 vs 基岩无 QC。

3. **提示词防注入围栏（Prompt Safety Fence）**：
   - 防范多人聊天中的提示词越权攻击与伪造分隔符；
   - 系统提示词全量注入 23 大 Minecraft 地面真实规则 `<canonical_rules>`，彻底规避模型幻觉与版本漂移。

4. **游戏内富文本与交互动作**：
   - 坐标自动高亮为可点击组件，点击直接在聊天栏填入 `/tp X Y Z`；
   - 附带悬浮提示（HoverEvent）与快捷指令推荐按钮。

5. **Gradle 构建配置**：
   - 提供 Java 21 Toolchain 与 Maven Publish 配置，支持作为 Fabric / NeoForge 子模块或依赖库接入。

---

## 📂 项目结构

```
mc-agent-core/
├── build.gradle / settings.gradle
├── src/main/java/hoshi/mcagent/
│   ├── context/                         # 玩家与目标方块不可变快照
│   ├── engine/
│   │   ├── LocalGameRules.java         # 23 大核心主题 Ground Truth
│   │   ├── FastPathResolver.java        # Java 确定性快速求解器（23 类主题）
│   │   └── PromptSafetyFence.java       # 提示词清洗与防注入围栏
│   ├── format/                          # Minecraft Click/Hover 文本组件
│   ├── async/                           # CompletableFuture 异步工作池
│   └── McAgentCore.java                 # 统一门面入口
├── src/test/java/hoshi/mcagent/
│   └── McAgentCoreTest.java             # Java 140 项全绿自动化测试
├── mc_agent_core/                       # Python 仿真套件与原型
└── tests/test_mc_agent_core.py          # Python 20 项端到端测试
```

---

## 🧪 验证结果

### Java 参考实现
```bash
javac -encoding UTF-8 -d bin $(find src/main/java src/test/java -name '*.java')
java -cp bin hoshi.mcagent.McAgentCoreTest
# 🎉 All 140/140 Java tests passed successfully!
```

### Python 仿真套件
```bash
PYTHONPATH=. uv run --with pytest pytest tests/
# 20 passed in 0.08s
```
