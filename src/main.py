from NYU_RV32I_6913 import DataMem

from riscvmodel.code import decode

if __name__ == "__main__":
    data_mem = DataMem("SS", "data")
    data_mem.write_data_mem(12, "10" * 16)
    data_mem.output_data_mem()

    # inst_word = int("0b00000100000100010111001000100100", 2)
    # instruction = decode(inst_word)
    # print(instruction)
