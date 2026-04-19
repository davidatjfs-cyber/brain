import json
import os

KNOWLEDGE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "knowledge_base.json"
)

TOOLS = {
    "wiki": True,
    "notebooklm": False,
    "external_api": False,
}

_RESTAURANT_KNOWLEDGE = """
【餐饮经营核心知识】

一、营收提升关键
- 提升客流量：门口引流、社交媒体、团购平台曝光
- 提升客单价：套餐设计、高毛利菜品推荐、限时加购
- 提升翻台率：简化菜单、优化动线、等位区管理、预点餐
- 提升复购率：会员体系、积分兑换、节日营销

二、毛利控制
- 菜品成本率：经典值 30-35%，超过 40% 需警惕
- 高毛利菜品：自制饮品、小菜、加工食品
- 低毛利菜品：爆款引流品，可接受 20-25%
- 损耗控制：食材保鲜、标准化操作、减少浪费

三、差评处理
- 差评黄金处理时间：24小时内回复
- 上菜慢：优化后厨出餐流程、预制半成品
- 味道问题：标准化配方、培训
- 服务问题：明确SOP、模拟演练

四、翻台率优化
- 午市高峰：提前备餐、减少点餐等待时间
- 晚市高峰：等位关怀、预点餐
- 清理动线：收桌与引导并行
- 翻台目标：午市≥1.5次/桌，晚市≥1.2次/桌

五、定价策略
- 锚定效应：高价菜衬托性价比
- 套餐定价：组合优惠感知价值高
- 限时折扣：午市特惠、团购引流
- 心理价位：人均 80-150元 为大众接受区间

六、员工管理
- 流失成本：招新培训成本约为月薪 1.5-2 倍
- 激励机制：提成制优于固定工资
- 培训体系：标准化 + 在岗带教
"""


def _load_knowledge_base():
    if not os.path.exists(KNOWLEDGE_FILE):
        return []
    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_wiki():
    wiki_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "knowledge", "wiki"
    )
    if not os.path.exists(wiki_dir):
        return ""
    chunks = []
    for fname in os.listdir(wiki_dir):
        if fname.endswith(".md"):
            fpath = os.path.join(wiki_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                chunks.append(f.read())
    return "\n\n".join(chunks)


def retrieve_knowledge(query: str = "") -> str:
    parts = []

    parts.append(_RESTAURANT_KNOWLEDGE.strip())

    if TOOLS["wiki"]:
        wiki = _load_wiki()
        if wiki:
            parts.append(f"\n【门店实战经验-Wiki】\n{wiki}")

    kb = _load_knowledge_base()
    if kb:
        kb_text = "\n".join(
            f"- {item.get('title', '')}: {item.get('content', '')[:200]}"
            for item in kb[:5]
        )
        parts.append(f"\n【知识库】\n{kb_text}")

    return "\n\n".join(parts)


def add_knowledge(title: str, content: str):
    os.makedirs(os.path.dirname(KNOWLEDGE_FILE), exist_ok=True)
    kb = _load_knowledge_base()
    kb.append({"title": title, "content": content})
    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)
