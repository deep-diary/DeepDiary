#!/bin/bash
# DeepWeb 最终启动脚本

echo "=========================================="
echo "DeepWeb - 不倒翁设备控制平台"
echo "=========================================="

# 检查虚拟环境
if [ -d "diary_env" ]; then
    echo "激活虚拟环境: diary_env"
    source diary_env/bin/activate
elif [ -n "$VIRTUAL_ENV" ]; then
    echo "已激活虚拟环境: $VIRTUAL_ENV"
else
    echo "未找到虚拟环境，使用系统Python"
fi

# 检查Python环境
python_version=$(python3 --version 2>&1)
echo "Python版本: $python_version"

# 安装核心依赖
# echo "安装依赖包..."
# pip install -r requirements.txt

echo "=========================================="
echo "启动DeepWeb应用..."
echo "请在浏览器中访问: http://localhost:7860"
echo "TCP视频接收端口: 8080"
echo "按 Ctrl+C 停止服务"
echo "=========================================="


# 杀掉原来进程
lsof -i :7860 | awk 'NR>1 {print $2}' | xargs -r kill -9

# 启动web界面应用
nohup python -u main.py > output.log 2>&1 &
