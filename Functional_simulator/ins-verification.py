import ak9327_am12553_funcsimulator as vp

def runSimulator(iodir):
    instr = "ADDVV VR3 VR2 VR1\nHALT"
    imem = vp.IMEM(iodir)
    imem.instructions = [instr]
    sdmem = vp.DMEM("SDMEM", iodir, 13)  # 32 KB is 2^15 bytes = 2^13 K 32-bit words.
    vdmem = vp.DMEM("VDMEM", iodir, 17)  # 512 KB is 2^19 bytes = 2^17 K 32-bit words.
    # Create Vector Core
    vcore = vp.Core(imem, sdmem, vdmem)
    result = vcore.run()
    # verify
    vl = vcore.mvl
    v1 = vcore.RFs.get("VRF").Read(1)
    v2 = vcore.RFs.get("VRF").Read(2)
    v3 = vcore.RFs.get("VRF").Read(3)
    for i in range(vl):
        if v1[i] + v2[i] != v3[i]:
            print("ADDVV Failed")
    print("ADDVV Verified")


    # reset pc
    vcore.PC = 0
    instr = "SUBVV VR3 VR2 VR1\nHALT"
    imem.instructions = [instr]
    result = vcore.run()
    # verify
    vl = vcore.mvl
    v1 = vcore.RFs.get("VRF").Read(1)
    v2 = vcore.RFs.get("VRF").Read(2)
    v3 = vcore.RFs.get("VRF").Read(3)
    for i in range(vl):
        if v1[i] - v2[i] != v3[i]:
            print("SUBVV Failed")
    print("SUBVV Verified")


    # reset pc
    vcore.PC = 0
    instr = "MULVV VR3 VR2 VR1\nHALT"
    imem.instructions = [instr]
    result = vcore.run()
    # verify
    vl = vcore.mvl
    v1 = vcore.RFs.get("VRF").Read(1)
    v2 = vcore.RFs.get("VRF").Read(2)
    v3 = vcore.RFs.get("VRF").Read(3)
    for i in range(vl):
        if v1[i] * v2[i] != v3[i]:
            print("MULVV Failed")
    print("MULVV Verified")

   # reset pc
    #vcore.PC = 0
    #instr = "DIVVV VR3 VR2 VR1\nHALT"
    #imem.instructions = [instr]
    #result = vcore.run()
    # verify
    #vl = vcore.mvl
    #v1 = vcore.RFs.get("VRF").Read(1)
    #v2 = vcore.RFs.get("VRF").Read(2)
    #v3 = vcore.RFs.get("VRF").Read(3)
    #for i in range(vl):
    #    if v1[i] / v2[i] != v3[i]:
    #        print("DIVVV Failed")
    #print("DIVVV Verified")

    # reset pc
    vcore.PC = 0
    instr = "ADDVS VR3 VR2 SR2\nHALT"
    imem.instructions = [instr]
    result = vcore.run()
    # verify
    vl = vcore.mvl
    v1 = vcore.RFs.get("VRF").Read(2)
    s2 = vcore.RFs.get("SRF").Read(2)
    v3 = vcore.RFs.get("VRF").Read(3)
    for i in range(vl):
        if v1[i] + s2 != v3[i]:
            print("ADDVS Failed")
    print("ADDVS Verified")

    # reset pc
    vcore.PC = 0
    instr = "SUBVS VR3 VR2 SR2\nHALT"
    imem.instructions = [instr]
    result = vcore.run()
    # verify
    vl = vcore.mvl
    v1 = vcore.RFs.get("VRF").Read(2)
    s2 = vcore.RFs.get("SRF").Read(2)
    v3 = vcore.RFs.get("VRF").Read(3)
    for i in range(vl):
        if v1[i] - s2 != v3[i]:
            print("SUBVS Failed")
    print("SUBVS Verified")

    # reset pc
    vcore.PC = 0
    instr = "MULVS VR3 VR2 SR2\nHALT"
    imem.instructions = [instr]
    result = vcore.run()
    # verify
    vl = vcore.mvl
    v1 = vcore.RFs.get("VRF").Read(2)
    s2 = vcore.RFs.get("SRF").Read(2)
    v3 = vcore.RFs.get("VRF").Read(3)
    for i in range(vl):
        if v1[i] * s2 != v3[i]:
            print("MULVS Failed")
    print("MULVS Verified")


    #reset pc
    vcore.PC = 0
    instr = "SEQVS VR1 SR2\nHALT"
    imem.instructions = [instr]
    result = vcore.run()
    vl = vcore.mvl
    v1 = vcore.RFs.get("VRF").Read(1)
    s1 = vcore.RFs.get("SRF").Read(2)
    mask_reg = vcore.RFs.get("VMR").Read()
    for i in range(vl):
        if (v1[i] == s1) != mask_reg[i]:
            print("SEQVS failed")
        else:
            print("SEQVS Verified")

        # reset pc
        vcore.PC = 0
        instr = "SNEVS VR1 SR2\nHALT"
        imem.instructions = [instr]
        result = vcore.run()
        vl = vcore.mvl
        v1 = vcore.RFs.get("VRF").Read(1)
        s1 = vcore.RFs.get("SRF").Read(2)
        mask_reg = vcore.RFs.get("VMR").Read()
        for i in range(vl):
            if (v1[i] != s1) != mask_reg[i]:
                print("SNEVS failed")
            else:
                print("SNEVS Verified")

        # reset pc
        vcore.PC = 0
        instr = "SGTVS VR1 SR2\nHALT"
        imem.instructions = [instr]
        result = vcore.run()
        vl = vcore.mvl
        v1 = vcore.RFs.get("VRF").Read(1)
        s1 = vcore.RFs.get("SRF").Read(2)
        mask_reg = vcore.RFs.get("VMR").Read()
        for i in range(vl):
            if (v1[i] > s1) != mask_reg[i]:
                print("SGTVS failed")
            else:
                print("SGTVS Verified")

        # reset pc
        vcore.PC = 0
        instr = "SLTVS VR1 SR2\nHALT"
        imem.instructions = [instr]
        result = vcore.run()
        vl = vcore.mvl
        v1 = vcore.RFs.get("VRF").Read(1)
        s1 = vcore.RFs.get("SRF").Read(2)
        mask_reg = vcore.RFs.get("VMR").Read()
        for i in range(vl):
            if (v1[i] < s1) != mask_reg[i]:
                print("SLTVS failed")
            else:
                print("SLTVS Verified")

        # reset pc
        vcore.PC = 0
        instr = "SGEVS VR1 SR2\nHALT"
        imem.instructions = [instr]
        result = vcore.run()
        vl = vcore.mvl
        v1 = vcore.RFs.get("VRF").Read(1)
        s1 = vcore.RFs.get("SRF").Read(2)
        mask_reg = vcore.RFs.get("VMR").Read()
        for i in range(vl):
            if (v1[i] >= s1) != mask_reg[i]:
                print("SGEVS failed")
            else:
                print("SGEVS Verified")

        # reset pc
        vcore.PC = 0
        instr = "SLEVS VR1 SR2\nHALT"
        imem.instructions = [instr]
        result = vcore.run()
        vl = vcore.mvl
        v1 = vcore.RFs.get("VRF").Read(1)
        s1 = vcore.RFs.get("SRF").Read(2)
        mask_reg = vcore.RFs.get("VMR").Read()
        for i in range(vl):
            if (v1[i] <= s1) != mask_reg[i]:
                print("SLEVS failed")
            else:
                print("SLEVS Verified")

        # reset pc
        vcore.PC = 0
        instr = "SEQVV VR1 VR2\nHALT"
        imem.instructions = [instr]
        result = vcore.run()
        vl = vcore.mvl
        v1 = vcore.RFs.get("VRF").Read(1)
        v2 = vcore.RFs.get("VRF").Read(2)
        mask_reg = vcore.RFs.get("VMR").Read()
        for i in range(vl):
            if (v1[i] == v2[i]) != mask_reg[i]:
                print("SEQVV failed")
            else:
                print("SEQVV Verified")

        # reset pc
        vcore.PC = 0
        instr = "SNEVV VR1 VR2\nHALT"
        imem.instructions = [instr]
        result = vcore.run()
        vl = vcore.mvl
        v1 = vcore.RFs.get("VRF").Read(1)
        v2 = vcore.RFs.get("VRF").Read(2)
        mask_reg = vcore.RFs.get("VMR").Read()
        for i in range(vl):
            if (v1[i] != v2[i]) != mask_reg[i]:
                print("SNEVV failed")
            else:
                print("SNEVV Verified")

        # reset pc
        vcore.PC = 0
        instr = "SGTVV VR1 VR2\nHALT"
        imem.instructions = [instr]
        result = vcore.run()
        vl = vcore.mvl
        v1 = vcore.RFs.get("VRF").Read(1)
        v2 = vcore.RFs.get("VRF").Read(2)
        mask_reg = vcore.RFs.get("VMR").Read()
        for i in range(vl):
            if (v1[i] > v2[i]) != mask_reg[i]:
                print("SGTVV failed")
            else:
                print("SGTVV Verified")

        # reset pc
        vcore.PC = 0
        instr = "SLTVV VR1 VR2\nHALT"
        imem.instructions = [instr]
        result = vcore.run()
        vl = vcore.mvl
        v1 = vcore.RFs.get("VRF").Read(1)
        v2 = vcore.RFs.get("VRF").Read(2)
        mask_reg = vcore.RFs.get("VMR").Read()
        for i in range(vl):
            if (v1[i] < v2[i]) != mask_reg[i]:
                print("SLTVV failed")
            else:
                print("SLTVV Verified")

        # reset pc
        vcore.PC = 0
        instr = "SGEVV VR1 VR2\nHALT"
        imem.instructions = [instr]
        result = vcore.run()
        vl = vcore.mvl
        v1 = vcore.RFs.get("VRF").Read(1)
        v2 = vcore.RFs.get("VRF").Read(2)
        mask_reg = vcore.RFs.get("VMR").Read()
        for i in range(vl):
            if (v1[i] >= v2[i]) != mask_reg[i]:
                print("SGEVV failed")
            else:
                print("SGEVV Verified")

        # reset pc
        vcore.PC = 0
        instr = "SLEVV VR1 VR2\nHALT"
        imem.instructions = [instr]
        result = vcore.run()
        vl = vcore.mvl
        v1 = vcore.RFs.get("VRF").Read(1)
        v2 = vcore.RFs.get("VRF").Read(2)
        mask_reg = vcore.RFs.get("VMR").Read()
        for i in range(vl):
            if (v1[i] <= v2[i]) != mask_reg[i]:
                print("SLEVV failed")
            else:
                print("SLEVV Verified")

        # reset pc
        vcore.PC = 0
        instr = "ADD SR3 SR1 SR2\nHALT"
        imem.instructions = [instr]
        result = vcore.run()
        vl = vcore.mvl
        s1 = vcore.RFs.get("SRF").Read(1)
        s2 = vcore.RFs.get("SRF").Read(2)
        s3 = vcore.RFs.get("SRF").Read(3)
        for i in range(vl):
            if s1 + s2 != s3:
                print("ADD Failed")
        print("ADD Verified")

        # reset pc
        vcore.PC = 0
        instr = "SUB SR3 SR1 SR2\nHALT"
        imem.instructions = [instr]
        result = vcore.run()
        vl = vcore.mvl
        s1 = vcore.RFs.get("SRF").Read(1)
        s2 = vcore.RFs.get("SRF").Read(2)
        s3 = vcore.RFs.get("SRF").Read(3)
        for i in range(vl):
            if s1 - s2 != s3:
                print("SUB Failed")
        print("SUB Verified")

        # reset pc
        vcore.PC = 0
        instr = "AND SR3 SR1 SR2\nHALT"
        imem.instructions = [instr]
        result = vcore.run()
        vl = vcore.mvl
        s1 = vcore.RFs.get("SRF").Read(1)
        s2 = vcore.RFs.get("SRF").Read(2)
        s3 = vcore.RFs.get("SRF").Read(3)
        for i in range(vl):
            if s1 & s2 != s3:
                print("AND Failed")
        print("AND Verified")

        # reset pc
        vcore.PC = 0
        instr = "OR SR3 SR1 SR2\nHALT"
        imem.instructions = [instr]
        result = vcore.run()
        vl = vcore.mvl
        s1 = vcore.RFs.get("SRF").Read(1)
        s2 = vcore.RFs.get("SRF").Read(2)
        s3 = vcore.RFs.get("SRF").Read(3)
        for i in range(vl):
            if s1 | s2 != s3:
                print("OR Failed")
        print("OR Verified")

        # reset pc
        vcore.PC = 0
        instr = "XOR SR3 SR1 SR2\nHALT"
        imem.instructions = [instr]
        result = vcore.run()
        vl = vcore.mvl
        s1 = vcore.RFs.get("SRF").Read(1)
        s2 = vcore.RFs.get("SRF").Read(2)
        s3 = vcore.RFs.get("SRF").Read(3)
        for i in range(vl):
            if s1 ^ s2 != s3:
                print("XOR Failed")
        print("XOR Verified")

        # reset pc
        vcore.PC = 0
        instr = "BNE SR3 SR1 2\nHALT"
        imem.instructions = [instr]
        result = vcore.run()
        vl = vcore.mvl
        s1 = vcore.RFs.get("SRF").Read(1)
        s3 = vcore.RFs.get("SRF").Read(3)
        if s3 == s1:
            if vcore.PC != 2:
                print("BNE Failed")
        print("BNE Verified")

        # reset pc
        vcore.PC = 0
        instr = "BEQ SR3 SR1 2\nHALT"
        imem.instructions = [instr]
        result = vcore.run()
        vl = vcore.mvl
        s1 = vcore.RFs.get("SRF").Read(1)
        s3 = vcore.RFs.get("SRF").Read(3)
        if s3 == s1:
            if vcore.PC == 2:
                print("BEQ Failed")
        print("BEQ Verified")

        # reset pc
        vcore.PC = 0
        instr = "BGT SR3 SR1 2\nHALT"
        imem.instructions = [instr]
        result = vcore.run()
        vl = vcore.mvl
        s1 = vcore.RFs.get("SRF").Read(1)
        s3 = vcore.RFs.get("SRF").Read(3)
        if s3 > s1:
            if vcore.PC != 2:
                print("BGT Failed")
        print("BGT Verified")

        # reset pc
        vcore.PC = 0
        instr = "BLT SR3 SR1 2\nHALT"
        imem.instructions = [instr]
        result = vcore.run()
        vl = vcore.mvl
        s1 = vcore.RFs.get("SRF").Read(1)
        s3 = vcore.RFs.get("SRF").Read(3)
        if s3 < s1:
            if vcore.PC != 2:
                print("BLT Failed")
        print("BLT Verified")

        # reset pc
        vcore.PC = 0
        instr = "BGE SR3 SR1 2\nHALT"
        imem.instructions = [instr]
        result = vcore.run()
        vl = vcore.mvl
        s1 = vcore.RFs.get("SRF").Read(1)
        s3 = vcore.RFs.get("SRF").Read(3)
        if s3 >= s1:
            if vcore.PC != 2:
                print("BGE Failed")
        print("BGE Verified")

        # reset pc
        vcore.PC = 0
        instr = "BLE SR3 SR1 2\nHALT"
        imem.instructions = [instr]
        result = vcore.run()
        vl = vcore.mvl
        s1 = vcore.RFs.get("SRF").Read(1)
        s3 = vcore.RFs.get("SRF").Read(3)
        if s3 <= s1:
            if vcore.PC != 2:
                print("BLE Failed")
        print("BLE Verified")


    # Dumping the final values
    vcore.dumpRegs(iodir)
    sdmem.dump()
    vdmem.dump()
    return vcore


if __name__ == "__main__":
    iodir = "instructiontest"
    result = runSimulator(iodir)  # Running simulator

