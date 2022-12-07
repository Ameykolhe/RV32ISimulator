import json

from bitstring import BitArray


# TODO: set nop default to false and handle it in init for core class
class InsMem(object):

    def __init__(self, name, io_dir):
        self.id = name

        with open(io_dir + "/imem.txt") as im:
            self.IMem = [data.replace("\n", "") for data in im.readlines()]

    def read_instr(self, read_address: int):
        # DONE: Handle word addressing - use nearest lower multiple for 4 for address = x - x % 4
        read_address = read_address - read_address % 4
        if len(self.IMem) < read_address + 4:
            raise Exception("Instruction MEM - Out of bound access")
        return "".join(self.IMem[read_address: read_address + 4])


class DataMem(object):
    def __init__(self, name, io_dir):
        self.id = name
        self.io_dir = io_dir
        with open(io_dir + "/dmem.txt") as dm:
            self.DMem = [data.replace("\n", "") for data in dm.readlines()]
            self.DMem += ["0" * 8] * (1000 - len(self.DMem))

    def read_data(self, read_address: int) -> int:
        # read data memory
        # return 32-bit signed int value

        # DONE: Handle word addressing - use nearest lower multiple for 4 for address = x - x % 4
        read_address = read_address - read_address % 4
        if len(self.DMem) < read_address + 4:
            raise Exception("Data MEM - Out of bound access")
        return BitArray(bin="".join(self.DMem[read_address: read_address + 4])).int32

    def write_data_mem(self, address: int, write_data: int):
        # write data into byte addressable memory
        # Assuming data as 32 bit signed integer

        # Converting from int to bin

        # DONE: Handle word addressing - use nearest lower multiple for 4 for address = x - x % 4
        address = address - address % 4
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
        if self.id == 'SS':
            res_path = self.io_dir + "/output/single_stage/" + self.id + "_DMEMResult.txt"
        else:
            res_path = self.io_dir + "/output/five_stage/" + self.id + "_DMEMResult.txt"
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


class IntermediateState:

    def __init__(self):
        pass

    def set_attributes(self, **kwargs):
        self.__dict__.update(kwargs)


class IFState(IntermediateState):

    def __init__(self):
        self.nop: bool = False  # NOP operation
        self.PC: int = 0  # Program Counter
        self.instruction_count: int = 0  # count of instructions fetched - used for performance metrics
        self.halt: bool = False  # Flag - identify end of program
        super(IFState, self).__init__()

    def __str__(self):
        return "\n".join([f"IF.{key}: {val}" for key, val in self.__dict__.items()])


class IDState(IntermediateState):

    def __init__(self):
        self.nop: bool = False  # NOP operation
        self.instruction_bytes: str = ""  # Binary Instruction string
        # self.instruction_ob = None  # Decoded InstructionBase object
        self.halt: bool = False  # Flag - identify end of program
        super(IDState, self).__init__()

    def __str__(self):
        return "\n".join([f"ID.{key}: {val}" for key, val in self.__dict__.items()])


class EXState(IntermediateState):

    def __init__(self):
        self.nop: bool = False  # NOP operation
        self.instruction_ob = None  # Decoded InstructionBase object
        self.operand1: int = 0  # operand 1 for execute
        self.operand2: int = 0  # operand 2 for execute - can be rs2 or imm or forwarded data
        self.store_data: int = 0  # sw data - result of alu
        self.destination_register: int = 0  # destination register - rd
        # self.alu_operation: str = None  # not required for now
        self.read_data_mem: bool = False  # Flag - identify if we need to read from mem (MEM Stage)
        self.write_data_mem: bool = False  # Flag - identify if we need to write to mem (MEM Stage)
        self.write_back_enable: bool = False  # Flag - identify if result needs to be written back to register
        self.halt: bool = False  # Flag - identify end of program
        super(EXState, self).__init__()

    def __str__(self):
        return "\n".join([f"EX.{key}: {val}" for key, val in self.__dict__.items()])


class MEMState(IntermediateState):

    def __init__(self):
        self.nop: bool = False  # NOP operation
        self.instruction_ob = None  # Decoded InstructionBase object
        self.data_address: int = 0  # address for read / write DMEM operation
        self.store_data: int = 0  # data to be written to MEM for SW instruction or passed to WB
        self.write_register_addr: int = 0  # register to load data from MEM
        self.read_data_mem: bool = False  # Flag - identify if we need to read from mem (MEM Stage)
        self.write_data_mem: bool = False  # Flag - identify if we need to write to mem (MEM Stage)
        self.write_back_enable: bool = False  # Flag - identify if result needs to be written back to register
        self.halt: bool = False  # Flag - identify end of program
        super(MEMState, self).__init__()

    def __str__(self):
        return "\n".join([f"MEM.{key}: {val}" for key, val in self.__dict__.items()])


class WBState(IntermediateState):

    def __init__(self):
        self.nop = False  # NOP operation
        self.instruction_ob = None  # Decoded InstructionBase object
        self.store_data: int = 0  # data to be written to MEM for SW instruction
        self.write_register_addr: int = 0  # register to load data from MEM
        self.write_back_enable: bool = False  # Flag - identify if result needs to be written back to register
        self.halt: bool = False  # Flag - identify end of program
        super(WBState, self).__init__()

    def __str__(self):
        return "\n".join([f"WB.{key}: {val}" for key, val in self.__dict__.items()])


class State(object):

    def __init__(self):
        self.IF: IFState = IFState()

        self.ID = IDState()

        self.EX = EXState()

        self.MEM = MEMState()

        self.WB = WBState()

    def nop_init(self):
        self.IF.nop = False
        self.ID.nop = True
        self.EX.nop = True
        self.MEM.nop = True
        self.WB.nop = True

    def __str__(self):
        # DONE: update __str__ to make use of individual State objects
        return "\n\n".join([str(self.IF), str(self.ID), str(self.EX), str(self.MEM), str(self.WB)])
