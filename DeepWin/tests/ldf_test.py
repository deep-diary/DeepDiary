import ldfparser
import binascii
import json

path = "demo.ldf"

# Load LDF
ldf = ldfparser.parse_ldf(path = path)
frame = ldf.get_unconditional_frame('EcmEcm_Lin4Fr01_ECM_LIN4')

# Get baudrate from LDF
print(ldf.get_baudrate())

# Encode signal values into frame
message = frame.encode_raw({"LbxvPosnReqExvPosnReq_ECM_LIN4": 123, "LbxvPosnReqExvCalibReq_ECM_LIN4": 0})
print(binascii.hexlify(message))


# Decode message into dictionary of signal names and values
received = bytearray([0x7B, 0x00])
print(frame.decode(received))


# Encode signal values through converters
message = frame.encode({"MotorRPM": 100, "FanState": "ON"})
print(binascii.hexlify(message))


ldf = ldfparser.parse_ldf_to_dict(path)
print(json.dumps(ldf, indent=2, ensure_ascii=False))