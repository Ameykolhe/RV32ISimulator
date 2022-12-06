import abc
import importlib
import os
from abc import ABC

from riscvmodel.code import decode
from riscvmodel.isa import Instruction

from models import DataMem, RegisterFile, State, EXState, WBState, MEMState


# TODO:
#   1. NOP Carry forwarding
#   2. Halt logic
#   3. Hazard Handling
#   4. Handle B and J type instructions

class InstructionBase(metaclass=abc.ABCMeta):

    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile, state: State,
                 nextState: State):
        self.instruction = instruction
        self.memory = memory
        self.registers = registers
        self.state = state
        self.nextState = nextState
        self.stages = self.memory.id

    def decode_ss(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def execute_ss(self, *args, **kwargs):
        pass

    def mem_ss(self, *args, **kwargs):
        pass

    def wb_ss(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def decode_fs(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def execute_fs(self, *args, **kwargs):
        pass

    def mem_fs(self, *args, **kwargs):
        wb_state = WBState()
        wb_state.set_attributes(
            instruction_ob=self.state.MEM.instruction_ob,
            store_data=self.state.MEM.store_data,
            write_register_addr=self.state.MEM.write_register_addr,
            write_back_enable=self.state.MEM.write_back_enable
        )
        self.nextState.WB = wb_state

    def wb_fs(self, *args, **kwargs):
        if self.state.WB.write_back_enable:
            self.registers.write_rf(self.state.WB.write_register_addr, self.state.WB.store_data)

    def decode(self, *args, **kwargs):
        if self.stages == "SS":
            return self.decode_ss(*args, **kwargs)
        else:
            return self.decode_fs(*args, **kwargs)

    def execute(self, *args, **kwargs):
        if self.stages == "SS":
            return self.execute_ss(*args, **kwargs)
        else:
            return self.execute_fs(*args, **kwargs)

    def mem(self, *args, **kwargs):
        if self.stages == "SS":
            return self.mem_ss(*args, **kwargs)
        else:
            return self.mem_fs(*args, **kwargs)

    def wb(self, *args, **kwargs):
        if self.stages == "SS":
            return self.wb_ss(*args, **kwargs)
        else:
            return self.wb_fs(*args, **kwargs)


class InstructionRBase(InstructionBase, ABC):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile, state: State,
                 nextState: State):
        super(InstructionRBase, self).__init__(instruction, memory, registers, state, nextState)
        self.rs1 = instruction.rs1
        self.rs2 = instruction.rs2
        self.rd = instruction.rd

    def wb_ss(self, *args, **kwargs):
        data = kwargs['alu_result']
        return self.registers.write_rf(self.rd, data)

    def decode_fs(self, *args, **kwargs):
        ex_state = EXState()

        # TODO: Handle Hazards
        #   set nop for EX state
        #   will be applicable in R, I, S, B, J type instructions
        # EX to EX

        # MEM to EX

        ex_state.set_attributes(
            instruction_ob=self,
            nop=self.state.ID.nop,
            operand1=self.registers.read_rf(self.rs1),
            operand2=self.registers.read_rf(self.rs2),
            destination_register=self.rd,
            write_back_enable=True
        )
        self.nextState.EX = ex_state

    def execute_fs(self, *args, **kwargs):
        mem_state = MEMState()
        mem_state.set_attributes(
            instruction_ob=self,
            nop=self.state.EX.nop,
            write_register_addr=self.state.EX.destination_register,
            write_back_enable=True
        )
        self.nextState.MEM = mem_state


class InstructionIBase(InstructionBase, ABC):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile, state: State,
                 nextState: State):
        super(InstructionIBase, self).__init__(instruction, memory, registers, state, nextState)
        self.rs1 = instruction.rs1
        self.rd = instruction.rd
        self.imm = instruction.imm.value

    def wb_ss(self, *args, **kwargs):
        data = kwargs['alu_result']
        return self.registers.write_rf(self.rd, data)

    def decode_fs(self, *args, **kwargs):
        ex_state = EXState()
        ex_state.set_attributes(
            instruction_ob=self,
            nop=self.state.ID.nop,
            operand1=self.registers.read_rf(self.rs1),
            operand2=self.imm,
            destination_register=self.rd,
            write_back_enable=True
        )
        self.nextState.EX = ex_state

    def execute_fs(self, *args, **kwargs):
        mem_state = MEMState()
        mem_state.set_attributes(
            instruction_ob=self,
            nop=self.state.EX.nop,
            write_register_addr=self.state.EX.destination_register,
            write_back_enable=True
        )
        self.nextState.MEM = mem_state


class InstructionSBase(InstructionBase, ABC):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile, state: State,
                 nextState: State):
        super(InstructionSBase, self).__init__(instruction, memory, registers, state, nextState)
        self.rs1 = instruction.rs1
        self.rs2 = instruction.rs2
        self.imm = instruction.imm.value

    def mem_ss(self, *args, **kwargs):
        address = kwargs['alu_result']
        data = self.registers.read_rf(self.rs2)
        self.memory.write_data_mem(address, data)

    def decode_fs(self, *args, **kwargs):
        ex_state = EXState()
        ex_state.set_attributes(
            instruction_ob=self,
            nop=self.state.ID.nop,
            operand1=self.registers.read_rf(self.rs1),
            operand2=self.imm,
            destination_register=self.rs2,
            write_data_mem=True
        )
        self.nextState.EX = ex_state

    def execute_fs(self, *args, **kwargs):
        mem_state = MEMState()
        mem_state.set_attributes(
            instruction_ob=self,
            nop=self.state.EX.nop,
            data_address=self.state.EX.operand1 + self.state.EX.operand1,
            store_data=self.state.EX.store_data,
            write_data_mem=True
        )
        self.nextState.MEM = mem_state

    def mem_fs(self, *args, **kwargs):
        if self.state.MEM.write_data_mem:
            self.memory.write_data_mem(self.state.MEM.data_address, self.state.MEM.store_data)
        wb_state = WBState()
        wb_state.set_attributes(
            instruction_ob=self,

        )
        self.nextState.WB = wb_state


class InstructionBBase(InstructionBase, ABC):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile, state: State,
                 nextState: State):
        super(InstructionBBase, self).__init__(instruction, memory, registers, state, nextState)
        self.rs1 = instruction.rs1
        self.rs2 = instruction.rs2
        self.imm = instruction.imm.value

    def mem_ss(self, *args, **kwargs):
        address = kwargs['alu_result']
        self.memory.write_data_mem(address, '{:032b}'.format(self.registers.read_rf(self.rs2)))

    def decode_fs(self, *args, **kwargs):
        # self.nextState.ID["rs1"] = self.rs1
        # self.nextState.ID["rs2"] = self.rs2
        # self.nextState.ID["imm"] = self.imm
        # self.nextState.ID["rs1_data"] = self.registers.read_rf(self.rs1)
        # self.nextState.ID["rs2_data"] = self.registers.read_rf(self.rs2)
        pass


class InstructionJBase(InstructionBase, ABC):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile, state: State,
                 nextState: State):
        super(InstructionJBase, self).__init__(instruction, memory, registers, state, nextState)
        self.rs1 = instruction.rs1
        self.rs2 = instruction.rs2
        self.imm = instruction.imm.value

    def mem_ss(self, *args, **kwargs):
        address = kwargs['alu_result']
        self.memory.write_data_mem(address, '{:032b}'.format(self.registers.read_rf(self.rs2)))

    def decode_fs(self, *args, **kwargs):
        # self.nextState.ID["rs1"] = self.rs1
        # self.nextState.ID["rs2"] = self.rs2
        # self.nextState.ID["imm"] = self.imm
        # self.nextState.ID["rs1_data"] = self.registers.read_rf(self.rs1)
        # self.nextState.ID["rs2_data"] = self.registers.read_rf(self.rs2)
        pass


class ADD(InstructionRBase):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile, state: State,
                 nextState: State):
        super(ADD, self).__init__(instruction, memory, registers, state, nextState)

    def execute_ss(self, *args, **kwargs):
        return self.registers.read_rf(self.rs1) + self.registers.read_rf(self.rs2)

    def execute_fs(self, *args, **kwargs):
        super(ADD, self).execute_fs()
        self.nextState.MEM.store_data = self.state.EX.operand1 + self.state.EX.operand2


class SUB(InstructionRBase):

    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile, state: State,
                 nextState: State):
        super(SUB, self).__init__(instruction, memory, registers, state, nextState)

    def execute_ss(self, *args, **kwargs):
        return self.registers.read_rf(self.rs1) - self.registers.read_rf(self.rs2)

    def execute_fs(self, *args, **kwargs):
        super(SUB, self).execute_fs()
        self.nextState.MEM.store_data = self.state.EX.operand1 - self.state.EX.operand2


class XOR(InstructionRBase):

    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile, state: State,
                 nextState: State):
        super(XOR, self).__init__(instruction, memory, registers, state, nextState)

    def execute_ss(self, *args, **kwargs):
        return self.registers.read_rf(self.rs1) ^ self.registers.read_rf(self.rs2)

    def execute_fs(self, *args, **kwargs):
        super(XOR, self).execute_fs()
        self.nextState.MEM.store_data = self.state.EX.operand1 ^ self.state.EX.operand2


class OR(InstructionRBase):

    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile, state: State,
                 nextState: State):
        super(OR, self).__init__(instruction, memory, registers, state, nextState)

    def execute_ss(self, *args, **kwargs):
        return self.registers.read_rf(self.rs1) | self.registers.read_rf(self.rs2)

    def execute_fs(self, *args, **kwargs):
        super(OR, self).execute_fs()
        self.nextState.MEM.store_data = self.state.EX.operand1 | self.state.EX.operand2


class AND(InstructionRBase):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile, state: State,
                 nextState: State):
        super(AND, self).__init__(instruction, memory, registers, state, nextState)

    def execute_ss(self, *args, **kwargs):
        return self.registers.read_rf(self.rs1) & self.registers.read_rf(self.rs2)

    def execute_fs(self, *args, **kwargs):
        super(AND, self).execute_fs()
        self.nextState.MEM.store_data = self.state.EX.operand1 & self.state.EX.operand2


class ADDI(InstructionIBase):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile, state: State,
                 nextState: State):
        super(ADDI, self).__init__(instruction, memory, registers, state, nextState)

    def execute_ss(self, *args, **kwargs):
        return self.registers.read_rf(self.rs1) + self.imm

    def execute_fs(self, *args, **kwargs):
        super(ADDI, self).execute_fs()
        self.nextState.MEM.store_data = self.state.EX.operand1 + self.state.EX.operand2


class XORI(InstructionIBase):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile, state: State,
                 nextState: State):
        super(XORI, self).__init__(instruction, memory, registers, state, nextState)

    def execute_ss(self, *args, **kwargs):
        return self.registers.read_rf(self.rs1) ^ self.imm

    def execute_fs(self, *args, **kwargs):
        super(XORI, self).execute_fs()
        self.nextState.MEM.store_data = self.state.EX.operand1 ^ self.state.EX.operand2


class ORI(InstructionIBase):

    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile, state: State,
                 nextState: State):
        super(ORI, self).__init__(instruction, memory, registers, state, nextState)

    def execute_ss(self, *args, **kwargs):
        return self.registers.read_rf(self.rs1) | self.imm

    def execute_fs(self, *args, **kwargs):
        super(ORI, self).execute_fs()
        self.nextState.MEM.store_data = self.state.EX.operand1 | self.state.EX.operand2


class ANDI(InstructionIBase):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile, state: State,
                 nextState: State):
        super(ANDI, self).__init__(instruction, memory, registers, state, nextState)

    def execute_ss(self, *args, **kwargs):
        return self.registers.read_rf(self.rs1) & self.imm

    def execute_fs(self, *args, **kwargs):
        super(ANDI, self).execute_fs()
        self.nextState.MEM.store_data = self.state.EX.operand1 & self.state.EX.operand2


class LW(InstructionIBase):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile, state: State,
                 nextState: State):
        super(LW, self).__init__(instruction, memory, registers, state, nextState)

    def execute_ss(self, *args, **kwargs):
        return self.registers.read_rf(self.rs1) + self.imm

    def mem_ss(self, *args, **kwargs):
        address = kwargs['alu_result']
        return self.memory.read_data(address)

    def wb_ss(self, *args, **kwargs):
        data = kwargs['mem_result']
        return self.registers.write_rf(self.rd, data)

    def execute_fs(self, *args, **kwargs):
        super(ADD, self).execute_fs()
        self.nextState.MEM.set_attributes(
            data_address=self.state.EX.operand1 + self.state.EX.operand2,
            read_data_mem=True
        )


class SW(InstructionSBase):
    def __init__(self, instruction: Instruction, memory: DataMem, registers: RegisterFile, state: State,
                 nextState: State):
        super(SW, self).__init__(instruction, memory, registers, state, nextState)

    def execute_ss(self, *args, **kwargs):
        return self.registers.read_rf(self.rs1) + self.imm

    def execute_fs(self, *args, **kwargs):
        self.nextState.EX["alu_result"] = self.state.ID["rs1_data"] + self.state.ID["imm"]


class ADDERBTYPE:
    def __init__(self, instruction: Instruction, state: State(), registers: RegisterFile):
        self.instruction = instruction
        self.state = state
        self.registers = registers
        self.rs1 = instruction.rs1
        self.rs2 = instruction.rs2
        self.imm = instruction.imm.value

    def get_pc(self, *args, **kwargs):
        if self.instruction.mnemonic == 'beq':
            if self.registers.read_rf(self.rs1) == self.registers.read_rf(self.rs2):
                return self.state.IF["PC"] + self.imm
            else:
                return self.state.IF["PC"] + 4
        else:
            if self.registers.read_rf(self.rs1) != self.registers.read_rf(self.rs2):
                return self.state.IF["PC"] + self.imm
            else:
                return self.state.IF["PC"] + 4


class ADDERJTYPE:
    def __init__(self, instruction: Instruction, state: State(), registers: RegisterFile):
        self.instruction = instruction
        self.state = state
        self.registers = registers
        self.rd = instruction.rd
        self.imm = instruction.imm.value

    def get_pc(self, *args, **kwargs):
        self.registers.write_rf(self.rd, self.state.IF["PC"] + 4)
        return self.state.IF["PC"] + self.imm


def get_instruction_class(mnemonic: str):
    try:
        if mnemonic == "lb":
            mnemonic = "lw"
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
