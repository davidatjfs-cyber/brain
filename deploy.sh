#!/bin/bash
set -e

REMOTE_HOST="8.153.95.62"
REMOTE_USER="root"
REMOTE_DIR="/opt/brain-v1"
BRAIN_PORT=9000

echo "=== Brain V5.0 + Synapse 部署脚本 ==="
echo "目标: ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}"

echo "[1/6] 测试SSH连接..."
ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST} "echo 'SSH连接成功'" || {
    echo "ERROR: 无法连接到服务器"
    exit 1
}

echo "[2/6] 同步代码到服务器..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "mkdir -p ${REMOTE_DIR}"
rsync -avz --exclude='__pycache__' --exclude='.DS_Store' --exclude='*.pyc' --exclude='data/synapse' \
    /Users/magainze/brain-v1/ ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/

echo "[3/6] 安装服务器依赖..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "cd ${REMOTE_DIR} && pip3 install -r requirements.txt 2>/dev/null || pip install -r requirements.txt"

echo "[4/6] 配置systemd服务..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "cat > /etc/systemd/system/brain.service << 'EOF'
[Unit]
Description=Brain V5 + Synapse Decision Engine
After=network.target

[Service]
Type=simple
WorkingDirectory=${REMOTE_DIR}
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port ${BRAIN_PORT}
Restart=always
RestartSec=5
Environment=PYTHONPATH=${REMOTE_DIR}

[Install]
WantedBy=multi-user.target
EOF"

echo "[5/6] 重启服务..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "systemctl daemon-reload && systemctl enable brain && systemctl restart brain"
sleep 3

echo "[6/6] 验证..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "curl -s http://localhost:${BRAIN_PORT}/feishu/agents | python3 -c 'import sys,json; d=json.load(sys.stdin); print(f\"Agents: {d[\\\"total\\\"]}\")'" || echo "WARNING: 验证失败"

echo ""
echo "=== 部署完成 ==="
echo "外部访问: http://${REMOTE_HOST}/brain/"
echo "内部访问: http://localhost:${BRAIN_PORT}"
echo ""
echo "飞书Bot端点:"
echo "  POST /brain/feishu/webhook    - 飞书事件回调"
echo "  POST /brain/feishu/send       - 发送消息"
echo "  POST /brain/feishu/feedback   - 用户反馈"
echo "  POST /brain/feishu/debate     - 触发辩论"
echo "  GET  /brain/feishu/agents     - Agent列表"
echo "  GET  /brain/feishu/agent/scores - Agent评分"