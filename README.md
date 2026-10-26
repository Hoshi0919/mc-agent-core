# McAgentCore：现代 Minecraft 智能问答助手核心架构（Java + Python 双栈）

针对 Minecraft 1.20.x ~ 1.21.x（Fabric / NeoForge / Paper）模组与服务端开发设计的非阻塞、防幻觉、全维游戏感知与交互式 AI 问答引擎。

---

## 🌟 核心特性（v2.1.0 里程碑：局部机器拓扑分析与因果图流式推断）

1. **Create 机械动力网络拓扑图论分析与齿轮卡死诊断 (Create Kinetic Network & Jamming Analyzer)**：
   - **`KineticNetworkAnalyzer`**：
     - **轴传动与啮合传递矩阵**：同轴直线刚性传递转向与转速完全恒定 ($\omega_2 = \omega_1$)；正齿轮外切啮合严格反向 ($\omega_2 = -\omega_1$)；大小齿轮 2:1 / 1:2 啮合转速加倍/减半且转向反转；
     - **动力卡死冲突检测 (Kinetic Jamming & Ratio Mismatch Lock)**：当机械传动分支在闭环回路中汇合时，沿环路累乘传动矩阵。若累乘转向为 -1（奇数次啮合回环造成齿轮在同一接触面企图同时反向转动）或转速比矛盾（如 $2.0x 
eq 1.0x$ 自相矛盾加速比），在 0ms 瞬间锁定冲突点坐标并报警；
     - **`/hoshi cluster kinetics`**：诊断当前准星局部多方块动力传动网络，精确给出卡死齿轮位置与换向齿轮箱 (Gearbox) 配平建议！

2. **生电漏斗物流有向图、闭环死锁与分类器串线击穿分析器 (Hopper Directed Graph & Item Sorter Bleed Analyzer)**：
   - **`HopperNetworkAnalyzer`**：
     - **有向环路死锁检测 (Hopper Cycle Deadlock)**：基于 DFS 递归栈检测漏斗互指闭环回路（$A 	o B 	o A$ 或复杂循环），精准定位卡住物料的死循环；
     - **背压停滞全线回溯 (Backpressure Stall)**：下游容器满仓或漏斗被意外红石信号锁定（`enabled=false`）时，逆向追溯标记整条受阻停滞流水线；
     - **分类器信号击穿与炸箱预警 (Item Sorter Overflow Bleed)**：精准读取过滤漏斗容纳物品数。当物品堆积达到 46 个时，比较器信号跳升至 3 级击穿相邻 1 格切片红石线导致隔壁箱子漏空！严格指导 41+1+1+1+1 防串线布局；
     - **`/hoshi cluster hopper`**：一键生成漏斗物流流向与死锁诊断报告！

3. **1.21 自动合成器流水线闭环诊断器 (Crafter Pipeline & Slot Masking Analyzer)**：
   - **`CrafterPipelineAnalyzer`**：
     - **槽位遮罩缺口诊断 (Slot Masking Deficit)**：针对非 9 格满配方（如胸甲需 8 格、镐需 5 格、剑需 3 格），检测是否点击禁用多余槽位，严防漏斗原料溢入破坏配方；
     - **多原料混投抢占死锁 (Slot Saturation Deadlock)**：单漏斗给多原料配方（如木棍+铁锭合成剑）无序供料时，单一原料抢占全部空槽导致死锁；指导采用投掷器脉冲定量配平；
     - **比较器满格脉冲闭环**：指导比较器信号与 1-tick 脉冲发生器的时钟同步；
     - **`/hoshi cluster crafter`**：诊断当前自动合成器配置状态！

---

## 🌟 核心特性（v2.0.0 里程碑）

1. **铁砧附魔合并二叉树优化器与惩罚规避算法 (Anvil Enchantment Tree Optimizer & Prior Work Penalty Avoidance)**：
   - **`AnvilOptimizer`**：
     - **累积惩罚指数爆炸公式**：每次铁砧操作记录工作次数 $N$，附加消耗惩罚为 $2^N - 1$ 级（0, 1, 3, 7, 15, 31, 63...）；
     - **规避【过于昂贵！(Too Expensive!)】**：生存模式单步铁砧消耗 $\ge 40$ 级即被彻底拒绝合成！线性依次敲 6~8 本书到第 5 步即突破 40 级导致装备报废；
     - **二叉树对数级合并**：通过将多本书两两构建平衡二叉合并树（树高仅 $\lceil \log_2(N) 
ceil \le 3$），最后一次性将复合书拍上装备，最终装备惩罚仅为 3~4 次（7~15 级），全程单步消耗控制在 10~25 级以内，彻底规避 39 级上限！
     - **附魔互斥与装备兼容性矩阵**：内置 37+ 种核心附魔属性、倍率与互斥对校验（精准采集 vs 时运、无限 vs 经验修补、四种保护互斥、三叉戟激流 vs 忠诚/引雷、1.21 重锤专属致密/破甲/风爆）；
   - **`/hoshi anvil <装备名> [附魔1:等级] [附魔2:等级]...`**：生成步骤清晰的左槽/右槽锻造执行工序与等级消耗报告！

2. **现代科技模组 Create 机械动力学应力与转速网络平衡引擎 (Create Stress Capacity & Gear Kinetics Analyzer)**：
   - **`CreateKineticsAnalyzer`**：
     - **转速应力守恒公式**：机器应力消耗遵循 $	ext{Impact}(SU) = \kappa 	imes 	ext{RPM}$。转速提升 2 倍，消耗同步翻倍；
     - **机器冲击系数 $\kappa$ 注册库**：粉碎轮/辊压机/机械臂 $\kappa=8$，搅拌机/动力锯/流体泵/磨盘 $\kappa=4$，传动带 $\kappa=1$；
     - **动力源阶梯**：小型水轮 (256 SU @ 8 RPM)、大型水轮 (512 SU @ 4 RPM)、风车轴承 (8~128 帆布，满级 8,192 SU @ 16 RPM)；
     - **工业级蒸汽机矩阵**：锅炉等级 1~18 级（由加热等级：营火/烈焰人/烈焰饼超频 + 机械泵注水决定），9 级被动满产 147,456 SU，18 级超频最大释放 294,912 SU @ 64 RPM；
     - **过载断裂诊断 (Overstressed Diagnostics)**：总消耗超过总容量时转速瞬间归零停摆；精准给出断裂缺口赤字、全线临界安全同步转速上限与齿轮比调谐/锅炉扩容方案；
   - **`/hoshi create stress <动力源> [规模] [机器配置]`**：为科技自动化工业基地提供即时动力学平衡演算！

3. **生电传送门常载网与 8:1 坐标对齐诊断器 (Portal Permaloader & Chunk Loading Grid)**：
   - **`PortalChunkLoaderAnalyzer`**：
     - **15.0 秒强加载时钟律**：实体穿越下界传送门产生持续 15 秒 (300 ticks) 的 Ticket 30 强加载票；精确校验投掷穿梭周期（安全黄金周期 8~12 秒），诊断超时引起的常载区块卸载停摆与死锁；
     - **三阶辐射圈判定**：3x3 实体完全处理区 (Entity Ticking)、5x5 方块红石区 (Block Ticking)、7x7 懒惰区 (Lazy Chunks)；
     - **8:1 坐标对齐与防串门 (Portal Bleed Diagnostics)**：主世界 $(X, Z)$ 对应下界 $(\lfloor X/8 
floor, \lfloor Z/8 
floor)$；精确解算欧氏空间漂移距离 $\Delta$，告警超过 16 格的安全容差门，严防单向串门撕裂并输出下界门精确迁址坐标！
   - **`/hoshi chunkloader permaloader [周期秒数]`** 与 **`/hoshi chunkloader portal <主界X> <主界Z> <下界X> <下界Z>`**：一键生成生电常载网络诊断报告！

4. **敌对生物生成动力学、清除球与刷怪塔诊断引擎 (Mob Spawning Dynamics & Despawn Spheres Analyzer)**

1. **敌对生物生成动力学、清除球与刷怪塔诊断引擎 (Mob Spawning Dynamics & Despawn Spheres Analyzer)**：
   - **`MobFarmDynamics`**：
     - **四大空间几何清除球判定**（以玩家挂机点为中心）：
       - `0 ~ 24 格`：绝对禁刷盲区 (No-Spawn Sphere)，除刷怪笼外禁止自然生成任何生物；
       - `24 ~ 32 格`：黄金高频活动圈 (Active Golden Sphere)，生物生成后立即自由寻路/活动，不触发随机消失，产出最高；
       - `33 ~ 128 格`：随机清除区 (Random Despawn Sphere)，每 tick 1/800 几率尝试清除（约 28s 半衰期），需极速冲刷或摔落；
       - `> 128 格`：瞬间蒸发视界 (Instant Despawn Horizon)，下一 tick 直接被垃圾回收强制清除！若挂机点距刷怪平台超过 128 格产出彻底为零；
     - **单人 70 生物Cap与洞穴压制诊断**：挂机点周边 128 格球体内未点亮矿洞会迅速占满 70 只怪物上限导致平台停摆，精准提示高空挂机或矿洞照亮；
     - **基岩低 Y 轴抽样优势**：计算地表包围盒与高度抽样率，深层基岩 ($Y=-58$) 挖空平台生成效率达常规地表的 3~4 倍；
     - **刷怪笼激活与光照压制 (`evaluateSpawner`)**：16 格激活半径检测、9×9×3 盒体生物上限检查与 1.18+ 光照 $\ge 11$ 彻底熄灭压制评估；
   - **`/hoshi mobfarm <挂机Y> <平台Y> [洞穴点亮]`** 与 **`/hoshi spawner <距离> <光照>`**：游戏内一键生成生电级刷怪动力学诊断报告！

2. **村民铁傀儡农场恐慌时序与工作站死锁诊断器 (Villager AI Dynamics & Iron Farm Analyzer)**：
   - **`VillagerDynamics`**：
     - **刷铁机运行诊断 (`diagnoseIronFarm`)**：
       - 硬性最低 3 名有效村民判定；
       - **致命永恒失眠陷阱 (Permanent Panic Insomnia)**：村民 24 小时目视僵尸导致持续逃跑恐慌而无法入睡，超过 20 分钟后因失眠彻底停产！诊断报告明确提示采用活塞遮挡板或水流颠簸进行周期性视线遮断 (LOS Break)，让村民每隔数秒偷睡 1 tick；
       - 20 分钟内入睡前置检查；
     - **村民繁殖机诊断 (`diagnoseBreeder`)**：
       - 床头上方至少 2 格充裕空气净空检测（小村民跳跃寻路硬性条件）；
       - 食物意愿储量检测（3 面包或 12 胡萝卜/马铃薯）；
       - 村庄未绑定空闲床位核验；
     - **村民交易大厅诊断 (`diagnoseTrading`)**：
       - 交易经验 $XP > 0$ 职业永久锁定检测；
       - 工作台物理脚部可达性与每日日间 2 次补货时钟验证；
   - **`/hoshi villager <iron/breeder/trading>`**：直击生存与交易大厅常见疑难杂症！

1. **多方块蓝图对齐校验与装配引擎 (Multiblock Blueprint Validator & Assembly Guide)**：
   - **`MultiblockValidator`**：支持现代 Minecraft 原版与生电自动化 6 大核心多方块结构定义：
     - **潮涌核心满级三环 (Conduit 3-Ring Frame)**：5×5×5 几何空间、42 块海晶石系方块环形闭合、中心 3×3×3 水体要求；激活 96 格最大有效半径与每 2 秒 4 点敌对生物电击伤害；
     - **四级信标金字塔 (Tier 4 Beacon Pyramid)**：9×9 底座 4 层金字塔 (164 矿物块)，天顶 320 格直视无阻挡检测；激活急迫 II (Haste II) 与生命恢复，实现秒挖深板岩；
     - **下界传送门极值架构 (Nether Portal)**：最小 4×5 (内框 2×3，10~14 黑曜石) 至最大 23×23 (内框 21×21)；实体穿过触发 15 秒目标区块强加载 (Chunk Loader)；
     - **末地传送门悬空环 (End Portal Ring)**：12 个框架内倾朝向 (facing) 判定与末影之眼填充，通往末影龙中心岛黑曜石平台；
     - **凋灵召唤构架 (Wither Assembly)**：4 灵魂沙/灵魂土 T 型骨架 + 3 凋灵骷髅头颅，最后放置判定与无敌充能自爆时钟；
     - **铁傀儡装配构架 (Iron Golem Assembly)**：4 铁块 T 型摆放 + 雕刻南瓜，2×3×2 实体空间排他校验。
   - **`validateInventory(bp, inv)` 背包材料智能核验**：精准比对玩家现有背包材料，计算完成度百分比，标出具体缺失材料清单（支持海晶石系与矿物块系智能别名混搭！）；
   - **`/hoshi multiblock <方案名>`**：即时调阅 3D 几何规格、材料满足度与激活装配指引。

2. **工业流水线与物流吞吐瓶颈分析引擎 (Pipeline Throughput & Bottleneck Analyzer)**：
   - **`PipelineThroughputAnalyzer`**：
     - 精准量化物流传输与机器消耗常数：单漏斗 2.5 items/s (8 ticks/item)、双漏斗 5.0 items/s、漏斗矿车隔空穿透 20.0 items/s (1 tick/item)、水流浮冰高速通道 32.0 items/s、普通熔炉 0.1 items/s (10.0s/物)、高炉/烟熏炉 0.2 items/s (5.0s/物)；
     - **`analyzeSmeltingArray(count, machine, transport)`**：输入阵列规模与物流方式，精确解算总需求通量与管道极限；若存在赤字（如单漏斗供料 16 台高炉时赤字 21.9%），直接告警主干供料瓶颈并计算最大满载承载台数（12 台），自动给出对称并联或矿车分流优化方案；
   - **`/hoshi pipeline <设备类型> [数量] [物流]`**：游戏内一键生成工业级流水线吞吐瓶颈诊断报告！

1. **红石与物流拓扑感知引擎 (Redstone & Logistics Topology Perception)**：
   - **`TargetBlock.evaluateLogisticsOrRedstone()`**：
     - **漏斗 (Hopper)**：精准诊断红石强充能锁定 (`enabled=false`)，告警停止吸取/漏出物品并指出排查点；解析朝向（下行直通 vs 侧向推入）；给出 2.5 组/秒速率与 41+1+1+1+1 防串线及 18+1+1+1+1 紧凑过滤布局；
     - **红石比较器 (Comparator)**：识别减法模式 (`subtract`, 前置火把点亮) 与比较模式 (`compare`)，即时输出差分代数公式与容器满度强度计算；
     - **红石中继器 (Repeater)**：解析 1~4 刻延迟 (0.1~0.4s) 与侧向锁存锁定状态 (基岩锁存器)；
     - **侦测器 (Observer)**：感知侦测面朝向与 1-tick 脉冲发射状态，提示面迎面 2-tick 超高频时钟与粘性活塞 1-tick 吐方块机制；
     - **自动合成器 (Crafter 1.21)**：感应上升沿脉冲合成与比较器槽位读取 (0~9)；
     - **阳光探测器 (Daylight Detector)**：识别日光正常 vs 月光夜间反转模式；
     - **幽匿感测体 (Sculk Sensor)**：区分标准型与校准型单一频率 (1~15) 过滤机制；
     - **水力气泡柱基座 (Soul Sand / Magma)**：区分上升极速喷射 (11m/s) 与下沉涡流，特别提示海带一键转化水源关键前置；
     - **投掷器 vs 发射器 (Dropper vs Dispenser)**：明确掉落物实体形态与专属执行动作的区别，防止管道搭建失误。
   - **`/hoshi inspect` 诊断集成**：准星注视红石物流组件时自动输出 `⚡ 红石/物流` 专属诊断与调优建议；
   - **准星红石即时提问**：当玩家看着眼前红石问“为什么不漏/为什么不动/怎么算”时，直接触发毫秒级拓扑诊断！

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
     - `/hoshi multiblock <方案>`：调阅多方块蓝图与背包材料核验（潮涌、信标、地狱门、末地门、凋灵、铁傀儡）；
     - `/hoshi pipeline <设备> [数量] [物流]`：诊断工业流水线供料瓶颈（普通熔炉、高炉、烟熏炉与漏斗/矿车/水流）；
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
     - **v1.7.0 新增核心力学主题**：
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
│   ├── crafting/                        # v1.7.0 配方与背包合成充盈度计算
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
│   └── McAgentCoreTest.java             # Java 579 项全绿自动化回归测试
├── mc_agent_core/                       # Python 仿真套件与原型（全模块 100% 对齐）
│   ├── crafting.py                      # Python 版配方与合成充盈度
│   ├── context.py                       # Python 版全维上下文快照
│   └── ...
└── tests/test_mc_agent_core.py          # Python 59 项端到端测试
```

---

## 🧪 自动化测试套件

### Java 参考实现
```bash
javac -encoding UTF-8 -d bin $(find src/main/java src/test/java -name '*.java')
java -cp bin hoshi.mcagent.McAgentCoreTest
# 🎉 All 579/579 Java tests passed successfully!
```

### Python 仿真套件
```bash
PYTHONPATH=. uv run --with pytest pytest tests/ -v
# 59 passed in 0.30s
```
