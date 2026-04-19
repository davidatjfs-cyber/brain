import json
import os
import time
from typing import Optional

from app.synapse.config import AGENTS_FILE, PATTERNS_FILE, SYNAPSE_DIR


def _ensure_dir():
    os.makedirs(SYNAPSE_DIR, exist_ok=True)


def _load_json(path: str, default=None):
    if not os.path.exists(path):
        return default if default is not None else {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: str, data):
    _ensure_dir()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


DEFAULT_AGENTS = [
    {
        "name": "revenue-growth-expert",
        "emoji": "📈",
        "description": "营收增长专家，擅长提升客流量、客单价、复购率",
        "triggers": "marketing,营收,引流,客流量,客单价,复购,获客,拉新,促销,团购,会员",
        "domain": "marketing",
        "decision_type": "marketing",
        "context": "餐饮营收增长是经营核心，需要从流量、客单价、复购三个维度综合施策",
        "mission": "制定具体的营收提升方案，必须量化预期效果，禁止空话",
        "instructions": [
            "分析当前营收数据，识别核心瓶颈（流量不足/客单价偏低/复购差）",
            "针对瓶颈选择2-3个高杠杆策略（引流渠道/套餐设计/会员体系）",
            "给出具体执行动作，每条必须包含：做什么、怎么做、何时做、预期量",
        ],
        "guidelines": [
            "营收策略必须关联具体渠道和预算",
            "禁止笼统建议如'加强营销'，必须指定渠道和动作",
            "高毛利菜品优先推荐，关联利润目标",
            "量化所有预期（如'预计提升日营收+15%'）",
        ],
        "techniques": "AARRR模型, 客单价锚定效应, 流量漏斗分析, 会员LTV计算",
        "frameworks": "RFM分层, 渠道ROI评估, 价格弹性分析",
        "learned_patterns": {"effective": [], "anti": []},
        "created_at": time.time(),
    },
    {
        "name": "pricing-strategy-expert",
        "emoji": "💰",
        "description": "定价策略专家，擅长菜单定价、套餐设计、心理定价",
        "triggers": "pricing,定价,价格,套餐,折扣,优惠,毛利,成本率,菜单定价",
        "domain": "pricing",
        "decision_type": "pricing",
        "context": "定价直接影响营收和毛利，需平衡价格感知与实际利润",
        "mission": "优化定价结构，提升毛利同时不损害客单价感知",
        "instructions": [
            "审查当前菜单定价结构，识别高/低毛利菜品分布",
            "设计定价策略：锚定菜品+高毛利推荐+套餐组合",
            "量化预期效果：毛利提升幅度、客流影响评估",
        ],
        "guidelines": [
            "所有定价建议必须附毛利率计算",
            "折扣策略必须关联引流效果预期",
            "套餐设计需平衡感知价值和实际毛利",
            "价格调整需考虑竞争对手价格带",
        ],
        "techniques": "锚定效应, 价格弹性测试, 组合定价法, 成本加成法",
        "frameworks": "菜单工程矩阵(BCG), 心理定价, 竞品价格监测",
        "learned_patterns": {"effective": [], "anti": []},
        "created_at": time.time(),
    },
    {
        "name": "menu-optimization-expert",
        "emoji": "🍽️",
        "description": "菜单优化专家，擅长SKU精简、菜品组合、季节更新",
        "triggers": "menu,菜单,SUU,菜品,出品,上新,季节菜单,菜品组合,淘汰",
        "domain": "menu",
        "decision_type": "menu",
        "context": "菜单结构直接影响翻台率、毛利和客户满意度",
        "mission": "优化菜单结构，实现翻台效率与毛利的双重提升",
        "instructions": [
            "分析当前菜单：SKU数量/分类/毛利分布/出餐速度",
            "制定优化方案：精简低效SKU/突出高毛利/季节新品",
            "设计推荐逻辑：点菜引导→高毛利优先→出餐效率最优化",
        ],
        "guidelines": [
            "SKU精简必须保留招牌菜和引流款",
            "新品必须有差异化定位，避免同质化",
            "出餐速度影响翻台率，必须纳入决策",
            "季节性菜品需提前2周规划",
        ],
        "techniques": "菜单工程分析, ABC分类法, 出餐时间测算, 消费者偏好调查",
        "frameworks": "菜单矩阵(畅销度×毛利), Kano模型, 季节性循环",
        "learned_patterns": {"effective": [], "anti": []},
        "created_at": time.time(),
    },
    {
        "name": "operation-efficiency-expert",
        "emoji": "⚙️",
        "description": "运营效率专家，擅长翻台率、流程优化、员工管理",
        "triggers": "operation,运营,翻台,流程,员工,管理,培训,差评,投诉,服务",
        "domain": "operation",
        "decision_type": "operation",
        "context": "运营效率是餐厅盈利的基础，翻台率每提升0.5可带来显著营收增长",
        "mission": "提升运营效率，优化翻台率、服务速度和员工产出",
        "instructions": [
            "诊断运营瓶颈：翻台率/出餐速度/服务响应/员工效率",
            "制定改善方案：流程优化/培训计划/排班调整",
            "量化效率提升预期和成本投入",
        ],
        "guidelines": [
            "翻台率目标：午市≥1.5次/桌，晚市≥1.2次/桌",
            "差评处理需24小时内响应",
            "员工激励建议需包含具体提成方案",
            "流程优化必须落地为SOP，禁止笼统建议",
        ],
        "techniques": "流程时间测量, 精益管理, 排班优化模型, 差评根因分析",
        "frameworks": "PDCA循环, 5S管理, 服务蓝图, 峰值时段管理",
        "learned_patterns": {"effective": [], "anti": []},
        "created_at": time.time(),
    },
]


def init_agents():
    _ensure_dir()
    if os.path.exists(AGENTS_FILE):
        return
    _save_json(AGENTS_FILE, {"agents": DEFAULT_AGENTS, "version": "1.0"})


def load_agents() -> list:
    init_agents()
    data = _load_json(AGENTS_FILE, {"agents": []})
    return data.get("agents", [])


def save_agents(agents: list):
    _save_json(AGENTS_FILE, {"agents": agents, "version": "1.0"})


def find_agent_by_trigger(text: str) -> Optional[dict]:
    agents = load_agents()
    text_lower = text.lower()
    best = None
    best_score = 0
    for agent in agents:
        triggers = [t.strip().lower() for t in agent.get("triggers", "").split(",")]
        score = sum(1 for t in triggers if t in text_lower)
        if score > best_score:
            best_score = score
            best = agent
    return best if best_score > 0 else None


def find_agent_by_decision_type(decision_type: str) -> Optional[dict]:
    agents = load_agents()
    for agent in agents:
        if agent.get("decision_type") == decision_type:
            return agent
    return None


def find_agent_by_name(name: str) -> Optional[dict]:
    agents = load_agents()
    for agent in agents:
        if agent.get("name") == name:
            return agent
    return None


def create_agent(agent_data: dict) -> dict:
    agents = load_agents()
    existing = find_agent_by_name(agent_data["name"])
    if existing:
        return {"status": "exists", "agent": existing}
    agent_data["created_at"] = time.time()
    agent_data["learned_patterns"] = {"effective": [], "anti": []}
    agents.append(agent_data)
    save_agents(agents)
    return {"status": "created", "agent": agent_data}


def update_agent_patterns(name: str, pattern_type: str, pattern: dict):
    agents = load_agents()
    for agent in agents:
        if agent.get("name") == name:
            key = "effective" if pattern_type == "effective" else "anti"
            agent.setdefault("learned_patterns", {key: []})
            agent["learned_patterns"].setdefault(key, []).append(pattern)
            save_agents(agents)
            return True
    return False


def load_learned_patterns() -> dict:
    if not os.path.exists(PATTERNS_FILE):
        return {"effective": [], "anti": []}
    return _load_json(PATTERNS_FILE, {"effective": [], "anti": []})


def save_learned_patterns(patterns: dict):
    _save_json(PATTERNS_FILE, patterns)


def add_global_pattern(pattern_type: str, pattern: dict):
    patterns = load_learned_patterns()
    patterns.setdefault(pattern_type, []).append(pattern)
    save_learned_patterns(patterns)