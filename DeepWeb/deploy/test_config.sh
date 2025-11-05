#!/bin/bash

# Nginx 配置测试和诊断脚本

echo "=========================================="
echo "Nginx 配置诊断测试"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. 检查 Nginx 配置语法
echo -e "${YELLOW}[1] 检查 Nginx 配置语法...${NC}"
if sudo nginx -t 2>&1 | grep -q "syntax is ok"; then
    echo -e "${GREEN}✓ Nginx 配置语法正确${NC}"
else
    echo -e "${RED}✗ Nginx 配置语法错误${NC}"
    sudo nginx -t
    exit 1
fi
echo ""

# 2. 检查配置是否加载
echo -e "${YELLOW}[2] 检查配置是否已加载...${NC}"
if sudo nginx -T 2>&1 | grep -q "img.deep-diary.com"; then
    echo -e "${GREEN}✓ img.deep-diary.com 配置已加载${NC}"
else
    echo -e "${RED}✗ img.deep-diary.com 配置未找到${NC}"
    exit 1
fi
echo ""

# 3. 检查 Nginx 服务状态
echo -e "${YELLOW}[3] 检查 Nginx 服务状态...${NC}"
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx 服务正在运行${NC}"
else
    echo -e "${RED}✗ Nginx 服务未运行${NC}"
    exit 1
fi
echo ""

# 4. 检查端口监听
echo -e "${YELLOW}[4] 检查端口 80 监听状态...${NC}"
if sudo ss -tlnp | grep -q ":80 "; then
    echo -e "${GREEN}✓ 端口 80 正在监听${NC}"
    sudo ss -tlnp | grep ":80 "
else
    echo -e "${RED}✗ 端口 80 未监听${NC}"
    exit 1
fi
echo ""

# 5. 检查后端服务（Immich）
echo -e "${YELLOW}[5] 检查后端服务 localhost:2283...${NC}"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:2283/ | grep -q "200"; then
    echo -e "${GREEN}✓ 后端服务 localhost:2283 正常响应${NC}"
else
    echo -e "${RED}✗ 后端服务 localhost:2283 无响应${NC}"
fi
echo ""

# 6. 本地代理测试
echo -e "${YELLOW}[6] 测试本地代理（通过 Nginx）...${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: img.deep-diary.com" http://127.0.0.1/)
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ 本地代理测试通过 (HTTP $HTTP_CODE)${NC}"
else
    echo -e "${RED}✗ 本地代理测试失败 (HTTP $HTTP_CODE)${NC}"
fi
echo ""

# 7. DNS 解析检查
echo -e "${YELLOW}[7] 检查 DNS 解析...${NC}"
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "无法获取")
echo "服务器公网 IP: $PUBLIC_IP"

# 尝试解析域名
if curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://img.deep-diary.com/ 2>&1 | grep -q "200\|301\|302"; then
    echo -e "${GREEN}✓ img.deep-diary.com DNS 解析正常，可以访问${NC}"
elif curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://img.deep-diary.com/ 2>&1 | grep -q "Could not resolve"; then
    echo -e "${RED}✗ img.deep-diary.com DNS 无法解析${NC}"
    echo -e "${YELLOW}  需要添加 DNS A 记录:${NC}"
    echo -e "${YELLOW}  域名: img.deep-diary.com${NC}"
    echo -e "${YELLOW}  类型: A${NC}"
    echo -e "${YELLOW}  值: $PUBLIC_IP${NC}"
else
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://img.deep-diary.com/ 2>&1)
    echo -e "${YELLOW}⚠ img.deep-diary.com 可以解析，但返回 HTTP $HTTP_CODE${NC}"
fi
echo ""

# 8. 检查防火墙
echo -e "${YELLOW}[8] 检查防火墙规则...${NC}"
if command -v ufw &> /dev/null; then
    UFW_STATUS=$(sudo ufw status 2>/dev/null | head -1)
    echo "UFW 状态: $UFW_STATUS"
    if echo "$UFW_STATUS" | grep -q "inactive"; then
        echo -e "${GREEN}✓ 防火墙未启用${NC}"
    else
        if sudo ufw status | grep -q "80/tcp"; then
            echo -e "${GREEN}✓ 端口 80 已在防火墙中开放${NC}"
        else
            echo -e "${YELLOW}⚠ 端口 80 可能未在防火墙中开放${NC}"
            echo -e "${YELLOW}  建议运行: sudo ufw allow 80/tcp${NC}"
        fi
    fi
else
    echo "未检测到 UFW，请手动检查防火墙规则"
fi
echo ""

# 9. 总结
echo "=========================================="
echo "诊断总结"
echo "=========================================="
echo ""
echo "Nginx 配置状态:"
echo "  - deep-diary.com → http://localhost:7860"
echo "  - img.deep-diary.com → http://localhost:2283"
echo ""
echo "如果外部无法访问 img.deep-diary.com，请检查："
echo "  1. DNS 是否已添加 A 记录: img.deep-diary.com → $PUBLIC_IP"
echo "  2. 防火墙是否开放端口 80"
echo "  3. 云平台安全组是否允许端口 80 入站流量"
echo ""
echo "DNS 配置完成后，等待几分钟让 DNS 传播，然后再次测试。"
echo ""

