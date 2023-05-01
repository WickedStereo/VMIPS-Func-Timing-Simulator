LS SR1 SR0 0        #Value 1
LS SR2 SR0 1        #Vector 1
LS SR3 SR0 2        #Vector 2
LS SR4 SR0 3        #VLG
LS SR5 SR0 4        #Loop variable roundoff(450/64) = 8
LS SR7 SR0 5        #Destination address
LS SR6 SR0 6        #Loading number of excess elements (448+2)
MTCL SR4            #Changing the VLG
LV VR1 SR2          #Vector 1
LV VR2 SR3          #Vector 2
MULVV VR3 VR1 VR2   #Multiplication
ADDVV VR4 VR3 VR4   #Addition
ADD SR2 SR2 SR4     #Vector 1 next elements after VLG
ADD SR3 SR3 SR4     #Vector 2 next elements after VLG
SUB SR5 SR5 SR1     #Decrementing loop variable
BNE SR5 SR1 2       #Last round of loop
MTCL SR6            #VLG set to excess elements
BNE SR5 SR0 -10     #Looping done
MTCL SR4            #Reset VLG
SV VR4 SR7          #Storing sum at destination
SRA SR4 SR4 SR1     #Reducing VLG by half
MTCL SR4
LV VR1 SR7          #Load first half of the sum vector
ADD SR2 SR7 SR4
LV VR2 SR2          #Load second half of the sum vector
ADDVV VR4 VR1 VR2   #Add and store at destination
SV VR4 SR7
BNE SR4 SR1 -7      #Loop till VLG = 1
HALT