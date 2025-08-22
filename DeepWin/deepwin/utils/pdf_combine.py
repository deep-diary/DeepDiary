import gradio as gr
import PyPDF2
import io
import os
from typing import List
import tempfile

def merge_pdfs(pdf_files: List[str]) -> str:
    """
    合并多个PDF文件
    
    Args:
        pdf_files: PDF文件路径列表
        
    Returns:
        合并后的PDF文件路径
    """
    if not pdf_files:
        return None
    
    # 创建PDF合并器
    merger = PyPDF2.PdfMerger()
    
    try:
        # 逐个添加PDF文件
        for pdf_file in pdf_files:
            if pdf_file and os.path.exists(pdf_file):
                merger.append(pdf_file)
        
        # 创建临时文件保存合并结果
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, "merged_document.pdf")
        
        # 写入合并后的PDF
        with open(output_path, "wb") as output_file:
            merger.write(output_file)
        
        merger.close()
        return output_path
        
    except Exception as e:
        print(f"合并PDF时出错: {str(e)}")
        return None

def process_pdfs(files):
    """
    处理上传的PDF文件并返回合并结果
    
    Args:
        files: 上传的文件列表
        
    Returns:
        合并后的PDF文件路径或错误信息
    """
    if not files:
        return "请选择要合并的PDF文件"
    
    # 检查文件类型
    pdf_files = []
    for file in files:
        if file.name.lower().endswith('.pdf'):
            pdf_files.append(file.name)
        else:
            return f"文件 {file.name} 不是PDF格式，请只上传PDF文件"
    
    if len(pdf_files) < 2:
        return "请至少选择2个PDF文件进行合并"
    
    # 合并PDF
    result_path = merge_pdfs(pdf_files)
    
    if result_path:
        return result_path
    else:
        return "PDF合并失败，请检查文件是否正确"

# 创建Gradio界面
def create_interface():
    with gr.Blocks(title="PDF合并工具", theme=gr.themes.Soft()) as interface:
        gr.Markdown("# 📄 PDF合并工具")
        gr.Markdown("上传多个PDF文件，将它们合并成一个文档")
        
        with gr.Row():
            with gr.Column(scale=2):
                # 文件上传组件
                file_input = gr.File(
                    label="选择PDF文件",
                    file_count="multiple",
                    file_types=[".pdf"],
                    height=200
                )
                
                # 合并按钮
                merge_btn = gr.Button("🔄 合并PDF", variant="primary", size="lg")
                
                # 状态显示
                status_output = gr.Textbox(
                    label="状态信息",
                    placeholder="等待上传文件...",
                    interactive=False
                )
            
            with gr.Column(scale=1):
                # 使用说明
                gr.Markdown("""
                ## 📋 使用说明
                
                1. 点击上方区域选择多个PDF文件
                2. 确保所有文件都是PDF格式
                3. 点击"合并PDF"按钮
                4. 下载合并后的文件
                
                ## ⚠️ 注意事项
                
                - 支持的文件格式：PDF
                - 建议文件大小不超过100MB
                - 合并顺序按文件选择顺序
                """)
        
        # 下载组件
        download_output = gr.File(
            label="下载合并后的PDF",
            visible=False
        )
        
        # 绑定事件
        def on_merge(files):
            if not files:
                return "请选择要合并的PDF文件", None
            
            result = process_pdfs(files)
            
            if result and os.path.exists(result):
                # 合并成功，显示下载链接
                return f"✅ PDF合并成功！文件已保存到: {result}", result
            else:
                # 合并失败，显示错误信息
                return f"❌ {result}", None
        
        merge_btn.click(
            fn=on_merge,
            inputs=[file_input],
            outputs=[status_output, download_output]
        )
        
        # 文件上传后自动显示状态
        def on_file_change(files):
            if files:
                file_names = [f.name for f in files]
                return f"已选择 {len(files)} 个文件:\n" + "\n".join(file_names)
            return "等待上传文件..."
        
        file_input.change(
            fn=on_file_change,
            inputs=[file_input],
            outputs=[status_output]
        )
    
    return interface

if __name__ == "__main__":
    # 创建并启动界面
    print("正在创建Gradio界面...")
    interface = create_interface()
    print("界面创建完成，正在启动...")
    
    try:
        # 使用最简单的启动方式
        interface.launch(
            inbrowser=True,
            quiet=True
        )
    except Exception as e:
        print(f"启动失败: {e}")
        print("尝试使用可分享链接...")
        try:
            interface.launch(share=True)
        except Exception as e2:
            print(f"可分享启动也失败: {e2}")
            print("请检查网络配置或防火墙设置")


