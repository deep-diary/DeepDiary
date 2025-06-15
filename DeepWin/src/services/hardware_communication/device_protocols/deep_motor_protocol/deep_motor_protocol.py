# from typing import Union, List

# class DeepMotorProtocol:
#     def encode_command(self, command_type: str, args: tuple) -> Union[bytes, List[bytes]]:
#         """
#         将命令类型和参数编码为底层协议命令。
#         :param command_type: 命令类型。
#         :param args: 命令参数元组。
#         :return: 编码后的命令字节或命令字节列表。
#         """
#         self.logger.debug(f"DeepMotorProtocol: 编码命令 '{command_type}' 参数: {args}")
        
#         # 获取命令处理器
#         handler = self._command_handlers.get(command_type)
#         if not handler:
#             raise ValueError(f"不支持的命令类型: {command_type}")
            
#         # 将位置参数转换为关键字参数
#         kwargs = {}
#         if command_type == 'enable_motor':
#             kwargs['motor_id'] = args[0] if args else 1
#         elif command_type == 'reset_motor':
#             kwargs['motor_id'] = args[0] if args else 1
#         elif command_type == 'zero_motor':
#             kwargs['motor_id'] = args[0] if args else 1
#         elif command_type == 'set_motor_mode':
#             kwargs['motor_id'] = args[0] if args else 1
#             kwargs['value'] = args[1] if len(args) > 1 else None
#         elif command_type == 'set_motor_mit_mode':
#             kwargs['motor_id'] = args[0] if args else 1
#             kwargs['torque'] = args[1] if len(args) > 1 else 0.0
#             kwargs['position'] = args[2] if len(args) > 2 else 0.0
#             kwargs['speed'] = args[3] if len(args) > 3 else 0.0
#             kwargs['kp'] = args[4] if len(args) > 4 else 0.0
#             kwargs['kd'] = args[5] if len(args) > 5 else 0.0
#         elif command_type == 'write_motor_param':
#             kwargs['motor_id'] = args[0] if args else 1
#             kwargs['index'] = args[1] if len(args) > 1 else None
#             kwargs['value'] = args[2] if len(args) > 2 else None
#         elif command_type == 'read_motor_param':
#             kwargs['motor_id'] = args[0] if args else 1
#             kwargs['index'] = args[1] if len(args) > 1 else None
#         elif command_type == 'jog_motor':
#             kwargs['motor_id'] = args[0] if args else 1
#             kwargs['speed'] = args[1] if len(args) > 1 else 0
#         elif command_type == 'stop_jog_motor':
#             kwargs['motor_id'] = args[0] if args else 1
#         elif command_type == 'init_motor':
#             kwargs['motor_id'] = args[0] if args else 1
#         elif command_type == 'init_all_motors':
#             kwargs['motor_ids'] = args[0] if args else []
#         elif command_type == 'reset_all_motors':
#             kwargs['motor_ids'] = args[0] if args else []
#         elif command_type == 'set_motor_position':
#             kwargs['motor_id'] = args[0] if args else 1
#             kwargs['position'] = args[1] if len(args) > 1 else None
#         elif command_type == 'set_all_motors_position':
#             kwargs['motor_ids'] = args[0] if args else []
#             kwargs['positions'] = args[1] if len(args) > 1 else []
#         elif command_type == 'set_motor_pos_speed':
#             kwargs['motor_id'] = args[0] if args else 1
#             kwargs['position'] = args[1] if len(args) > 1 else None
#             kwargs['speed'] = args[2] if len(args) > 2 else None
#         elif command_type == 'set_all_motors_pos_speed':
#             kwargs['motor_ids'] = args[0] if args else []
#             kwargs['positions'] = args[1] if len(args) > 1 else []
#             kwargs['speeds'] = args[2] if len(args) > 2 else []
            
#         # 调用命令处理器
#         return handler(**kwargs) 