import gradio as gr
from datetime import datetime

def get_time():
    # 返回带毫秒的时间字符串
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:23]

def update_time():
    # 仅更新 Textbox 的 value
    return gr.update(value=get_time())

with gr.Blocks() as demo:
    # 方式一：Timer 定时刷新（每 0.05 秒）
    timer_box = gr.Textbox(label="Timer 定时刷新（毫秒）", interactive=False)
    timer = gr.Timer(0.05, active=True)
    timer.tick(fn=update_time, inputs=None, outputs=timer_box)


demo.launch()