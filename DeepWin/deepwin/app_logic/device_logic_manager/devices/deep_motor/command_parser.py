from typing import List
from .command_description import *

class CommandParser:
    """DeepMotor 命令描述和注册中心"""
    _commands = CommandDescription.commands

    # 构建命令模型映射表（从_commands中提取）
    @classmethod
    def _get_command_models(cls) -> dict:
        """获取命令名称到模型类的映射"""
        models = {}
        for cmd in cls._commands:
            models[cmd["name"]] = cmd["model"]
        return models

    @classmethod
    def get_command_description(cls, command_name: str):
        """根据命令名称获取命令描述"""
        for command in cls._commands:
            if command["name"] == command_name:
                return command
        return None

    @classmethod
    def get_all_command_descriptions(cls):
        """获取所有命令描述"""
        return cls._commands

    @classmethod
    def get_commands_by_category(cls, category: str):
        """根据类别获取命令"""
        return [cmd for cmd in cls._commands if cmd.get("category") == category]

    @classmethod
    def get_all_voice_prompts(cls):
        """获取所有命令的语音提示"""
        prompts = {}
        for command in cls._commands:
            prompts[command["name"]] = command.get("voice_prompt", [])
        return prompts

    @classmethod
    def get_command_help(cls):
        """获取命令帮助信息"""
        help_info = {}
        for command in cls._commands:
            help_info[command["name"]] = {
                "description": command["description"],
                "example": command["example"],
                "voice_prompts": command.get("voice_prompt", []),
                "category": command["category"]
            }
        return help_info

    @classmethod
    def search_commands(cls, keyword: str):
        """根据关键词搜索命令"""
        keyword = keyword.lower()
        results = []
        
        for command in cls._commands:
            # 搜索命令名称
            if keyword in command["name"].lower():
                results.append(command)
                continue
            
            # 搜索描述
            if keyword in command["description"].lower():
                results.append(command)
                continue
            
            # 搜索语音提示
            voice_prompts = command.get("voice_prompt", [])
            for prompt in voice_prompts:
                if keyword in prompt.lower():
                    results.append(command)
                    break
        
        return results

    
    @classmethod
    def get_command_model(cls, command_name: str):
        """获取命令模型类"""
        models = cls._get_command_models()
        return models.get(command_name)
    
    @classmethod
    def get_all_command_names(cls) -> List[str]:
        """获取所有命令名称"""
        return list(cls._get_command_models().keys())
    
    @classmethod
    def get_command_schema(cls, command_name: str) -> dict:
        """获取命令的JSON Schema"""
        model = cls.get_command_model(command_name)
        if model:
            return model.schema()
        return {}
    
    @classmethod
    def get_all_schemas(cls) -> dict:
        """获取所有命令的JSON Schema"""
        schemas = {}
        models = cls._get_command_models()
        for name, model in models.items():
            schemas[name] = model.schema()
        return schemas
    
    @classmethod
    def validate_command(cls, command_name: str, params: dict):
        """验证命令参数"""
        model = cls.get_command_model(command_name)
        if not model:
            raise ValueError(f"未知命令: {command_name}")
        
        try:
            return model(**params)
        except Exception as e:
            raise ValueError(f"命令参数验证失败: {e}")
    
    @classmethod
    def parse_command_string(cls, command_str: str):
        """解析命令字符串，如 'motor_set_speed(1500)'"""
        try:
            if '(' in command_str and command_str.endswith(')'):
                func_name = command_str[:command_str.find('(')]
                args_str = command_str[command_str.find('(')+1:-1]
                
                models = cls._get_command_models()
                if func_name not in models:
                    raise ValueError(f"未知命令: {func_name}")
                
                # 解析参数
                args = []
                if args_str.strip():
                    for arg in args_str.split(','):
                        arg = arg.strip()
                        try:
                            if '.' in arg:
                                args.append(float(arg))
                            else:
                                args.append(int(arg))
                        except ValueError:
                            args.append(arg)
                
                # 获取命令模型
                model = models[func_name]
                
                # 根据参数位置创建参数字典
                param_names = list(model.model_fields.keys())
                params = {}
                
                for i, arg in enumerate(args):
                    if i < len(param_names):
                        params[param_names[i]] = arg
                
                # 填充默认值
                for field_name, field in model.model_fields.items():
                    if field_name not in params and field.default is not None:
                        params[field_name] = field.default
                
                return func_name, params
            else:
                return None, {}
        except Exception as e:
            raise ValueError(f"解析命令字符串失败: {e}")

    @classmethod
    def parse_command_dashscope(cls, command_dict: dict):
        """
        解析百炼平台命令字符串，如：
        command_dict: {'name': 'motor_set_pos', 'params': [{'name': 'pos', 'value': '1', 'normValue': '1'}]}
        """     
        try:
            command_name = command_dict.get('name', '')
            params = command_dict.get('params', [])
            params_dict = {}
            # 将params转换为字典
            if not params:
                params_dict = {param['name']: param['value'] for param in params}
            else:
                params_dict = {}
            print(f"params_dict: {params_dict}")
            
            # 验证参数
            validated_params = cls.validate_command(command_name, params_dict)
            
            # 返回与 parse_command_string 一致的格式
            return command_name, validated_params.model_dump()
        except Exception as e:
            raise ValueError(f"解析百炼平台命令字符串失败: {e}")


                
# === 便捷函数（保持向后兼容）===
def get_command_model(command_name: str):
    """获取命令模型类的便捷函数"""
    return CommandParser.get_command_model(command_name)

def validate_command_params(command_name: str, params: dict):
    """验证命令参数的便捷函数"""
    return CommandParser.validate_command(command_name, params)

def parse_command_string(command_str: str):
    """解析命令字符串的便捷函数"""
    return CommandParser.parse_command_string(command_str)

def get_all_command_names() -> List[str]:
    """获取所有命令名称的便捷函数"""
    return CommandParser.get_all_command_names()

def get_command_schemas() -> dict:
    """获取所有命令Schema的便捷函数"""
    return CommandParser.get_all_schemas()