import os
import argparse


class IMEM(object):
    def __init__(self, iodir):
        self.size = pow(2, 16)  # Can hold a maximum of 2^16 instructions.
        self.filepath = os.path.abspath(os.path.join(iodir, "Code.asm"))
        self.instructions = []

        try:
            with open(self.filepath, 'r') as insf:
                self.instructions = [instruction.split('#')[0].strip() for instruction in insf.readlines() if
                                     not (instruction.startswith('#') or instruction.strip() == '')]
            print("IMEM - Instructions loaded from file:", self.filepath)
        except:
            print("IMEM - ERROR: Couldn't open file in path:", self.filepath)

    def Read(self, idx):  # Use this to read from IMEM.
        if idx < self.size:
            return self.instructions[idx]
        else:
            print("IMEM - ERROR: Invalid memory access at index: ", idx, " with memory size: ", self.size)


class DMEM(object):
    # Word addressible - each address contains 32 bits.
    def __init__(self, name, iodir, addressLen):
        self.name = name
        self.size = pow(2, addressLen)
        self.min_value = -pow(2, 31)
        self.max_value = pow(2, 31) - 1
        self.ipfilepath = os.path.abspath(os.path.join(iodir, name + ".txt"))
        self.opfilepath = os.path.abspath(os.path.join(iodir, name + "OP.txt"))
        self.data = []

        try:
            with open(self.ipfilepath, 'r') as ipf:
                self.data = [int(line.strip()) for line in ipf.readlines()]
            print(self.name, "- Data loaded from file:", self.ipfilepath)
            # print(self.name, "- Data:", self.data)
            self.data.extend([0x0 for _ in range(self.size - len(self.data))])  # Initialize the remaining as zeroes
        except:
            print(self.name, "- ERROR: Couldn't open input file in path:", self.ipfilepath)

    def Read(self, idx):  # Use this to read from DMEM.
        if idx < self.size:
            return self.data[idx]
        else:
            print("Error : Out of bounds exception")

    def Write(self, idx, val):  # Use this to write into DMEM.
        if idx < self.size:
            self.data[idx] = val
        else:
            print("Error : Out of bounds exception")

    def dump(self):
        try:
            with open(self.opfilepath, 'w') as opf:
                lines = [str(data) + '\n' for data in self.data]
                opf.writelines(lines)
            print(self.name, "- Dumped data into output file in path:", self.opfilepath)
        except:
            print(self.name, "- ERROR: Couldn't open output file in path:", self.opfilepath)


class RegisterFile(object):
    def __init__(self, name, count, length=1, size=32):
        self.name = name
        self.reg_count = count
        self.vec_length = length  # Number of 32 bit words in a register.
        self.reg_bits = size
        self.min_value = -pow(2, self.reg_bits - 1)
        self.max_value = pow(2, self.reg_bits - 1) - 1
        self.registers = [[0x0 for _ in range(self.vec_length)] for r in
                          range(self.reg_count)]  # list of lists of integers

    def Read(self, idx=0):
        if idx < self.reg_count:
            val = self.registers[idx]
            if len(val) != 1:
                return self.registers[idx]
            else:
                return self.registers[idx][0]
        else:
            print("Error : Out of bounds exception")

    def Write(self, idx, val):
        if idx < self.reg_count:
            if type(val) == int:
                self.registers[idx] = [val]
            else:
                self.registers[idx] = val
        else:
            print("Error : Out of bounds exception")

    def dump(self, iodir):
        opfilepath = os.path.abspath(os.path.join(iodir, self.name + ".txt"))
        try:
            with open(opfilepath, 'w') as opf:
                row_format = "{:<13}" * self.vec_length
                lines = [row_format.format(*[str(i) for i in range(self.vec_length)]) + "\n",
                         '-' * (self.vec_length * 13) + "\n"]
                lines += [row_format.format(*[str(val) for val in data]) + "\n" for data in self.registers]
                opf.writelines(lines)
            print(self.name, "- Dumped data into output file in path:", opfilepath)
        except:
            print(self.name, "- ERROR: Couldn't open output file in path:", opfilepath)


class Core:
    def __init__(self, imem, sdmem, vdmem):
        self.imem = imem
        self.sdmem = sdmem
        self.vdmem = vdmem
        self.ins = Instructionref(self)
        self.RFs = {"SRF": RegisterFile("SRF", 8),
                    "VRF": RegisterFile("VRF", 8, 64),
                    "VMR": RegisterFile("VMR", 1, 64, 1),
                    "VLG": RegisterFile("VLG", 1, 1)}
        self.pc = 0
        self.mvl = 64
        self.RFs.get("VLG").Write(0, self.mvl)
        self.RFs.get("VMR").Write(0, [1] * 64)
        self.resolvedCode = []
        print("Core Initialized")

    def run(self):
        print("Simulation started")
        while True:
            try:
                temp = self.imem.Read(self.pc)
                ret, resolvedCode = self.ins.execute(temp)
            except IndexError:
                return 0

            if ret == 1:
                self.resolvedCode.append(resolvedCode)
                print("Instruction being executed...")
            elif ret == 0:
                break

    def dumpRegs(self, iodir):
        for rf in self.RFs.values():
            rf.dump(iodir)

    def dumpResolvedCode(self, iodir, name="resolvedCode"):
        path = os.path.abspath(os.path.join(iodir, name + ".txt"))
        try:
            with open(path, 'w') as opf:
                lines = [str(data) + '\n' for data in self.resolvedCode]
                opf.writelines(lines)
            print(name, "- Resolved Code dumped into ", path)
        except:
            print(name, "- ERROR: Couldn't open output file ", path)


class Instructionref:
    def __init__(self, core):
        self.core = core
        self.ins = {
            "ADDVV": self.ADDVV,
            "SUBVV": self.SUBVV,
            "MULVV": self.MULVV,
            "DIVVV": self.DIVVV,
            "SEQVV": self.SEQVV,
            "SNEVV": self.SNEVV,
            "SGTVV": self.SGTVV,
            "SLTVV": self.SLTVV,
            "SGEVV": self.SGEVV,
            "SLEVV": self.SLEVV,
            "ADDVS": self.ADDVS,
            "SUBVS": self.SUBVS,
            "MULVS": self.MULVS,
            "DIVVS": self.DIVVS,
            "SEQVS": self.SEQVS,
            "SNEVS": self.SNEVS,
            "SGTVS": self.SGTVS,
            "SLTVS": self.SLTVS,
            "SGEVS": self.SGEVS,
            "SLEVS": self.SLEVS,
            "POP": self.POP,
            "MTCL": self.MTCL,
            "MFCL": self.MFCL,
            "LV": self.LV,
            "SV": self.SV,
            "LS": self.LS,
            "SS": self.SS,
            "LVWS": self.LVWS,
            "SVWS": self.SVWS,
            "LVI": self.LVI,
            "SVI": self.SVI,
            "ADD": self.ADD,
            "SUB": self.SUB,
            "SRA": self.SRA,
            "SRL": self.SRL,
            "SLL": self.SLL,
            "AND": self.AND,
            "OR": self.OR,
            "XOR": self.XOR,
            "BEQ": self.BEQ,
            "BNE": self.BNE,
            "BGT": self.BGT,
            "BLT": self.BLT,
            "BGE": self.BGE,
            "BLE": self.BLE,
            "CVM": self.CVM,
            "HALT": self.HALT,
        }
        self.operands = []

    def execute(self, instruction):
        self.operands = instruction.split()
        instr = self.ins.get(self.operands[0], self.Default)()
        return instr

    # region Memory Access Instructions

    def LV(self):
        ins, op1, op2 = (self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]))
        op2_val = self.core.RFs.get("SRF").Read(op2)
        veclen = self.core.RFs.get("VLG").Read()
        op1_val_final = [self.core.vdmem.Read(op2_val + i) for i in range(veclen)]
        self.core.RFs.get("VRF").Write(op1, self.mask(op1, op1_val_final, veclen))
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "

        resolvedCode += "("
        for i in range(veclen):
            resolvedCode += str(op2_val + i) + ","

        resolvedCode = resolvedCode[:-1] + ")"
        return 1, resolvedCode.strip()

    def SV(self):
        ins, op1, op2 = (self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]))
        op2_val = self.core.RFs.get("SRF").Read(op2)
        op1_val = self.core.RFs.get("VRF").Read(op1)
        veclen = self.core.RFs.get("VLG").Read()
        mask_reg = self.core.RFs.get("VMR").Read()
        for i in range(op2_val, op2_val + veclen):
            if mask_reg[i - op2_val]:
                self.core.vdmem.Write(i, op1_val[i - op2_val])
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        resolvedCode += "("
        for i in range(veclen):
            resolvedCode += str(op2_val + i) + ","
        resolvedCode = resolvedCode[:-1] + ")"
        return 1, resolvedCode.strip()

    def LS(self):
        ins, op1, op2, imm = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3]))
        op2_val = self.core.RFs.get("SRF").Read(op2)
        op1_val = self.core.sdmem.Read(op2_val + imm)
        self.core.RFs.get("SRF").Write(op1, op1_val)
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def SS(self):
        ins, op1, op2, imm = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3]))
        op1_val = self.core.RFs.get("SRF").Read(op1)
        self.core.sdmem.Write(op2 + imm, op1_val)
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def LVWS(self):
        ins, op1, op2, op1 = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3][2:]))
        op2_val = self.core.RFs.get("SRF").Read(op2)
        op1_val = self.core.RFs.get("SRF").Read(op1)
        veclen = self.core.RFs.get("VLG").Read()
        op1_val_final = [self.core.vdmem.Read(op2_val + i * op1_val) for i in range(veclen)]
        self.core.RFs.get("VRF").Write(op1, self.mask(op1, op1_val_final, veclen))
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        resolvedCode += "("
        for i in range(veclen):
            resolvedCode += str(op2_val + i * op1_val) + ","
        resolvedCode = resolvedCode[:-1] + ")"
        return 1, resolvedCode.strip()

    def SVWS(self):
        ins, op1, op2, op1 = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3][2:]))
        op2_val = self.core.RFs.get("SRF").Read(op2)
        op1_val = self.core.RFs.get("SRF").Read(op1)
        op1_val = self.core.RFs.get("VRF").Read(op1)
        veclen = self.core.RFs.get("VLG").Read()
        mask_reg = self.core.RFs.get("VMR").Read()
        for i in range(veclen):
            if mask_reg[i]:
                self.core.vdmem.Write(op2_val + i * op1_val, op1_val[i])
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        resolvedCode += "("
        for i in range(veclen):
            resolvedCode += str(op2_val + i * op1_val) + ","
        resolvedCode = resolvedCode[:-1] + ")"
        return 1, resolvedCode.strip()

    def LVI(self):
        ins, op1, op2, op3 = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3][2:]))
        op2_val = self.core.RFs.get("SRF").Read(op2)
        op3_val = self.core.RFs.get("VRF").Read(op3)
        veclen = self.core.RFs.get("VLG").Read()
        op1_val_final = [self.core.vdmem.Read(op2_val + i) for i in op3_val[0:veclen]]
        self.core.vdmem.Write(op1, self.mask(op1, op1_val_final, veclen))
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        resolvedCode += "("
        for i in op3_val[0:veclen]:
            resolvedCode += str(op2_val + i) + ","
        resolvedCode = resolvedCode[:-1] + ")"
        return 1, resolvedCode.strip()

    def SVI(self):
        ins, op1, op2, op3 = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3][2:]))
        op2_val = self.core.RFs.get("SRF").Read(op2)
        op3_val = self.core.RFs.get("VRF").Read(op3)
        op1_val = self.core.RFs.get("VRF").Read(op1)
        veclen = self.core.RFs.get("VLG").Read()
        mask_reg = self.core.RFs.get("VMR").Read()
        for i in range(veclen):
            if mask_reg[i]:
                self.core.vdmem.Write(op2_val + op3_val[i], op1_val[i])
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        resolvedCode += "("
        for i in op3_val[0:veclen]:
            resolvedCode += str(op2_val + i) + ","
        resolvedCode = resolvedCode[:-1] + ")"
        return 1, resolvedCode.strip()

    # endregion

    # region Vector Instructions
    def ADDVV(self):
        ins, op3, op1, op2 = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3][2:]))
        op1_val = self.core.RFs.get("VRF").Read(op1)
        op2_val = self.core.RFs.get("VRF").Read(op2)
        veclen = self.core.RFs.get("VLG").Read()
        op3_val_final = [op1_val[i] + op2_val[i] for i in range(0, veclen)]
        self.core.RFs.get("VRF").Write(op3, self.mask(op3, op3_val_final, veclen))
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "

        return 1, resolvedCode.strip()

    def SUBVV(self):
        ins, op3, op1, op2 = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3][2:]))
        op1_val = self.core.RFs.get("VRF").Read(op1)
        op2_val = self.core.RFs.get("VRF").Read(op2)
        veclen = self.core.RFs.get("VLG").Read()
        op3_val_final = [op1_val[i] - op2_val[i] for i in range(0, veclen)]
        self.core.RFs.get("VRF").Write(op3, self.mask(op3, op3_val_final, veclen))
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "

        return 1, resolvedCode.strip()

    def MULVV(self):
        ins, op3, op1, op2 = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3][2:]))
        op1_val = self.core.RFs.get("VRF").Read(op1)
        op2_val = self.core.RFs.get("VRF").Read(op2)
        veclen = self.core.RFs.get("VLG").Read()
        op3_val_final = [op1_val[i] * op2_val[i] for i in range(0, veclen)]
        self.core.RFs.get("VRF").Write(op3, self.mask(op3, op3_val_final, veclen))
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "

        return 1, resolvedCode.strip()

    def DIVVV(self):
        ins, op3, op1, op2 = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3][2:]))
        op1_val = self.core.RFs.get("VRF").Read(op1)
        op2_val = self.core.RFs.get("VRF").Read(op2)
        vl = self.core.RFs.get("VLG").Read()
        op3_val_final = [op1_val[i] / op2_val[i] for i in range(0, vl)]
        self.core.RFs.get("VRF").Write(op3, self.mask(op3, op3_val_final))
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "

        return 1, resolvedCode.strip()

    def ADDVS(self):
        ins, op3, op1, op2 = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3][2:]))
        op1_val = self.core.RFs.get("VRF").Read(op1)
        op2_val = self.core.RFs.get("SRF").Read(op2)
        vl = self.core.RFs.get("VLG").Read()
        op3_val_final = [op1_val[i] + op2_val for i in range(0, vl)]
        self.core.RFs.get("VRF").Write(op3, self.mask(op3, op3_val_final))
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def SUBVS(self):
        ins, op3, op1, op2 = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3][2:]))
        op1_val = self.core.RFs.get("VRF").Read(op1)
        op2_val = self.core.RFs.get("SRF").Read(op2)
        vl = self.core.RFs.get("VLG").Read()
        op3_val_final = [op1_val[i] - op2_val for i in range(0, vl)]
        self.core.RFs.get("VRF").Write(op3, self.mask(op3, op3_val_final))
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def MULVS(self):
        ins, op3, op1, op2 = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3][2:]))
        op1_val = self.core.RFs.get("VRF").Read(op1)
        op2_val = self.core.RFs.get("SRF").Read(op2)
        vl = self.core.RFs.get("VLG").Read()
        op3_val_final = [op1_val[i] * op2_val for i in range(0, vl)]
        self.core.RFs.get("VRF").Write(op3, self.mask(op3, op3_val_final))
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def DIVVS(self):
        ins, op3, op1, op2 = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3][2:]))
        op1_val = self.core.RFs.get("VRF").Read(op1)
        op2_val = self.core.RFs.get("SRF").Read(op2)
        vl = self.core.RFs.get("VLG").Read()
        op3_val_final = [op1_val[i] / op2_val for i in range(0, vl)]
        self.core.RFs.get("VRF").Write(op3, self.mask(op3, op3_val_final))
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    # endregion

    # region Mask Instructions
    # vector
    def SEQVV(self):
        ins, op1, op2 = (self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]))
        op1_val = self.core.RFs.get("VRF").Read(op1)
        op2_val = self.core.RFs.get("VRF").Read(op2)
        vl = self.core.RFs.get("VLG").Read()
        masked_reg = [int(op1_val[i] == op2_val[i]) for i in range(0, vl)]
        masked_reg.extend([0 for _ in range(self.core.MVL - vl)])
        self.core.RFs.get("VMR").Write(0, masked_reg)
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def SNEVV(self):
        ins, op1, op2 = (self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]))
        op1_val = self.core.RFs.get("VRF").Read(op1)
        op2_val = self.core.RFs.get("VRF").Read(op2)
        vl = self.core.RFs.get("VLG").Read()
        masked_reg = [int(op1_val[i] != op2_val[i]) for i in range(0, vl)]
        masked_reg.extend([0 for _ in range(self.core.MVL - vl)])
        self.core.RFs.get("VMR").Write(0, masked_reg)
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def SGTVV(self):
        ins, op1, op2 = (self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]))
        op1_val = self.core.RFs.get("VRF").Read(op1)
        op2_val = self.core.RFs.get("VRF").Read(op2)
        vl = self.core.RFs.get("VLG").Read()
        masked_reg = [int(op1_val[i] > op2_val[i]) for i in range(0, vl)]
        masked_reg.extend([0 for _ in range(self.core.MVL - vl)])
        self.core.RFs.get("VMR").Write(0, masked_reg)
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def SLTVV(self):
        ins, op1, op2 = (self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]))
        op1_val = self.core.RFs.get("VRF").Read(op1)
        op2_val = self.core.RFs.get("VRF").Read(op2)
        vl = self.core.RFs.get("VLG").Read()
        masked_reg = [int(op1_val[i] < op2_val[i]) for i in range(0, vl)]
        masked_reg.extend([0 for _ in range(self.core.MVL - vl)])
        self.core.RFs.get("VMR").Write(0, masked_reg)
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def SGEVV(self):
        ins, op1, op2 = (self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]))
        op1_val = self.core.RFs.get("VRF").Read(op1)
        op2_val = self.core.RFs.get("VRF").Read(op2)
        vl = self.core.RFs.get("VLG").Read()
        masked_reg = [int(op1_val[i] >= op2_val[i]) for i in range(0, vl)]
        masked_reg.extend([0 for _ in range(self.core.MVL - vl)])
        self.core.RFs.get("VMR").Write(0, masked_reg)
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def SLEVV(self):
        ins, op1, op2 = (self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]))
        op1_val = self.core.RFs.get("VRF").Read(op1)
        op2_val = self.core.RFs.get("VRF").Read(op2)
        vl = self.core.RFs.get("VLG").Read()
        masked_reg = [int(op1_val[i] <= op2_val[i]) for i in range(0, vl)]
        masked_reg.extend([0 for _ in range(self.core.MVL - vl)])
        self.core.RFs.get("VMR").Write(0, masked_reg)
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    # scalar
    def SEQVS(self):
        ins, op1, op2 = (self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]))
        op1_val = self.core.RFs.get("VRF").Read(op1)
        op2_val = self.core.RFs.get("SRF").Read(op2)
        vl = self.core.RFs.get("VLG").Read()
        masked_reg = [int(op1_val[i] == op2_val) for i in range(0, vl)]
        masked_reg.extend([0 for _ in range(self.core.MVL - vl)])
        self.core.RFs.get("VMR").Write(0, masked_reg)
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def SNEVS(self):
        ins, op1, op2 = (self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]))
        op1_val = self.core.RFs.get("VRF").Read(op1)
        op2_val = self.core.RFs.get("SRF").Read(op2)
        vl = self.core.RFs.get("VLG").Read()
        masked_reg = [int(op1_val[i] != op2_val) for i in range(0, vl)]
        masked_reg.extend([0 for _ in range(self.core.MVL - vl)])
        self.core.RFs.get("VMR").Write(0, masked_reg)
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def SGTVS(self):
        ins, op1, op2 = (self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]))
        op1_val = self.core.RFs.get("VRF").Read(op1)
        op2_val = self.core.RFs.get("SRF").Read(op2)
        vl = self.core.RFs.get("VLG").Read()
        masked_reg = [int(op1_val[i] > op2_val) for i in range(0, vl)]
        masked_reg.extend([0 for _ in range(self.core.MVL - vl)])
        self.core.RFs.get("VMR").Write(0, masked_reg)
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def SLTVS(self):
        ins, op1, op2 = (self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]))
        op1_val = self.core.RFs.get("VRF").Read(op1)
        op2_val = self.core.RFs.get("SRF").Read(op2)
        vl = self.core.RFs.get("VLG").Read()
        masked_reg = [int(op1_val[i] < op2_val) for i in range(0, vl)]
        masked_reg.extend([0 for _ in range(self.core.MVL - vl)])
        self.core.RFs.get("VMR").Write(0, masked_reg)
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def SGEVS(self):
        ins, op1, op2 = (self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]))
        op1_val = self.core.RFs.get("VRF").Read(op1)
        op2_val = self.core.RFs.get("SRF").Read(op2)
        vl = self.core.RFs.get("VLG").Read()
        masked_reg = [int(op1_val[i] >= op2_val) for i in range(0, vl)]
        masked_reg.extend([0 for _ in range(self.core.MVL - vl)])
        self.core.RFs.get("VMR").Write(0, masked_reg)
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def SLEVS(self):
        ins, op1, op2 = (self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]))
        op1_val = self.core.RFs.get("VRF").Read(op1)
        op2_val = self.core.RFs.get("SRF").Read(op2)
        vl = self.core.RFs.get("VLG").Read()
        masked_reg = [int(op1_val[i] <= op2_val) for i in range(0, vl)]
        masked_reg.extend([0 for _ in range(self.core.MVL - vl)])
        self.core.RFs.get("VMR").Write(0, masked_reg)
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    # other
    def POP(self):
        ins, op2 = (self.operands[0], int(self.operands[1][2:]))
        masked_reg = self.core.RFs.get("VMR").Read(0)
        op2_val = 0
        for i in masked_reg:
            op2_val += i
        self.core.RFs.get("SRF").Write(op2, op2_val)
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def CVM(self):
        self.core.RFs.get("VMR").Write(0, [1] * 64)
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    # endregion

    # region VLG Instructions
    def MTCL(self):
        ins, op2 = (self.operands[0], int(self.operands[1][2:]))
        op2_val = self.core.RFs.get("SRF").Read(op2)
        self.core.RFs.get("VLG").Write(0, op2_val)
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        resolvedCode += str(op2_val)
        return 1, resolvedCode.strip()

    def MFCL(self):
        ins, op2 = (self.operands[0], int(self.operands[1][2:]))
        veclen = self.core.RFs.get("VLG").Read()
        self.core.RFs.get("SRF").Write(op2, veclen)
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    # endregion

    # region Scalar Instructions
    def ADD(self):
        ins, op3, op1, op2 = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3][2:]))
        op2_val = self.core.RFs.get("SRF").Read(op2)
        op1_val = self.core.RFs.get("SRF").Read(op1)
        self.core.RFs.get("SRF").Write(op3, op1_val + op2_val)
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def SUB(self):
        ins, op3, op1, op2 = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3][2:]))
        op2_val = self.core.RFs.get("SRF").Read(op2)
        op1_val = self.core.RFs.get("SRF").Read(op1)
        self.core.RFs.get("SRF").Write(op3, op1_val - op2_val)
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def SRA(self):
        ins, op3, op1, op2 = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3][2:]))
        op2_val = self.core.RFs.get("SRF").Read(op2)
        op1_val = self.core.RFs.get("SRF").Read(op1)
        self.core.RFs.get("SRF").Write(op3, self.arithrightshift(op1_val, op2_val))
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def SRL(self):
        ins, op3, op1, op2 = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3][2:]))
        op2_val = self.core.RFs.get("SRF").Read(op2)
        op1_val = self.core.RFs.get("SRF").Read(op1)
        self.core.RFs.get("SRF").Write(op3, self.logicalrightshift(op1_val, op2_val))
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def SLL(self):
        ins, op3, op1, op2 = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3][2:]))
        op2_val = self.core.RFs.get("SRF").Read(op2)
        op1_val = self.core.RFs.get("SRF").Read(op1)
        self.core.RFs.get("SRF").Write(op3, self.logicalleftshift(op1_val, op2_val))
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def AND(self):
        ins, op3, op1, op2 = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3][2:]))
        op2_val = self.core.RFs.get("SRF").Read(op2)
        op1_val = self.core.RFs.get("SRF").Read(op1)
        self.core.RFs.get("SRF").Write(op3, op1_val & op2_val)
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def OR(self):
        ins, op3, op1, op2 = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3][2:]))
        op2_val = self.core.RFs.get("SRF").Read(op2)
        op1_val = self.core.RFs.get("SRF").Read(op1)
        self.core.RFs.get("SRF").Write(op3, op1_val | op2_val)
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def XOR(self):
        ins, op3, op1, op2 = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3][2:]))
        op2_val = self.core.RFs.get("SRF").Read(op2)
        op1_val = self.core.RFs.get("SRF").Read(op1)
        self.core.RFs.get("SRF").Write(op3, op1_val ^ op2_val)
        self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def logicalleftshift(self, n, shift):
        return (n << shift) & 0xffffffff

    def logicalrightshift(self, n, shift):
        n_unsigned = n & 0xffffffff
        result_unsigned = n_unsigned >> shift

        if n < 0:
            if result_unsigned & 0x80000000:
                result_signed = -((~result_unsigned + 1) & 0xffffffff)
            else:
                result_signed = result_unsigned
        else:
            result_signed = result_unsigned
        return result_signed

    def arithrightshift(self, n, shift):
        if n < 0:
            n = (n >> 1) & ~(1 << 31)
            for i in range(shift - 1):
                n = (n >> 1) | (1 << 31)
        else:
            n = n >> shift
        return n

    # endregion

    # region Control Instructions
    def BEQ(self):
        ins, op1, op2, imm = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3]))
        op2_val = self.core.RFs.get("SRF").Read(op2)
        op1_val = self.core.RFs.get("SRF").Read(op1)
        if op2_val == op1_val:
            self.core.pc += imm
        else:
            self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def BNE(self):
        ins, op1, op2, imm = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3]))
        op2_val = self.core.RFs.get("SRF").Read(op2)
        op1_val = self.core.RFs.get("SRF").Read(op1)
        if op2_val != op1_val:
            self.core.pc += imm
        else:
            self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def BGT(self):
        ins, op1, op2, imm = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3]))
        op2_val = self.core.RFs.get("SRF").Read(op2)
        op1_val = self.core.RFs.get("SRF").Read(op1)
        if op2_val < op1_val:
            self.core.pc += imm
        else:
            self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def BLT(self):
        ins, op1, op2, imm = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3]))
        op2_val = self.core.RFs.get("SRF").Read(op2)
        op1_val = self.core.RFs.get("SRF").Read(op1)
        if op2_val > op1_val:
            self.core.pc += imm
        else:
            self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def BGE(self):
        ins, op1, op2, imm = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3]))
        op2_val = self.core.RFs.get("SRF").Read(op2)
        op1_val = self.core.RFs.get("SRF").Read(op1)
        if op2_val <= op1_val:
            self.core.pc += imm
        else:
            self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    def BLE(self):
        ins, op1, op2, imm = (
        self.operands[0], int(self.operands[1][2:]), int(self.operands[2][2:]), int(self.operands[3]))
        op2_val = self.core.RFs.get("SRF").Read(op2)
        op1_val = self.core.RFs.get("SRF").Read(op1)
        if op2_val >= op1_val:
            self.core.pc += imm
        else:
            self.core.pc += 1
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 1, resolvedCode.strip()

    # endregion

    # region Other
    def HALT(self):
        resolvedCode = ""
        for i in self.operands:
            resolvedCode += i + " "
        return 0, resolvedCode.strip()

    def mask(self, index, value, vector_length=-1):
        present_val = self.core.RFs.get("VRF").Read(index)
        mask_reg = self.core.RFs.get("VMR").Read()
        if vector_length == -1:
            vector_length = self.core.RFs.get("VLG").Read()
        for i in range(vector_length):
            if mask_reg[i]:
                present_val[i] = value[i]
        return present_val

    # endregion

    # region Default
    def Default(self):
        print("Wrong Instruction")
        return 0
    # endregion


if __name__ == "__main__":
    # parse arguments for input file location
    parser = argparse.ArgumentParser(
        description='Vector Core Performance Model')
    parser.add_argument('--iodir', default="", type=str,
                        help='Path to the folder containing the input files - instructions and data.')
    args = parser.parse_args()

    iodir = os.path.abspath(args.iodir)
    print("IO Directory:", iodir)
    # Parse IMEM
    imem = IMEM(iodir)
    # Parse SMEM
    sdmem = DMEM("SDMEM", iodir, 13)  # 32 KB is 2^15 bytes = 2^13 K 32-bit words.
    # Parse VMEM
    vdmem = DMEM("VDMEM", iodir, 17)  # 512 KB is 2^19 bytes = 2^17 K 32-bit words.

    # Create Vector Core
    vcore = Core(imem, sdmem, vdmem)
    result = vcore.run()
    if result == 0:
        print("Simulation Completed!")
    vcore.dumpRegs(iodir)
    vcore.dumpResolvedCode(iodir)
    sdmem.dump()
    vdmem.dump()
