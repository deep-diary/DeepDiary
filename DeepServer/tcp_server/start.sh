
#!/bin/bash
# 激活环境
source ~/diary_env/bin/activate

# 杀掉原来进程
pkill -f "python -u tcp_video_server_web.py"
# 后台启动
nohup python -u tcp_video_server_web.py --stream-name ATK-DNESP32S3-9888e000ae28 > output.log 2>&1 &
