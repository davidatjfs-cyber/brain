TEST_CASES = [
    {
        "name": "营收大幅下降",
        "input": {
            "store_id": "hongchao_001",
            "date": "2026-04-01",
            "metrics": {
                "daily_revenue": 12000,
                "target_revenue": 30000,
                "dine_traffic": 65,
                "avg_ticket": 90,
                "delivery_ratio": 0.4,
            },
            "menu": [
                {"name": "煲仔饭", "sales": 30, "cost": 18, "price": 58},
                {"name": "炒菜", "sales": 15, "cost": 20, "price": 55},
            ],
            "feedback": [],
        },
    },
    {
        "name": "翻台率过低",
        "input": {
            "store_id": "majixian_001",
            "date": "2026-04-02",
            "metrics": {
                "daily_revenue": 25000,
                "target_revenue": 28000,
                "dine_traffic": 100,
                "avg_ticket": 200,
                "delivery_ratio": 0.1,
            },
            "menu": [
                {"name": "烧鹅", "sales": 20, "cost": 80, "price": 188},
                {"name": "叉烧", "sales": 15, "cost": 40, "price": 98},
            ],
            "feedback": [
                {"type": "service", "content": "等位超过30分钟"},
            ],
        },
    },
    {
        "name": "差评激增",
        "input": {
            "store_id": "hongchao_002",
            "date": "2026-04-03",
            "metrics": {
                "daily_revenue": 22000,
                "target_revenue": 25000,
                "dine_traffic": 110,
                "avg_ticket": 120,
                "delivery_ratio": 0.2,
            },
            "menu": [
                {"name": "煲仔饭", "sales": 50, "cost": 18, "price": 58},
            ],
            "feedback": [
                {"type": "product", "content": "煲仔饭里有异物"},
                {"type": "product", "content": "菜品不新鲜"},
                {"type": "service", "content": "服务员态度差"},
            ],
        },
    },
    {
        "name": "高毛利菜品滞销",
        "input": {
            "store_id": "hongchao_003",
            "date": "2026-04-04",
            "metrics": {
                "daily_revenue": 18000,
                "target_revenue": 22000,
                "dine_traffic": 80,
                "avg_ticket": 95,
                "delivery_ratio": 0.35,
            },
            "menu": [
                {
                    "name": "烧味拼盘",
                    "sales": 3,
                    "cost": 50,
                    "price": 128,
                    "profit_margin": 0.61,
                },
                {
                    "name": "煲仔饭",
                    "sales": 45,
                    "cost": 18,
                    "price": 58,
                    "profit_margin": 0.69,
                },
            ],
            "feedback": [
                {"type": "product", "content": "烧味太贵了"},
            ],
        },
    },
    {
        "name": "午市客流不足",
        "input": {
            "store_id": "majixian_002",
            "date": "2026-04-05",
            "metrics": {
                "daily_revenue": 15000,
                "target_revenue": 25000,
                "dine_traffic": 50,
                "avg_ticket": 180,
                "delivery_ratio": 0.15,
            },
            "menu": [
                {"name": "烧鹅", "sales": 10, "cost": 80, "price": 188},
                {"name": "白切鸡", "sales": 8, "cost": 35, "price": 88},
            ],
            "feedback": [],
        },
    },
    {
        "name": "外卖占比过高",
        "input": {
            "store_id": "hongchao_004",
            "date": "2026-04-06",
            "metrics": {
                "daily_revenue": 35000,
                "target_revenue": 30000,
                "dine_traffic": 100,
                "avg_ticket": 100,
                "delivery_ratio": 0.55,
            },
            "menu": [
                {"name": "煲仔饭", "sales": 200, "cost": 18, "price": 58},
            ],
            "feedback": [
                {"type": "service", "content": "堂食品质比外卖好"},
            ],
        },
    },
    {
        "name": "新菜品推出后无反响",
        "input": {
            "store_id": "majixian_003",
            "date": "2026-04-07",
            "metrics": {
                "daily_revenue": 20000,
                "target_revenue": 24000,
                "dine_traffic": 90,
                "avg_ticket": 140,
                "delivery_ratio": 0.2,
            },
            "menu": [
                {"name": "新菜品A", "sales": 2, "cost": 30, "price": 68},
                {"name": "烧鹅", "sales": 20, "cost": 80, "price": 188},
            ],
            "feedback": [
                {"type": "product", "content": "新菜品不知道是什么"},
            ],
        },
    },
    {
        "name": "周末客流正常但营收低",
        "input": {
            "store_id": "hongchao_005",
            "date": "2026-04-08",
            "metrics": {
                "daily_revenue": 22000,
                "target_revenue": 35000,
                "dine_traffic": 180,
                "avg_ticket": 75,
                "delivery_ratio": 0.2,
            },
            "menu": [
                {"name": "煲仔饭", "sales": 100, "cost": 18, "price": 58},
                {"name": "小菜", "sales": 80, "cost": 5, "price": 18},
            ],
            "feedback": [
                {"type": "service", "content": "点单价太低了"},
            ],
        },
    },
    {
        "name": "员工流失导致出品质量下降",
        "input": {
            "store_id": "hongchao_006",
            "date": "2026-04-09",
            "metrics": {
                "daily_revenue": 19000,
                "target_revenue": 25000,
                "dine_traffic": 95,
                "avg_ticket": 115,
                "delivery_ratio": 0.25,
            },
            "menu": [
                {"name": "煲仔饭", "sales": 40, "cost": 18, "price": 58},
                {"name": "炒菜", "sales": 20, "cost": 22, "price": 62},
            ],
            "feedback": [
                {"type": "product", "content": "出品不稳定"},
                {"type": "product", "content": "和以前味道差很多"},
            ],
        },
    },
    {
        "name": "竞争对手开业分流",
        "input": {
            "store_id": "majixian_004",
            "date": "2026-04-10",
            "metrics": {
                "daily_revenue": 16000,
                "target_revenue": 28000,
                "dine_traffic": 70,
                "avg_ticket": 150,
                "delivery_ratio": 0.3,
            },
            "menu": [
                {"name": "烧鹅", "sales": 15, "cost": 80, "price": 188},
                {"name": "叉烧", "sales": 12, "cost": 40, "price": 98},
            ],
            "feedback": [
                {"type": "service", "content": "隔壁新开了一家"},
            ],
        },
    },
]
