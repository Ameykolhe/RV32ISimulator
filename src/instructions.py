import abc
import importlib
import os

from riscvmodel.code import decode
from riscvmodel.isa import Instruction

from models import DataMem, RegisterFile, State


class InstructionBase(metaclass=abc.ABCMeta):

    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile):
        self.instruction = instruction
        self.memory = memory
        self.registers = registers

    @abc.abstractmethod
    def execute(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def mem(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def wb(self, *args, **kwargs):
        pass


class InstructionRBase(InstructionBase):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile):
        super(InstructionRBase, self).__init__(instruction, memory, registers)
        self.rs1 = instruction.rs1
        self.rs2 = instruction.rs2
        self.rd = instruction.rd

    @abc.abstractmethod
    def execute(self, *args, **kwargs):
        pass

    def mem(self, *args, **kwargs):
        pass

    def wb(self, *args, **kwargs):
        data = kwargs['alu_result']
        return self.registers.write_rf(self.rd, data)


class InstructionIBase(InstructionBase):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile):
        super(InstructionIBase, self).__init__(instruction, memory, registers)
        self.rs1 = instruction.rs1
        self.rd = instruction.rd
        self.imm = instruction.imm.value

    @abc.abstractmethod
    def execute(self, *args, **kwargs):
        pass

    def mem(self, *args, **kwargs):
        pass

    def wb(self, *args, **kwargs):
        data = kwargs['alu_result']
        return self.registers.write_rf(self.rd, data)


class InstructionSBase(InstructionBase):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile):
        super(InstructionSBase, self).__init__(instruction, memory, registers)
        self.rs1 = instruction.rs1
        self.rs2 = instruction.rs2
        self.imm = instruction.imm.value

    @abc.abstractmethod
    def execute(self, *args, **kwargs):
        pass

    def mem(self, *args, **kwargs):
        address = kwargs['alu_result']
        self.memory.write_data_mem(address, '{:032b}'.format(self.registers.read_rf(self.rs2)))

    def wb(self, *args, **kwargs):
        pass


class InstructionBBase(InstructionBase):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile):
        super(InstructionBBase, self).__init__(instruction, memory, registers)
        self.rs1 = instruction.rs1
        self.rs2 = instruction.rs2
        self.imm = instruction.imm.value

    @abc.abstractmethod
    def execute(self, *args, **kwargs):
        pass

    def mem(self, *args, **kwargs):
        address = kwargs['alu_result']
        self.memory.write_data_mem(address, '{:032b}'.format(self.registers.read_rf(self.rs2)))

    def wb(self, *args, **kwargs):
        pass


class InstructionJBase(InstructionBase):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile):
        super(InstructionSBase, self).__init__(instruction, memory, registers)
        self.rs1 = instruction.rs1
        self.rs2 = instruction.rs2
        self.imm = instruction.imm.value

    @abc.abstractmethod
    def execute(self, *args, **kwargs):
        pass

    def mem(self, *args, **kwargs):
        address = kwargs['alu_result']
        self.memory.write_data_mem(address, '{:032b}'.format(self.registers.read_rf(self.rs2)))

    def wb(self, *args, **kwargs):
        pass


class ADD(InstructionRBase):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile):
        super(ADD, self).__init__(instruction, memory, registers)

    def execute(self, *args, **kwargs):
        return self.registers.read_rf(self.rs1) + self.registers.read_rf(self.rs2)


class SUB(InstructionRBase):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile):
        super(SUB, self).__init__(instruction, memory, registers)

    def execute(self, *args, **kwargs):
        return self.registers.read_rf(self.rs1) - self.registers.read_rf(self.rs2)


class XOR(InstructionRBase):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile):
        super(XOR, self).__init__(instruction, memory, registers)

    def execute(self, *args, **kwargs):
        return self.registers.read_rf(self.rs1) ^ self.registers.read_rf(self.rs2)


class OR(InstructionRBase):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile):
        super(OR, self).__init__(instruction, memory, registers)

    def execute(self, *args, **kwargs):
        return self.registers.read_rf(self.rs1) | self.registers.read_rf(self.rs2)


class AND(InstructionRBase):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile):
        super(AND, self).__init__(instruction, memory, registers)

    def execute(self, *args, **kwargs):
        return self.registers.read_rf(self.rs1) & self.registers.read_rf(self.rs2)


class ADDI(InstructionIBase):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile):
        super(ADDI, self).__init__(instruction, memory, registers)

    def execute(self, *args, **kwargs):
        return self.registers.read_rf(self.rs1) + self.imm


class XORI(InstructionIBase):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile):
        super(XORI, self).__init__(instruction, memory, registers)

    def execute(self, *args, **kwargs):
        return self.registers.read_rf(self.rs1) ^ self.imm


class ORI(InstructionIBase):

    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile):
        super(ORI, self).__init__(instruction, memory, registers)

    def execute(self, *args, **kwargs):
        return self.registers.read_rf(self.rs1) | self.imm


class ANDI(InstructionIBase):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile):
        super(ANDI, self).__init__(instruction, memory, registers)

    def execute(self, *args, **kwargs):
        return self.registers.read_rf(self.rs1) & self.imm


class LW(InstructionIBase):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile):
        super(LW, self).__init__(instruction, memory, registers)

    def execute(self, *args, **kwargs):
        return self.registers.read_rf(self.rs1) + self.imm

    def mem(self, *args, **kwargs):
        address = kwargs['alu_result']
        return self.memory.read_data(address)

    def wb(self, *args, **kwargs):
        data = kwargs['mem_result']
        return self.registers.write_rf(self.rd, data)


class ADDER:
    def __init__(self, instruction: Instruction, nextState: State(), registers: RegisterFile):
        self.instruction = instruction
        self.nextState = nextState
        self.registers = registers
        self.rs1 = instruction.rs1
        self.rs2 = instruction.rs2
        self.imm = instruction.imm.value

    def get_pc(self, *args, **kwargs):
        if self.instruction.mnemonic == 'beq':
            if self.registers.read_rf(self.rs1) == self.registers.read_rf(self.rs2):
                return self.nextState.IF["PC"] - 4 + self.imm
            else:
                return self.nextState.IF["PC"]
        else:
            if self.registers.read_rf(self.rs1) != self.registers.read_rf(self.rs2):
                return self.nextState.IF["PC"] - 4 + self.imm
            else:
                return self.nextState.IF["PC"]

class SW(InstructionSBase):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile):
        super(SW, self).__init__(instruction, memory, registers)

    def execute(self, *args, **kwargs):
        return self.registers.read_rf(self.rs1) + self.imm


def get_instruction_class(mnemonic: str):
    try:
        cls = getattr(importlib.import_module('instructions'), mnemonic.upper())
        return cls
    except AttributeError as e:
        raise Exception("Invalid Instruction")


def main():
    instruction: Instruction = decode(int("01000100010000100110101110010011", 2))
    ioDir = os.path.abspath("./data")
    dmem_ss = DataMem("SS", ioDir)
    registers = RegisterFile(ioDir)

    cls = get_instruction_class("ori")
    instruction_ob = cls(instruction, dmem_ss, registers)
    result = instruction_ob.execute("arg1", "arg2", kwarg1="val_kwarg1", kwarg2="val_kwarg2")


if __name__ == "__main__":
    main()
