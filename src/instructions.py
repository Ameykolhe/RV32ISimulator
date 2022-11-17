import abc
import importlib
import os

from riscvmodel.code import decode
from riscvmodel.isa import Instruction

from models import DataMem, RegisterFile


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


class ORI(InstructionBase):

    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile):
        super(ORI, self).__init__(instruction, memory, registers)
        self.rs1 = instruction.rs1
        self.rd = instruction.rd
        self.imm = instruction.imm.value

    def execute(self, *args, **kwargs):
        return self.rs1 | self.imm

    def mem(self, *args, **kwargs):
        pass

    def wb(self, *args, **kwargs):
        pass


def get_instruction_class(mnemonic: str):
    cls = getattr(importlib.import_module('instructions'), mnemonic.upper())
    if cls is None:
        raise Exception("Invalid Instruction")
    else:
        return cls


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
