''' 可以用一個IP讀兩個以上的Slave'''
# pip install modbus_tk
import sys
import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.modbus_tcp as modbus_tcp
LOGGER = modbus_tk.utils.create_logger(name="console", record_format="%(message)s")
if __name__ == "__main__":
    try:
        #設立連線---------------------------------------------------------------------------------------------
        # The address in server need to write the IP of raspberry pie and open the port, pay attention to opening the corresponding port
        SERVER = modbus_tcp.TcpServer(address="140.118.172.166", port=502)
        LOGGER.info("running...")#print
        LOGGER.info("enter 'quit' for closing the server")#print
        SERVER.start()

        #設立slave -------------------------------------------------------------------------------------------------
        # add_slave(self, slave_id, unsigned=True, memory=None)
        # set_values(self, block_name, address, values)
        # https://programmer.help/blogs/modbus-tcp-protocol-learning.html
        #-----------------------------------------------------------------------------------------------------------

        #設立第一個slave
        SLAVE1 = SERVER.add_slave(1)
        SLAVE1.add_block('A', cst.HOLDING_REGISTERS, 0, 4) #Address 0, quantity 4
        SLAVE1.add_block('B', cst.HOLDING_REGISTERS, 4, 14)

        # 設立第一個slave
        SLAVE2 = SERVER.add_slave(2)
        SLAVE2.add_block('C', cst.COILS, 0, 10)   #Address 0, quantity 10
        SLAVE2.add_block('D', cst.HOLDING_REGISTERS, 0, 10) #Address 0, quantity 10

        # change value
        SLAVE1.set_values('A', 0, 4) #改變 address 0 的數值
        SLAVE1.set_values('B', 4, [1, 2, 3, 4, 5, 5, 12, 1232]) #改變 address 4 的數值

        SLAVE2.set_values('C', 0, [1, 1, 1, 1, 1, 1])
        SLAVE2.set_values('D', 0, 10)


        while True:
            CMD = sys.stdin.readline()S
            if CMD.find('quit') == 0:
                sys.stdout.write('bye-bye\r\n')
                break
            else:
                sys.stdout.write("unknown command %s\r\n" % (args[0]))
    finally:
        SERVER.stop()