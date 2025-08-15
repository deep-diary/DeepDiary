import cantools
from pprint import pprint

# 创建温度信号的转换器
temp_conversion = cantools.database.conversion.LinearConversion(
    scale=0.1,
    offset=0,
    is_float=True
)

def create_dbc(dbc_name):
    db = cantools.db.Database()

    # 添加消息定义
    # 对于 big_endian (Motorola) 格式：
    # 0 1 2 3 4 5 6 7 | 8 9 10 11 12 13 14 15 | ...
    # 字节 0         | 字节 1               | ...
    msg = cantools.db.Message(
        name='MotorStatus',
        frame_id=0x028006FD,
        is_extended_frame=True,
        length=8,  # 8 bytes = 64 bits
        signals=[
            cantools.db.Signal(
                name='Position',
                start=0,    # Bits 0-15 (Byte 0, Byte 1)
                length=16,
                byte_order='big_endian',
                is_signed=True,
                unit='rad'
            ),
            cantools.db.Signal(
                name='Speed',
                start=16,   # Bits 16-31 (Byte 2, Byte 3)
                length=16,
                byte_order='big_endian',
                is_signed=True,
                unit='rad/s'
            ),
            cantools.db.Signal(
                name='Torque',
                start=32,   # Bits 32-47 (Byte 4, Byte 5)
                length=16,
                byte_order='big_endian',
                is_signed=True,
                unit='Nm'
            ),
            cantools.db.Signal(
                name='Temperature',
                start=48,   # Bits 48-63 (Byte 6, Byte 7)
                length=8,
                byte_order='big_endian',
                is_signed=True,
                unit='°C'
            )
        ]
    )
    db.messages.append(msg)

    try:
        cantools.database.dump_file(db, dbc_name)
        print(f"DBC file '{dbc_name}' created successfully.")
    except Exception as e:
        print(f"Error creating DBC file: {e}")

dbc_name = 'deep_motor.dbc'

create_dbc(dbc_name)

# 读取dbc文件
db = cantools.database.load_file(dbc_name)

# 获取消息定义
msg = db.get_message_by_name('MotorStatus')
msg = db.get_message_by_frame_id(0x028006FD)
pprint(msg)

# 获取信号定义
signal = msg.signals
pprint(signal)

# encode
data = msg.encode({'Position': 10, 'Speed': 20, 'Torque': 5, 'Temperature': 31})
# 十六进制打印 data
print("0x" + "".join([f"{x:02X}" for x in data]))

# decode
decoded = msg.decode(data)
pprint(decoded)

# 测试实际数据
test_data = bytes([0x41, 0x54, 0x02, 0x80, 0x06, 0xFD, 0x08, 0xFF, 0xFF, 0x82, 0x0F, 0x81, 0x51, 0x01, 0x36, 0x0D, 0x0A])
decoded = msg.decode(test_data[7:15])  # 只解码数据部分（去掉AT和CAN ID）
pprint(decoded)

# 测试物理量转raw
param = 1000
value = (param - temp_conversion.offset) / temp_conversion.scale
pprint(value)

# 测试raw转物理量
param = value * temp_conversion.scale + temp_conversion.offset
pprint(param)
