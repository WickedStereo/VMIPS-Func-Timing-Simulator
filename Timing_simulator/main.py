import time
import os


class Config(object):
    def __init__(self, iodir, fileName="Config.txt"):
        self.filepath = os.path.abspath(os.path.join(iodir, fileName))
        self.parameters = {}
        self.numberOfLanes = None
        self.addPipelineDepth = None
        self.mulPipelineDepth = None
        self.divPipelineDepth = None
        self.dataQueueDepth = None
        self.computeQueueDepth = None
        self.numberOfBanks = None
        self.vlsPipelineDepth = None
        try:
            with open(self.filepath, 'r') as conf:
                self.parameters = {line.split('=')[0].strip(): int(line.split('=')[1].split('#')[0].strip()) for line in
                                   conf.readlines() if not (line.startswith('#') or line.strip() == '')}
            print("Config - Parameters loaded from file:", self.filepath)
            print("Config parameters:", self.parameters)
            self.parseParameters()
        except:
            print("Config - ERROR: Couldn't open file in path:", self.filepath)
            raise

    def parseParameters(self):
        if self.parameters["dataQueueDepth"] is not None:
            self.dataQueueDepth = self.parameters["dataQueueDepth"]
        else:
            self.dataQueueDepth = 4
            print("dataQueueDepth not found in " + self.filepath + " taking 4 as default value.")

        self.computeQueueDepth = self.parameters["computeQueueDepth"]
        self.numberOfBanks = self.parameters["vdmNumBanks"]
        self.vlsPipelineDepth = self.parameters["vlsPipelineDepth"]
        self.numberOfLanes = self.parameters["numLanes"]
        self.addPipelineDepth = self.parameters["pipelineDepthAdd"]
        self.mulPipelineDepth = self.parameters["pipelineDepthMul"]
        self.divPipelineDepth = self.parameters["pipelineDepthDiv"]


class IMEM(object):
    def __init__(self, iodir):
        self.size = pow(2, 16)  # Can hold a maximum of 2^16 instructions.
        self.filepath = os.path.abspath(os.path.join(iodir, "code.txt"))
        self.instructions = []

        try:
            with open(self.filepath, 'r') as insf:
                self.instructions = [ins.split('#')[0].strip() for ins in insf.readlines() if
                                     not (ins.startswith('#') or ins.strip() == '')]
            print("IMEM - Instructions loaded from file:", self.filepath)
            # print("IMEM - Instructions:", self.instructions)
        except:
            print("IMEM - ERROR: Couldn't open file in path:", self.filepath)
            raise


class Core:
    def __init__(self, config, imem):
        self.config = config
        self.imem = imem
        self.compute = ComputeExec(self.config.addPipelineDepth, self.config.mulPipelineDepth,
                                   self.config.divPipelineDepth, self.config.numberOfLanes)
        self.data = DataExec(6, self.config.numberOfBanks, self.config.vlsPipelineDepth)
        self.decode = Decode(self.config.computeQueueDepth, self.config.dataQueueDepth, 8, 8, self.compute, self.data)
        self.fetch = Fetch(self.imem.instructions, self.decode)
        self.compute.setFreeBusyBoard(self.decode.freeBusyBoard)
        self.data.setFreeBusyBoard(self.decode.freeBusyBoard)
        self.clk = 1
        self.startTime = None
        self.endTime = None

    def run(self):
        print("Timing Simulation Started")
        self.startTime = time.time()
        while not (self.fetch.getStatus() == Status.COMPLETED and self.decode.isClear()):
            status1, instr = self.fetch.run()
            status2, computeInstr, dataInstr, scalarInstr = self.decode.run(instr)
            self.compute.run(computeInstr, self.fetch.getCurrentVectorLength())
            self.data.run(dataInstr)
            self.clk += 1

        self.endTime = time.time()
        print("Timing Simulation Completed")

    def printResult(self):
        time_difference = self.endTime - self.startTime
        minutes = str(int(time_difference // 60))
        seconds = str(int(time_difference % 60))
        # milliseconds = str(int((time_difference - int(time_difference)) * 1000))
        print("----------------Simulation Results----------------")
        print("Clock Cycles: ", self.clk - 1)
        print("Time Elapsed: ", minutes + "m", seconds + "s")
        print("--------------------------------------------------")

    def dumpResult(self):
        pass


class Status:
    FAILED = 0
    SUCCESS = 1
    COMPLETED = 2
    BUSY = 3
    FREE = 4


class Fetch:
    def __init__(self, imem, decode):
        self.imem = imem
        self.addr = 0
        self.decode = decode
        self.currentVectorLength = 64
        self.__status = Status.FREE

    def run(self):

        # instr = self.imem.Read(self.addr)  # Reading the instruction
        if len(self.imem) == self.addr or self.__status == Status.COMPLETED:
            self.__status = Status.COMPLETED
            return Status.SUCCESS, None

        instr = self.imem[self.addr]

        if instr.split()[0] == 'MTCL':
            if self.decode.isClear():
                self.currentVectorLength = int(instr.split()[-1])
                self.addr = self.addr + 1
                return Status.SUCCESS, instr
            else:
                return Status.SUCCESS, None
        else:
            self.addr = self.addr + 1
            return Status.SUCCESS, instr

    def getCurrentVectorLength(self):
        return self.currentVectorLength

    def getStatus(self):
        return self.__status


class Decode:
    INSTR_EMPTY = 0
    INSTR_COMPUTE = 1
    INSTR_DATA = 2
    INSTR_SCALAR = 3
    INSTR_TYPE = "Type"
    INSTR_SDEST = "SDest"
    INSTR_VDEST = "VDest"
    INSTR_VSRC = "VSrc"
    INSTR_SSRC = "SSrc"
    INSTR_NAME = "Name"
    INSTR_ADDRESS = "Address"
    INSTR_ARGS = "Args"

    INS = dict.fromkeys(['LS', 'SS', 'ADD', 'SUB', 'SRA', 'SRL', 'SLL', 'AND', 'OR',
                         'XOR', 'BEQ', 'BNE', 'BGT', 'BLT', 'BGE', 'BLE', 'MFCL', 'MTCL', 'CVM', 'POP', 'HALT'],
                        INSTR_SCALAR)
    INS.update(dict.fromkeys(['LV', 'SV', 'LVWS', 'SVWS', 'LVI', 'SVI'], INSTR_DATA))
    INS.update(dict.fromkeys(['ADDVV', 'SUBVV', 'MULVV', 'DIVVV', 'SEQVV', 'SNEVV', 'SGTVV', 'SLTVV', 'SGEVV', 'SLEVV',
                              'ADDVS', 'SUBVS', 'MULVS', 'DIVVS', 'SEQVS', 'SNEVS', 'SGTVS', 'SLTVS', 'SGEVS', 'SLVES'],
                             INSTR_COMPUTE))

    def __init__(self, computeQueueDepth, dataQueueDepth, vectorRegisterLength, scalarRegisterLength, computeExec,
                 dataExec):
        self.computeQueueDepth = computeQueueDepth
        self.dataQueueDepth = dataQueueDepth
        self.computeExec = computeExec
        self.dataExec = dataExec
        self.computeQueue = []
        self.dataQueue = []
        self.scalarQueue = []
        self.args = 0
        self.__computeStatus = Status.FREE
        self.__dataStatus = Status.FREE
        self.instr = None
        self.vectorBusyBoard = [0] * vectorRegisterLength
        self.scalarBusyBoard = [0] * scalarRegisterLength
        self.priorityQueue = []

    def run(self, instr):

        # region Popping out of the queue
        if self.shouldPopCompute():
            computeInstr = self.computeQueue.pop(0) if len(self.computeQueue) > 0 else None
        else:
            computeInstr = None

        if self.shouldPopData():
            dataInstr = self.dataQueue.pop(0) if len(self.dataQueue) > 0 else None
        else:
            dataInstr = None

        scalarInstr = self.scalarQueue.pop(0) if len(self.scalarQueue) > 0 else None
        self.freeBusyBoard(scalarInstr)
        # endregion

        # Adding to Queue
        if instr is not None:
            self.args = instr.split()
            self.instr = {Decode.INSTR_TYPE: self.INS.get(self.args[0], None),
                          Decode.INSTR_NAME: self.args[0],
                          Decode.INSTR_ARGS: instr.split()}
            self.priorityQueue.append(self.instr)
            if self.instr.get(Decode.INSTR_TYPE) is None:
                return Status.FAILED, None, None, None
            toggle = False
            for index, instr in enumerate(self.priorityQueue):
                self.instr = instr
                self.args = instr.get(Decode.INSTR_ARGS)
                self.parseInstruction()
                # Compute part
                if self.__computeStatus == Status.FREE and instr.get(Decode.INSTR_TYPE) == Decode.INSTR_COMPUTE:
                    if self.checkBusyBoard():
                        self.updateBusyBoard()
                        self.computeQueue.append(self.instr)
                        toggle = True
                        if len(self.computeQueue) == self.computeQueueDepth:
                            self.__computeStatus = Status.BUSY
                        else:
                            self.__computeStatus = Status.FREE

                # Data Part
                elif self.__dataStatus == Status.FREE and instr.get(Decode.INSTR_TYPE) == Decode.INSTR_DATA:
                    if self.checkBusyBoard():
                        self.updateBusyBoard()
                        self.dataQueue.append(self.instr)
                        toggle = True
                        if len(self.dataQueue) == self.dataQueueDepth:
                            self.__dataStatus = Status.BUSY
                        else:
                            self.__dataStatus = Status.FREE

                # Scalar Part
                elif instr.get(Decode.INSTR_TYPE) == Decode.INSTR_SCALAR and self.checkBusyBoard():
                    self.updateBusyBoard()
                    toggle = True
                    self.scalarQueue.append(self.instr)

                if toggle:
                    self.priorityQueue.pop(index)
                    break

        return Status.SUCCESS, computeInstr, dataInstr, scalarInstr

    def getComputeStatus(self):
        return self.__computeStatus

    def getDataStatus(self):
        return self.__dataStatus

    def isClear(self):
        # a = self.shouldPopCompute() and len(self.computeQueue) == 1
        # b = self.shouldPopData() and len(self.dataQueue) == 1
        c = len(self.computeQueue) == 0
        d = len(self.dataQueue) == 0
        e = self.dataExec.getStatus() == Status.FREE
        f = self.computeExec.isDone()
        if c and d and e and f:
            return True
        else:
            return False

    def shouldPopCompute(self):
        return len(self.computeQueue) > 0 and ((self.computeQueue[0].get(
            Decode.INSTR_NAME) in ComputeExec.addPipelineInstr and self.computeExec.getAddPipelineStatus() == Status.FREE)
                                               or (self.computeQueue[0].get(
                    Decode.INSTR_NAME) in ComputeExec.mulPipelineInstr and self.computeExec.getMulPipelineStatus() == Status.FREE)
                                               or (self.computeQueue[0].get(
                    Decode.INSTR_NAME) in ComputeExec.divPipelineInstr and self.computeExec.getDivPipelineStatus() == Status.FREE))

    def shouldPopData(self):
        return self.dataExec.getStatus() == Status.FREE

    def freeBusyBoard(self, instr):
        if instr is not None:
            sdest = instr.get(Decode.INSTR_SDEST)
            if sdest is not None:
                self.scalarBusyBoard[sdest] = 0

            vdest = instr.get(Decode.INSTR_VDEST)
            if vdest is not None:
                self.vectorBusyBoard[vdest] = 0

    def parseInstruction(self):
        name = self.instr[Decode.INSTR_NAME]
        type = self.instr[Decode.INSTR_TYPE]

        if type == Decode.INSTR_COMPUTE:
            if name in ['ADDVV', 'SUBVV', 'MULVV', 'DIVVV']:
                self.instr[Decode.INSTR_VDEST] = int(self.args[1][2:])
                self.instr[Decode.INSTR_VSRC] = [int(self.args[2][2:]), int(self.args[3][2:])]
            elif name in ['ADDVS', 'SUBVS', 'MULVS', 'DIVVS']:
                self.instr[Decode.INSTR_VDEST] = int(self.args[1][2:])
                self.instr[Decode.INSTR_VSRC] = [int(self.args[2][2:])]
                self.instr[Decode.INSTR_SSRC] = [int(self.args[3][2:])]
            elif name in ['SEQVV', 'SNEVV', 'SGTVV', 'SLTVV', 'SGEVV', 'SLEVV']:
                self.instr[Decode.INSTR_VSRC] = [int(self.args[1][2:]), int(self.args[2][2:])]
            elif name in ['SEQVS', 'SNEVS', 'SGTVS', 'SLTVS', 'SGEVS', 'SLVES']:
                self.instr[Decode.INSTR_VSRC] = [int(self.args[1][2:])]
                self.instr[Decode.INSTR_SSRC] = [int(self.args[2][2:])]
        elif type == Decode.INSTR_SCALAR:
            if name == 'SS':
                self.instr[Decode.INSTR_SSRC] = [int(self.args[1][2:]), int(self.args[2][2:])]
            elif name == 'LS':
                self.instr[Decode.INSTR_SDEST] = int(self.args[1][2:])
                self.instr[Decode.INSTR_SSRC] = [int(self.args[2][2:])]
            elif name in ['ADD', 'SUB', 'AND', 'OR', 'XOR', 'SLL', 'SRL', 'SRA']:
                self.instr[Decode.INSTR_SDEST] = int(self.args[1][2:])
                self.instr[Decode.INSTR_SSRC] = [int(self.args[2][2:]), int(self.args[3][2:])]
            elif name in ['BEQ', 'BNE', 'BGT', 'BLT', 'BGE', 'BLE']:
                self.instr[Decode.INSTR_SSRC] = [int(self.args[1][2:]), int(self.args[2][2:])]
            elif name in ['MFCL', 'POP']:
                self.instr[Decode.INSTR_SDEST] = int(self.args[1][2:])
            elif name == 'MTCL':
                self.instr[Decode.INSTR_SSRC] = [int(self.args[1][2:])]
        else:
            self.instr[Decode.INSTR_ADDRESS] = [int(num) for num in self.args[-1].strip('()').split(',')]
            if name == 'LV':
                self.instr[Decode.INSTR_VDEST] = int(self.args[1][2:])
                self.instr[Decode.INSTR_SSRC] = [int(self.args[2][2:])]
            elif name == 'LVI':
                self.instr[Decode.INSTR_VDEST] = int(self.args[1][2:])
                self.instr[Decode.INSTR_SSRC] = [int(self.args[2][2:])]
                self.instr[Decode.INSTR_VSRC] = [int(self.args[3][2:])]
            elif name == 'LVWS':
                self.instr[Decode.INSTR_VDEST] = int(self.args[1][2:])
                self.instr[Decode.INSTR_SSRC] = [int(self.args[2][2:])]
                self.instr[Decode.INSTR_SSRC] = [int(self.args[3][2:])]
            elif name == 'SV':
                self.instr[Decode.INSTR_VDEST] = int(self.args[1][2:])
                self.instr[Decode.INSTR_SSRC] = [int(self.args[2][2:])]
            elif name == 'SVI':
                self.instr[Decode.INSTR_SSRC] = [int(self.args[2][2:])]
                self.instr[Decode.INSTR_VSRC] = [int(self.args[1][2:]), int(self.args[3][2:])]
            elif name == 'SVWS':
                self.instr[Decode.INSTR_VSRC] = [int(self.args[1][2:])]
                self.instr[Decode.INSTR_SSRC] = [int(self.args[2][2:]), int(self.args[3][2:])]

    def checkBusyBoard(self):
        ssrc = self.instr.get(Decode.INSTR_SSRC)
        if ssrc is not None:
            for i in ssrc:
                if self.scalarBusyBoard[i]:
                    return False

        vsrc = self.instr.get(Decode.INSTR_VSRC)
        if vsrc is not None:
            for i in vsrc:
                if self.vectorBusyBoard[i]:
                    return False

        sdest = self.instr.get(Decode.INSTR_SDEST)
        if sdest is not None:
            if self.scalarBusyBoard[sdest]:
                return False

        vdest = self.instr.get(Decode.INSTR_VDEST)
        if vdest is not None:
            if self.vectorBusyBoard[vdest]:
                return False

        return True

    def updateBusyBoard(self):
        sdest = self.instr.get(Decode.INSTR_SDEST)
        if sdest is not None:
            self.scalarBusyBoard[sdest] = 1

        vdest = self.instr.get(Decode.INSTR_VDEST)
        if vdest is not None:
            self.vectorBusyBoard[vdest] = 1


class ComputeExec:
    addPipelineInstr = ['ADDVV', 'SUBVV', 'ADDVS', 'SUBVS', 'SEQVV', 'SNEVV', 'SGTVV', 'SLTVV', 'SGEVV', 'SLEVV',
                        'SEQVS', 'SNEVS', 'SGTVS', 'SLTVS', 'SGEVS', 'SLEVS']
    mulPipelineInstr = ['MULVV', 'MULVS']
    divPipelineInstr = ['DIVVV', 'DIVVS']

    def __init__(self, addPipelineDepth, mulPipelineDepth, divPipelineDepth, numberOfLanes):
        self.addPipelineDepth = addPipelineDepth
        self.mulPipelineDepth = mulPipelineDepth
        self.divPipelineDepth = divPipelineDepth
        self.numberOfLanes = numberOfLanes
        self.currentAddInstr = None
        self.currentDivInstr = None
        self.currentMulInstr = None
        self.__addPipelineStatus = Status.FREE
        self.__mulPipelineStatus = Status.FREE
        self.__divPipelineStatus = Status.FREE
        self.addCycle = 0
        self.mulCycle = 0
        self.divCycle = 0
        self.freeBusyBoard = None

    def run(self, computeInstr, currentVectorLength):
        self.addCycle = max(0, self.addCycle - 1)
        self.mulCycle = max(0, self.mulCycle - 1)
        self.divCycle = max(0, self.divCycle - 1)

        if computeInstr is not None:
            if computeInstr.get(
                    Decode.INSTR_NAME) in ComputeExec.addPipelineInstr and self.__addPipelineStatus == Status.FREE:
                self.__addPipelineStatus = Status.BUSY
                self.currentAddInstr = computeInstr
                self.addCycle = self.addPipelineDepth + (currentVectorLength / self.numberOfLanes) - 1


            elif computeInstr.get(
                    Decode.INSTR_NAME) in ComputeExec.mulPipelineInstr and self.__mulPipelineStatus == Status.FREE:
                self.__mulPipelineStatus = Status.BUSY
                self.currentMulInstr = computeInstr
                self.mulCycle = self.mulPipelineDepth + (currentVectorLength / self.numberOfLanes) - 1
            else:
                self.__divPipelineStatus = Status.BUSY
                self.currentDivInstr = computeInstr
                self.divCycle = self.divPipelineDepth + (currentVectorLength / self.numberOfLanes) - 1

        if self.addCycle == 0 and self.__addPipelineStatus == Status.BUSY:
            self.freeBusyBoard(self.currentAddInstr)
            self.__addPipelineStatus = Status.FREE
        if self.mulCycle == 0 and self.__mulPipelineStatus == Status.BUSY:
            self.freeBusyBoard(self.currentMulInstr)
            self.__mulPipelineStatus = Status.FREE
        if self.divCycle == 0 and self.__divPipelineStatus == Status.BUSY:
            self.freeBusyBoard(self.currentDivInstr)
            self.__divPipelineStatus = Status.FREE

    def getPipelineStatus(self):
        return self.__addPipelineStatus, self.__mulPipelineStatus, self.__divPipelineStatus

    def getAddPipelineStatus(self):
        return self.__addPipelineStatus

    def getMulPipelineStatus(self):
        return self.__mulPipelineStatus

    def getDivPipelineStatus(self):
        return self.__divPipelineStatus

    def setFreeBusyBoard(self, freeBusyBoard):
        self.freeBusyBoard = freeBusyBoard

    def isDone(self):
        return self.__divPipelineStatus == Status.FREE and self.__mulPipelineStatus == Status.FREE and self.__addPipelineStatus == Status.FREE


class DataExec:

    def __init__(self, bankBusyTime, numberOfBanks, loadStorePipeline):
        self.bankBusyTime = bankBusyTime
        self.numberOfBanks = numberOfBanks
        self.loadStorePipeline = loadStorePipeline
        self.bankBusyBoard = [0] * numberOfBanks
        self.addresses = []
        self.__status = Status.FREE
        self.pipeline = [None] * self.loadStorePipeline
        self.element = None
        self.freeBusyBoard = None
        self.instr = None
        pass

    def run(self, dataInstr):
        for i in range(self.numberOfBanks):
            self.bankBusyBoard[i] = max(0, self.bankBusyBoard[i] - 1)

        if dataInstr is not None and self.__status == Status.FREE:
            self.instr = dataInstr
            self.__status = Status.BUSY
            self.addresses = dataInstr.get(Decode.INSTR_ADDRESS)

        if self.__status == Status.BUSY and len(self.addresses) > 0:
            address = self.pipeline[-1]
            if address is not None:
                bankNo = address % self.numberOfBanks
                if self.bankBusyBoard[bankNo] == 0:
                    self.bankBusyBoard[bankNo] = self.bankBusyTime
                    self.pipeline.pop()
                    self.pipeline.insert(0, self.addresses.pop())
            else:
                self.pipeline.pop()
                self.pipeline.insert(0, self.addresses.pop())

        # print(self.addresses)
        if len(self.addresses) == 0 and self.areBanksFree():
            self.freeBusyBoard(self.instr)
            self.__status = Status.FREE

    def getStatus(self):
        return self.__status

    def setFreeBusyBoard(self, freeBusyBoard):
        self.freeBusyBoard = freeBusyBoard

    def areBanksFree(self):
        for element in self.bankBusyBoard:
            if element != 0:
                return False
        return True


if __name__ == "__main__":
    iodir = "IODir"
    imem = IMEM(iodir)
    config = Config(iodir)
    core = Core(config, imem)
    core.run()
    core.printResult()
    core.dumpResult()
