import argparse
import os

from models import DataMem, InsMem
from rv32i_simulator import SingleStageCore, FiveStageCore


def main():
    # parse arguments for input file location
    parser = argparse.ArgumentParser(description='RV32I processor')
    parser.add_argument('--iodir', default="", type=str, help='Directory containing the input files.')
    args = parser.parse_args()

    ioDir = os.path.abspath(args.iodir)
    print("IO Directory:", ioDir)

    imem = InsMem("Imem", ioDir)
    dmem_ss = DataMem("SS", ioDir)
    dmem_fs = DataMem("FS", ioDir)

    ssCore = SingleStageCore(ioDir, imem, dmem_ss)
    fsCore = FiveStageCore(ioDir, imem, dmem_fs)

    while True:
        if not ssCore.halted:
            ssCore.step()

        if not fsCore.halted:
            fsCore.step()

        if ssCore.halted and fsCore.halted:
            break

    # dump SS and FS data mem.
    dmem_ss.output_data_mem()
    dmem_fs.output_data_mem()


if __name__ == "__main__":
    # data_mem = DataMem("SS", "data")
    # data_mem.write_data_mem(12, "10" * 16)
    # data_mem.output_data_mem()
    #
    # inst_word = int("0b00000100000100010111001000100100", 2)
    # instruction = decode(inst_word)
    # print(instruction)

    main()
