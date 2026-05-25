'!TITLE "MAIN"
PROGRAM MAIN
    DEFIN li1
    REM ========= I1 notify that new string data is received. after processed, set I1 to 0 to wait for new data.
    I1 = 0
    REM ========= I4 and I5 used for ring buffer for processed joint.
    I4 = 0
    I5 = 0
    FLUSH #1
    FOR li1 = 0 to 99
        J[li1] = (0,0,0,0,0,0)
    NEXT li1
    REM ==== Read Serial Task
    RUN TASK0, C = 10
    DELAY 20
    REM ==== Process recevied data
    RUN TASK1CRC, C = 15
    REM ==== RUN ROBOT
    RUN TASK3, C = 35
    REM ==== Transmit current joint
    RUN GET_JOINT, C = 100
END