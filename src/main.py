import argparse
import os

from models import DataMem, InsMem
from rv32i_simulator import SingleStageCore, FiveStageCore


def main():
    # parse arguments for input file location
    parser = argparse.ArgumentParser(description='RV32I processor')
    parser.add_argument('--iodir', default="", type=str, help='Directory containing the input files.')
    parser.add_argument("--testpath", default="", type=str, help="Test Case Path")
    args = parser.parse_args()
    test_case_number = 1

    ioDir = os.path.abspath(args.iodir)
    ioTest = os.path.abspath(args.testpath)

    print("IO Directory:", ioDir)
    print("Test Path:", ioTest)

    if ioTest == "":
        imem = InsMem("Imem", ioDir, ioTest=ioTest, tc=test_case_number)
        dmem_ss = DataMem("SS", ioDir, ioTest=ioTest, tc=test_case_number)
        dmem_fs = DataMem("FS", ioDir, ioTest=ioTest, tc=test_case_number)
    else:
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

    # dumps SS and DS Performance
    ssCore.calculate_performance_metrics()
    fsCore.calculate_performance_metrics()


if __name__ == "__main__":
    # data_mem = DataMem("SS", "data")
    # data_mem.write_data_mem(12, "10" * 16)
    # data_mem.output_data_mem()
    #
    # inst_word = int("0b00000100000100010111001000100100", 2)
    # instruction = decode(inst_word)
    # print(instruction)

    main()
