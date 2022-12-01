import ctypes

from bitstring import BitArray


class InsMem(object):
    def __init__(self, name, io_dir):
        self.id = name

        with open(io_dir + "/imem.txt") as im:
            self.IMem = [data.replace("\n", "") for data in im.readlines()]

    def read_instr(self, read_address: int):
        if len(self.IMem) < read_address + 4:
            raise Exception("Instruction MEM - Out of bound access")
        return "".join(self.IMem[read_address: read_address + 4])


class DataMem(object):
    def __init__(self, name, io_dir):
        self.id = name
        self.io_dir = io_dir
        with open(io_dir + "/dmem.txt") as dm:
            self.DMem = [data.replace("\n", "") for data in dm.readlines()]

    def read_data(self, read_address: int) -> int:
        # read data memory
        # return 32-bit signed int value
        if len(self.DMem) < read_address + 4:
            raise Exception("Data MEM - Out of bound access")
        return BitArray(bin="".join(self.DMem[read_address: read_address + 4])).int32

    def write_data_mem(self, address: int, write_data: int):
        # write data into byte addressable memory
        # Assuming data as 32 bit signed integer

        # Converting from int to bin
        write_data = '{:032b}'.format(write_data & 0xffffffff)

        left, right, zeroes = [], [], []

        if address <= len(self.DMem):
            left = self.DMem[:address]
        else:
            left = self.DMem
            zeroes = ["0" * 8] * (address - len(self.DMem))
        if address + 4 <= len(self.DMem):
            right = self.DMem[address + 4:]

        self.DMem = left + zeroes + [write_data[i: i + 8] for i in range(0, 32, 8)] + right

    def output_data_mem(self):
        res_path = self.io_dir + "/" + self.id + "_DMEMResult.txt"
        with open(res_path, "w") as rp:
            rp.writelines([str(data) + "\n" for data in self.DMem])


class RegisterFile(object):
    def __init__(self, io_dir):
        self.output_file = io_dir + "RFResult.txt"
        self.registers = [0x0 for _ in range(32)]

    def read_rf(self, reg_addr: int) -> int:
        return self.registers[reg_addr]

    def write_rf(self, reg_addr: int, wrt_reg_data: int):
        if reg_addr != 0:
            self.registers[reg_addr] = wrt_reg_data

    def output_rf(self, cycle):
        op = ["State of RF after executing cycle:\t" + str(cycle) + "\n"]
        op.extend(['{:032b}'.format(val & 0xffffffff) + "\n" for val in self.registers])
        if cycle == 0:
            perm = "w"
        else:
            perm = "a"
        with open(self.output_file, perm) as file:
            file.writelines(op)


class State(object):
    def __init__(self):
        self.IF = {"nop": False, "PC": 0}
        self.ID = {"nop": False, "Instr": 0}
        self.EX = {"nop": False, "Read_data1": 0, "Read_data2": 0, "Imm": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0,
                   "is_I_type": False, "rd_mem": 0,
                   "wrt_mem": 0, "alu_op": 0, "wrt_enable": 0}
        self.MEM = {"nop": False, "ALUresult": 0, "Store_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "rd_mem": 0,
                    "wrt_mem": 0, "wrt_enable": 0}
        self.WB = {"nop": False, "Wrt_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "wrt_enable": 0}
