"""
配置查看器组件
用于显示不同格式的配置信息
"""

import streamlit as st
import json
import os

class ConfigViewer:
    """配置查看器"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
    
    def show_json_config(self):
        """显示JSON格式配置"""
        try:
            config_data = self.config_manager.get_all()
            json_str = json.dumps(config_data, indent=2, ensure_ascii=False)
            
            st.write("**JSON格式配置**")
            st.code(json_str, language="json")
            
            # 下载按钮
            st.download_button(
                label="📥 下载JSON配置",
                data=json_str,
                file_name="config.json",
                mime="application/json"
            )
            
        except Exception as e:
            st.error(f"❌ 显示JSON配置失败: {str(e)}")
    
    def show_env_config(self):
        """显示环境变量配置"""
        try:
            # 获取环境变量
            env_vars = {}
            for key, value in os.environ.items():
                if key.startswith(('DEEPWIN_', 'LLM_', 'DEEPARM_')):
                    env_vars[key] = value
            
            if env_vars:
                st.write("**环境变量配置**")
                
                # 显示环境变量
                for key, value in env_vars.items():
                    st.code(f"{key}={value}")
                
                # 生成.env文件内容
                env_content = "\n".join([f"{key}={value}" for key, value in env_vars.items()])
                
                # 下载按钮
                st.download_button(
                    label="📥 下载.env文件",
                    data=env_content,
                    file_name="config.env",
                    mime="text/plain"
                )
            else:
                st.info("ℹ️ 未找到相关的环境变量")
                
        except Exception as e:
            st.error(f"❌ 显示环境变量配置失败: {str(e)}")
