import json
import os
from typing import Dict, Any, Optional

from app.llm_client import call_llm
from app.knowledge import add_knowledge
from app.synapse.config import SYNAPSE_DIR


SEARCH_CACHE_FILE = os.path.join(SYNAPSE_DIR, "search_cache.json")


def _ensure_dir():
    os.makedirs(SYNAPSE_DIR, exist_ok=True)


def _load_cache() -> list:
    if not os.path.exists(SEARCH_CACHE_FILE):
        return []
    with open(SEARCH_CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_cache(cache: list):
    _ensure_dir()
    with open(SEARCH_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def research_domain(domain: str, query: str = "") -> Dict[str, Any]:
    cache = _load_cache()
    for entry in cache:
        if entry.get("domain") == domain:
            return entry["result"]

    search_query = f"{domain}餐饮 {query}" if query else f"{domain}餐饮经营 最佳实践 方法论"

    prompt = f"""你是一个领域研究专家。请针对以下主题进行深度研究，输出结构化结果。

研究主题: {search_query}

请按以下格式输出:

### Domain Profile: {domain}

**Core Expertise**: [1-2句核心总结]

**Key Frameworks/Methodologies**:
- [框架1]: [简述]
- [框架2]: [简述]
- [框架3]: [简述]

**Essential Vocabulary**:
| Term | Definition | Level |
|------|-----------|-------|

**Common User Needs**:
1. [需求1]
2. [需求2]
3. [需求3]

**Recommended Agent Configuration**:
- Emoji: [建议emoji]
- Title: [建议标题]
- Primary Techniques: [3-4个关键技术]
- Communication Style: [建议沟通风格]

**Anti-Patterns to Avoid**:
- [要避免的做法1]
- [要避免的做法2]

要求：内容必须与餐饮经营相关，实用为主。"""

    try:
        result_text = call_llm(prompt)
    except Exception:
        return {"domain": domain, "error": "研究暂时不可用", "core_expertise": "", "frameworks": []}

    result = {
        "domain": domain,
        "research_text": result_text,
        "query": search_query,
    }

    cache.append({"domain": domain, "result": result})
    if len(cache) > 50:
        cache = cache[-50:]
    _save_cache(cache)

    return result


def research_and_expand_knowledge(domain: str, query: str = "") -> Dict[str, Any]:
    research = research_domain(domain, query)
    research_text = research.get("research_text", "")

    if research_text and len(research_text) > 50:
        try:
            add_knowledge(f"[Synapse域名研究] {domain}", research_text[:2000])
        except Exception:
            pass

    return research


def auto_research_for_decision_type(decision_type: str) -> Optional[Dict[str, Any]]:
    domain_map = {
        "marketing": "营销引流",
        "pricing": "定价策略",
        "menu": "菜单优化",
        "operation": "运营效率",
    }
    domain = domain_map.get(decision_type)
    if not domain:
        return None
    return research_and_expand_knowledge(domain)