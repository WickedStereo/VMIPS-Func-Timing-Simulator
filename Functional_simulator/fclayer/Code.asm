LS SR1 SR0 0
LS SR2 SR0 1
LS SR3 SR0 2
LS SR4 SR0 3
LS SR5 SR0 4
LS SR6 SR0 5
LS SR7 SR0 6
LV VR1 SR4
LV VR2 SR5
MULVV VR3 VR1 VR2
ADDVV VR4 VR3 VR4
ADD SR4 SR4 SR3
ADD SR5 SR5 SR3
SUB SR6 SR6 SR1
BNE SR6 SR0 -7
SV VR4 SR7
LS SR6 SR0 2
SRA SR6 SR6 SR1
MTCL SR6
LV VR1 SR7
ADD SR4 SR7 SR6
LV VR2 SR4
ADDVV VR3 VR1 VR2
SV VR3 SR7
BNE SR6 SR1 -7
ADD SR7 SR7 SR1
LS SR4 SR0 3
SUB SR2 SR2 SR1
LS SR6 SR0 2
MTCL SR6
SUBVV VR4 VR4 VR4
LS SR6 SR0 5
BNE SR2 SR0 -25
HALT