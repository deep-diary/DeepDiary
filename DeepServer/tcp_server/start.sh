
#!/bin/bash

# 杀掉原来进程
pkill -f "python -u tcp_video_server_web.py"
# 后台启动
nohup python -u tcp_video_server_web.py > output.log 2>&1 &
