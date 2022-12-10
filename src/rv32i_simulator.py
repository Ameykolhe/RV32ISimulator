import copy

from riscvmodel.code import decode, MachineDecodeError
from riscvmodel.isa import Instruction

from instructions import get_instruction_class, InstructionBase, ADDERBTYPE, ADDERJTYPE
from models import InsMem, DataMem, RegisterFile, State

# memory size, in reality, the memory size should be 2^32, but for this lab, for the space reason
# we keep it as this large number, but the memory is still 32-bit addressable.
MemSize = 1000


class Core(object):
    def __init__(self, ioDir: str, imem: InsMem, dmem: DataMem):
        self.myRF = RegisterFile(ioDir)
        self.cycle = 0
        self.halted = False
        self.ioDir = ioDir
        self.state = State()
        self.state.nop_init()
        self.nextState = State()
        self.nextState.nop_init()
        self.ext_imem: InsMem = imem
        self.ext_dmem: DataMem = dmem

    def calculate_performance_metrics(self):
        cpi = float(self.cycle) / self.state.IF.instruction_count
        ipc = 1 / cpi

        result_format = f"{self.stages} Core Performance Metrics-----------------------------\n" \
                        f"Number of cycles taken: {self.cycle}\n" \
                        f"Cycles per instruction: {cpi}\n" \
                        f"Instructions per cycle: {ipc}\n"

        write_mode = "w" if self.stages == "Single Stage" else "a"

        with open(self.ioDir + "PerformanceMetrics_Result.txt", "w") as file:
            file.write(result_format)


class SingleStageCore(Core):
    def __init__(self, io_dir: str, imem: InsMem, dmem: DataMem):
        super(SingleStageCore, self).__init__(io_dir + "/output/single_stage/SS_", imem, dmem)
        self.opFilePath = io_dir + "/output/single_stage/StateResult_SS.txt"
        self.stages = "Single Stage"

    def step(self):
        # IF
        instruction_bytes = self.ext_imem.read_instr(self.state.IF.PC)
        if instruction_bytes == "1" * 32:
            self.nextState.IF.nop = True
        else:
            self.nextState.IF.PC += 4
            self.nextState.IF.instruction_count = self.nextState.IF.instruction_count + 1

        try:
            # ID
            instruction: Instruction = decode(int(instruction_bytes, 2))
            if instruction.mnemonic in ['beq', 'bne']:
                self.nextState.IF.PC = ADDERBTYPE(instruction, self.state, self.myRF).get_pc()
            elif instruction.mnemonic == 'jal':
                self.nextState.IF.PC = ADDERJTYPE(instruction, self.state, self.myRF).get_pc()
            else:
                instruction_ob: InstructionBase = get_instruction_class(instruction.mnemonic)(instruction,
                                                                                              self.ext_dmem, self.myRF,
                                                                                              self.state,
                                                                                              self.nextState)
                # Ex
                alu_result = instruction_ob.execute()
                # Load/Store (MEM)
                mem_result = instruction_ob.mem(alu_result=alu_result)
                # WB
                wb_result = instruction_ob.wb(mem_result=mem_result, alu_result=alu_result)
        except MachineDecodeError as e:
            if "{:08x}".format(e.word) == 'ffffffff':
                pass
            else:
                raise Exception("Invalid Instruction to Decode")
        # self.halted = True
        if self.state.IF.nop:
            self.nextState.IF.instruction_count = self.nextState.IF.instruction_count + 1
            self.halted = True

        self.myRF.output_rf(self.cycle)  # dump RF
        self.printState(self.nextState, self.cycle)  # print states after executing cycle 0, cycle 1, cycle 2 ...

        # The end of the cycle and updates the current state with the values calculated in this cycle
        self.state = copy.deepcopy(self.nextState)
        # self.nextState = copy.deepcopy(self.nextState)
        self.cycle += 1

    def printState(self, state, cycle):
        printstate = ["-" * 70 + "\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.append("IF.PC: " + str(state.IF.PC) + "\n")
        printstate.append("IF.nop: " + str(state.IF.nop) + "\n")

        if (cycle == 0):
            perm = "w"
        else:
            perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)


class FiveStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(FiveStageCore, self).__init__(ioDir + "/output/five_stage/FS_", imem, dmem)
        self.opFilePath = ioDir + "/output/five_stage/StateResult_FS.txt"
        self.stages = "Five Stage"

    def print_current_instruction(self, cycle, stage, instruction):
        if issubclass(type(instruction), Instruction):
            print(f"{cycle}\t{stage}\t{instruction}")
        else:
            if all([x in ["0", "1"] for x in instruction]):
                try:
                    print(f"{cycle}\t{stage}\t{decode(int(instruction, 2))}")
                except MachineDecodeError as e:
                    print(f"{cycle}\t{stage}\tHalt")
            else:
                print(f"{cycle}\t{stage}\t{instruction}")

    def step(self):
        # Your implementation

        # --------------------- WB stage ----------------------
        if not self.state.WB.nop:
            self.print_current_instruction(self.cycle, "WB", self.state.WB.instruction_ob.instruction)

            self.state, self.nextState, self.ext_dmem, self.myRF, _ = self.state.WB.instruction_ob.wb(
                state=self.state,
                nextState=self.nextState,
                registers=self.myRF,
                memory=self.ext_dmem)
        else:
            self.print_current_instruction(self.cycle, "WB", "nop")


        # --------------------- MEM stage ---------------------
        if not self.state.MEM.nop:
            self.print_current_instruction(self.cycle, "MEM", self.state.MEM.instruction_ob.instruction)

            self.state, self.nextState, self.ext_dmem, self.myRF, _ = self.state.MEM.instruction_ob.mem(
                state=self.state,
                nextState=self.nextState,
                registers=self.myRF,
                memory=self.ext_dmem)
        else:
            self.nextState.WB.nop = True
            self.print_current_instruction(self.cycle, "MEM", "nop")


        # --------------------- EX stage ----------------------
        if not self.state.EX.nop:
            self.print_current_instruction(self.cycle, "EX", self.state.EX.instruction_ob.instruction)

            self.state, self.nextState, self.ext_dmem, self.myRF, _ = self.state.EX.instruction_ob.execute(
                state=self.state, nextState=self.nextState, registers=self.myRF, memory=self.ext_dmem)
        else:
            self.nextState.MEM.nop = True
            self.print_current_instruction(self.cycle, "EX", "nop")

        # --------------------- ID stage ----------------------
        if not self.state.ID.nop:
            self.print_current_instruction(self.cycle, "ID", self.state.ID.instruction_bytes)
            try:
                instruction = decode(int(self.state.ID.instruction_bytes, 2))
                instruction_ob: InstructionBase = get_instruction_class(instruction.mnemonic)(instruction,
                                                                                              self.ext_dmem,
                                                                                              self.myRF,
                                                                                              self.state,
                                                                                              self.nextState)
                self.state, self.nextState, self.ext_dmem, self.myRF, _ = instruction_ob.decode(state=self.state,
                                                                                                nextState=self.nextState,
                                                                                                registers=self.myRF,
                                                                                                memory=self.ext_dmem)
            except MachineDecodeError as e:
                if "{:08x}".format(e.word) == 'ffffffff':
                    self.nextState.ID.halt = True
                else:
                    raise Exception("Invalid Instruction to Decode")
        else:
            self.nextState.EX.nop = True
            self.print_current_instruction(self.cycle, "ID", "nop")

        # --------------------- IF stage ----------------------
        if not self.state.IF.nop:
            self.nextState.ID.instruction_bytes = self.ext_imem.read_instr(self.state.IF.PC)
            self.nextState.ID.nop = False
            if self.nextState.ID.instruction_bytes == "1" * 32:
                self.nextState.ID.nop = True
                self.nextState.IF.nop = True
            else:
                self.nextState.IF.PC = self.state.IF.PC + 4
                self.nextState.IF.instruction_count = self.state.IF.instruction_count + 1

            self.print_current_instruction(self.cycle, "IF", self.nextState.ID.instruction_bytes)
        else:
            self.nextState.ID.nop = True
            self.print_current_instruction(self.cycle, "IF", "nop")

        if (self.state.IF.halt or self.state.IF.nop) and (self.state.ID.halt or self.state.ID.nop) and (
                self.state.EX.halt or self.state.EX.nop) and (self.state.MEM.halt or self.state.MEM.nop) and (
                self.state.WB.halt or self.state.WB.nop):
            self.halted = True
            self.print_current_instruction(self.cycle, "--", "End of Simulation")

        self.myRF.output_rf(self.cycle)  # dump RF
        self.printState(self.nextState, self.cycle)  # print states after executing cycle 0, cycle 1, cycle 2 ...

        self.state = copy.deepcopy(self.nextState)
        self.cycle += 1

    def printState(self, state, cycle):
        print_state = "\n" + "-" * 70 + "\n" + "State after executing cycle: " + str(cycle) + "\n\n"
        print_state += str(state)

        if (cycle == 0):
            perm = "w"
        else:
            perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.write(print_state)


if __name__ == "__main__":
    pass
