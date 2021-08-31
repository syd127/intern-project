
import modbus_tk.modbus_tcp as mt
import modbus_tk.defines as cst
import serial
import modbus_tk
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu


# # 遠程連接到slave端（從）
# master = mt.TcpMaster("140.118.172.166", 502)
# master.set_timeout(5.0)
# logger = modbus_tk.utils.create_logger("console")

# # @slave=1 : identifier of the slave. from 1 to 247.  0為廣播所有的slave
# # @function_code=READ_HOLDING_REGISTERS：功能碼
# # @starting_address=1：開始地址
# # @quantity_of_x=3：寄存器/線圈的數量
# # @output_value：一個整數或可叠代的值：1/[1,1,1,0,0,1]/xrange(12)
# # @data_format
# # @expected_length
# aa = master.execute(slave=1, function_code=md.READ_HOLDING_REGISTERS, starting_address=0, quantity_of_x=3, output_value=5)
# print(aa)  # 取到的所有寄存器的值
# print(aa[0])    # 獲取第一個寄存器的值

import serial
import modbus_tk
import modbus_tk.defines as cst

from pymodbus.client.sync import ModbusSerialClient as ModbusClient
# #PORT = 1
# PORT = "COM3"
# def main():
#     logger = modbus_tk.utils.create_logger("console")
#     try:
#     #Connect to the slave
#         # master = modbus_rtu.RtuMaster(serial.Serial(port=PORT, baudrate=9600, bytesize=8, parity='N', stopbits=1, xonxoff=0))
#         # master = ModbusClient(method = 'localhost', port = 'COM3', stopbits=1 , bytesize=8, parity='N', baudrate=9600, timeout = 1)
#         master = cst.TcpMaster("140.118.172.166", 502)
#         # master = ModbusClient(host="localhost", auto_open=True, auto_close=True)

#         connection = master.connect()
#         master.set_timeout(5.0)
#         master.set_verbose(True)
#         logger.info("connected")
#         logger.info(master.execute(1, cst.READ_HOLDING_REGISTERS, 1, 1))
#     #send some queries
#     #logger.info(master.execute(1, cst.READ_COILS, 0, 10))
#     #logger.info(master.execute(1, cst.READ_DISCRETE_INPUTS, 0, 8))
#     #logger.info(master.execute(1, cst.READ_INPUT_REGISTERS, 100, 3))
#     #logger.info(master.execute(1, cst.READ_HOLDING_REGISTERS, 100, 12))
#     #logger.info(master.execute(1, cst.WRITE_SINGLE_COIL, 7, output_value=1))
#     #logger.info(master.execute(1, cst.WRITE_SINGLE_REGISTER, 100, output_value=54))
#     #logger.info(master.execute(1, cst.WRITE_MULTIPLE_COILS, 0, output_value=))
#     #logger.info(master.execute(1, cst.WRITE_MULTIPLE_REGISTERS, 100, output_value=xrange(12)))
#     except modbus_tk.modbus.ModbusError as exc:
#         logger.error("%s- Code=%d", exc, exc.get_exception_code())
# if __name__ == "__main__":
#     main()





import sys

import logging

import modbus_tk

import modbus_tk.defines as cst

import modbus_tk.modbus_tcp as modbus_tcp

# LOGGER = modbus_tk.utils.create_logger("console")

# if __name__ == "main":
#     try:

#         #连接从机地址,这里要注意端口号和IP与从机一致

#         MASTER = modbus_tcp.TcpMaster("140.118.172.166", 502)
#         c = ModbusClient(host="140.118.172.166", auto_open=True, auto_close=True)
#         connection = c.connect()
#         MASTER.set_timeout(5.0)

#         # logger.info - 最佳的logger 来源和相关信息。("connected")

#         # #读取从机1的0-4保持寄存器

#         # logger.info - 最佳的logger 来源和相关信息。(MASTER.execute(1, cst.READ_HOLDING_REGISTERS, 0, 4))

#         # #读取从机1的4-14保持寄存器，因为寄存器独立分块了，所以不能直接连通读取，强行结果是会出现数据越界

#         # logger.info - 最佳的logger 来源和相关信息。(MASTER.execute(1, cst.READ_HOLDING_REGISTERS, 4, 14))

#         # # 需要按照execute格式

#         # logger.info - 最佳的logger 来源和相关信息。(MASTER.execute(1, cst.WRITE_MULTIPLE_REGISTERS, 0, output_value=[0, 1, 2]))

#         # logger.info - 最佳的logger 来源和相关信息。(MASTER.execute(1, cst.READ_HOLDING_REGISTERS, 0, 4))
#         # logger.info - 最佳的logger 来源和相关信息。(MASTER.execute(2, cst.READ_COILS, 0, 8))
#         # logger.info - 最佳的logger 来源和相关信息。(MASTER.execute(2, cst.WRITE_MULTIPLE_COILS, 0, output_value=[1, 0, 0, 0, 1]))
#         # logger.info - 最佳的logger 来源和相关信息。(MASTER.execute(2, cst.READ_COILS, 0, 8))
#         # logger.info - 最佳的logger 来源和相关信息。(MASTER.execute(2, cst.READ_HOLDING_REGISTERS, 0, 4))
#         # 线圈和寄存器地址不是同一区块的
#     except modbus_tk.modbus.ModbusError as err:
#         LOGGER.error("%s- Code=%d" % (err, err.get_exception_code()))



import sys
import logging
import threading
import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.modbus as modbus
import modbus_tk.modbus_tcp as modbus_tcp
LOGGER = modbus_tk.utils.create_logger(name="console", record_format="%(message)s")

print('bbbbb')
try:
    print('dddd',)

    # server里的address需要写的树莓派的IP和需要开放的端口，注意开放相应的端口

    SERVER = modbus_tcp.TcpServer(address="140.118.172.166", port=502)
    # logger.info - 最佳的logger 来源和相关信息。("running…")
    # logger.info - 最佳的logger 来源和相关信息。("enter 'quit' for closing the server")
    # 服务启动
    LOGGER.info("running...")
    LOGGER.info("enter 'quit' for closing the server")
    SERVER.start()
    # 建立第一个从机
    SLAVE1 = SERVER.add_slave(1)
    SLAVE1.add_block('A', cst.HOLDING_REGISTERS, 0, 4)#地址0，长度4
    SLAVE1.add_block('B', cst.HOLDING_REGISTERS, 4, 14)
    #建立另一个从机2
    SLAVE2 = SERVER.add_slave(2)
    SLAVE2.add_block('C', cst.COILS, 0, 10)   #地址0，长度10
    SLAVE2.add_block('D', cst.HOLDING_REGISTERS, 0, 10)#地址0，长度10

    SLAVE1.set_values('A', 0, 4) #改变在地址0处的寄存器的值
    SLAVE1.set_values('B', 4, [1, 2, 3, 4, 5, 5, 12, 1232])     #改变在地址4处的寄存器的值
    SLAVE2.set_values('C', 0, [1, 1, 1, 1, 1, 1])
    SLAVE2.set_values('D', 0, 10)

    while True:
        CMD = sys.stdin.readline()
        if CMD.find('quit') == 0:
            sys.stdout.write('bye-bye\r\n')
            break
        else:

            sys.stdout.write("unknown command %s\r\n" % (args[0]))
except:
    print('aaaaaa')
finally:
    print('aaa')
    SERVER.stop()
    