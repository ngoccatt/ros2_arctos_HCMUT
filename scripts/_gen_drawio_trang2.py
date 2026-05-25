#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Replace Trang-2 in Thesis.drawio with 6 clean, organised architecture diagrams.
Each diagram is self-contained in its own area for easy screenshot export.

Run from repository root:
    py -3 scripts/_gen_drawio_trang2.py
"""

import re

# ─── Label helpers ────────────────────────────────────────────────────────────
def lbl(text):
    """Plain text → XML-attribute-safe (newlines become &#xa;)."""
    s = (text
         .replace('&', '&amp;')
         .replace('<', '&lt;')
         .replace('>', '&gt;')
         .replace('"', '&quot;')
         .replace('\n', '&#xa;'))
    return s

# ─── Style constants ──────────────────────────────────────────────────────────
HW   = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;fontStyle=1;fontSize=13;"
DRV  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=12;"
HWI  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=12;"
CTRL = "rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=12;"
APP  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontSize=12;"
FLOW = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=12;"
DEC  = "rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=12;"
TTL  = "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=16;fontStyle=1;"
GRP  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f8f8f8;strokeColor=#888888;opacity=40;dashed=1;verticalAlign=top;spacingTop=6;fontSize=14;fontStyle=1;"
ANN  = "text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;fontSize=10;fontStyle=2;fontColor=#555555;"
ARR  = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=2;fontSize=11;"
ARRB = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=2;startArrow=block;startFill=1;endArrow=block;endFill=1;fontSize=11;"
ARRD = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=1;dashed=1;fontSize=10;"

def _lhdr(fill, stroke):
    return f"rounded=0;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};fontColor=#ffffff;fontSize=11;fontStyle=1;align=center;"

# ─── Cell builders ────────────────────────────────────────────────────────────
_id = [20000]
cells = []

def nid():
    _id[0] += 1
    return f"d{_id[0]}"

def V(x, y, w, h, label, style_str):
    i = nid()
    cells.append(
        f'        <mxCell id="{i}" parent="1" style="{style_str}" '
        f'value="{lbl(label)}" vertex="1">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" />'
        f'</mxCell>'
    )
    return i

def E(src, tgt, label="", style_str=None):
    i = nid()
    st = style_str or ARR
    cells.append(
        f'        <mxCell id="{i}" parent="1" style="{st}" '
        f'value="{lbl(label)}" edge="1" source="{src}" target="{tgt}">'
        f'<mxGeometry relative="1" as="geometry" /></mxCell>'
    )
    return i

def section(x, y, w, h, title):
    """Background group box with title."""
    V(x, y, w, h, title, GRP)

def ttl(x, y, w, text):
    V(x, y - 36, w, 32, text, TTL)

def ann(x, y, w, text):
    V(x, y, w, 20, text, ANN)


# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 1 — ROS2-Control Layered Architecture
# Position: (80, 80) → (2250, 1160)
# ══════════════════════════════════════════════════════════════════════════════
X1, Y1 = 80, 80
LW = 2170   # layer width
LH = 120    # normal layer height

ttl(X1, Y1, LW, "1. Kiến trúc phần mềm ROS2-Control (phân lớp)")
section(X1, Y1, LW, 1080, "")

# ── Layer 5: Applications ──────────────────────────────────────────────────
l5y = Y1 + 10
V(X1, l5y, 110, LH, "Ứng dụng\n(L5)", _lhdr("#9673a6","#9673a6"))
a5_moveit  = V(X1+125, l5y+15, 210, 90, "MoveIt2\n(path planning)", APP)
a5_servo   = V(X1+350, l5y+15, 220, 90, "Denso MoveIt Servo\n(Service Provider)", APP)
a5_remote  = V(X1+585, l5y+15, 220, 90, "Denso Remote Control\n(Action Server)", APP)
a5_rviz    = V(X1+820, l5y+15, 175, 90, "Rviz2\n(visualization)", APP)
a5_cam     = V(X1+1010, l5y+15, 175, 90, "V4L2 Camera\n(USB)", APP)

# ── L5 → L4 communication label ───────────────────────────────────────────
comm1y = l5y + LH + 4
ann(X1+120, comm1y, 800, "action: FollowJointTrajectory  |  action: GripperCommand")

# ── Layer 4: MoveIt Controller Manager ────────────────────────────────────
l4y = comm1y + 22
V(X1, l4y, 110, 75, "MoveIt2 CM\n(L4)", _lhdr("#82b366","#82b366"))
l4_mgr = V(X1+125, l4y+10, 500, 55, "Moveit Simple Controller Manager", CTRL)
E(a5_moveit, l4_mgr)

# ── L4 → L3 communication label ───────────────────────────────────────────
comm2y = l4y + 75 + 4
ann(X1+120, comm2y, 700, "command_interface  /  state_interface")

# ── Layer 3: Controllers ───────────────────────────────────────────────────
l3y = comm2y + 22
V(X1, l3y, 110, LH, "Controllers\n(L3)", _lhdr("#82b366","#82b366"))
l3_arm  = V(X1+125, l3y+15, 295, 90, "denso_arm_controller\nJointTrajectoryController", CTRL)
l3_hand = V(X1+435, l3y+15, 295, 90, "denso_hand_controller\nGripperActionController", CTRL)
l3_jsb  = V(X1+745, l3y+15, 295, 90, "joint_state_broadcaster\nJointStateBroadcaster", CTRL)
E(l4_mgr, l3_arm)
E(l4_mgr, l3_hand)

# ── L3 → L2 communication label ───────────────────────────────────────────
comm3y = l3y + LH + 4
ann(X1+120, comm3y, 500, "function calls")

# ── Layer 2: Hardware Interface ────────────────────────────────────────────
l2y = comm3y + 22
V(X1, l2y, 110, LH, "Hardware\nInterface\n(L2)", _lhdr("#6c8ebf","#6c8ebf"))
l2_arc  = V(X1+125, l2y+10, 390, 100, "DensoInterface (arctos_interface)\non_init / configure / activate\nread()  |  write()", HWI)
l2_hand = V(X1+535, l2y+10, 390, 100, "DensoHandInterface\non_init / configure / activate\nread()  |  write()", HWI)
E(l3_arm,  l2_arc)
E(l3_hand, l2_hand)

# ── L2 → L1 communication label ───────────────────────────────────────────
comm4y = l2y + LH + 4
ann(X1+120, comm4y, 450, "function calls")

# ── Layer 1: Drivers ──────────────────────────────────────────────────────
l1y = comm4y + 22
V(X1, l1y, 110, LH, "Driver\n(L1)", _lhdr("#d6b656","#a07e00"))
l1_mdr  = V(X1+125, l1y+15, 255, 90, "motor_driver\n(MksDriver)", DRV)
l1_srv  = V(X1+395, l1y+15, 255, 90, "servo_driver\n(ServoDriver)", DRV)
l1_uart = V(X1+665, l1y+15, 255, 90, "uart_protocol\n(UartProtocol)", DRV)
E(l2_arc,  l1_mdr)
E(l2_arc,  l1_uart)
E(l2_hand, l1_srv)
E(l2_hand, l1_uart)

# ── L1 → L0 communication label ───────────────────────────────────────────
comm5y = l1y + LH + 4
ann(X1+120, comm5y, 350, "UART 115200 bps")

# ── Layer 0: Hardware ─────────────────────────────────────────────────────
l0y = comm5y + 22
V(X1, l0y, 110, 95, "Phần cứng\n(L0)", _lhdr("#b85450","#b85450"))
l0_rc5  = V(X1+125, l0y+10, 370, 75, "RC5 Controller\n(Denso VS-6577E)", HW)
l0_hat  = V(X1+530, l0y+10, 370, 75, "Driver-Hat-A\n(Gripper-A)", HW)
E(l1_mdr,  l0_rc5)
E(l1_uart, l0_rc5)
E(l1_srv,  l0_hat)
E(l1_uart, l0_hat)


# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 2 — RC5 Program Architecture
# Position: (2350, 80) → (4650, 1160)
# ══════════════════════════════════════════════════════════════════════════════
X2, Y2 = 2350, 80
TW = 2300   # total width

ttl(X2, Y2, TW, "2. Kiến trúc chương trình điều khiển RC5")
section(X2, Y2, TW, 1080, "")

# ── MAIN.pac block ────────────────────────────────────────────────────────
main = V(X2+50, Y2+20, TW-100, 70,
         "MAIN.pac    ▶  RUN TASK0 (C=10ms)    RUN TASK1CRC (C=15ms)    RUN TASK3 (C=35ms)    RUN GET_JOINT (C=100ms)",
         "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontStyle=1;fontSize=13;")

# Task column widths
TH = 370   # task area height
COL_W = 490
task_tops = [Y2 + 115, Y2 + 115, Y2 + 115, Y2 + 115]
col_xs    = [X2+30,    X2+560,    X2+1090,   X2+1620]

# ── TASK0 ────────────────────────────────────────────────────────────────
t0 = V(col_xs[0], task_tops[0], COL_W-20, 35, "TASK0  (C = 10 ms)", CTRL)
E(main, t0)
t0_chk  = V(col_xs[0]+60, task_tops[0]+60, 180, 60, "I1 = 0 ?", DEC)
t0_rd   = V(col_xs[0]+30, task_tops[0]+155, 240, 55, "Đọc UART → S1", FLOW)
t0_set  = V(col_xs[0]+30, task_tops[0]+235, 240, 55, "I1 = 1", FLOW)
E(t0, t0_chk)
E(t0_chk, t0_rd,  "có",    ARR)
E(t0_rd,  t0_set)
# "không" loops back
V(col_xs[0]+260, task_tops[0]+80, 80, 25, "không", ANN)

# ── TASK1CRC ──────────────────────────────────────────────────────────────
t1 = V(col_xs[1], task_tops[1], COL_W-20, 35, "TASK1CRC  (C = 15 ms)", CTRL)
E(main, t1)
t1_chk  = V(col_xs[1]+60, task_tops[1]+60, 180, 60, "I1 = 1 ?", DEC)
t1_zero = V(col_xs[1]+30, task_tops[1]+155, 240, 50, "all-zero check", FLOW)
t1_crc  = V(col_xs[1]+30, task_tops[1]+230, 240, 50, "CRC check\n(len payload)", FLOW)
t1_sep  = V(col_xs[1]+30, task_tops[1]+305, 240, 50, "joint_separation\n(6 values)", FLOW)
t1_buf  = V(col_xs[1]+30, task_tops[1]+380, 240, 50, "J[I5] = new_joint\nI5++ ,  I1 = 0", FLOW)
E(t1, t1_chk)
E(t1_chk, t1_zero, "có")
E(t1_zero, t1_crc)
E(t1_crc,  t1_sep)
E(t1_sep,  t1_buf)
V(col_xs[1]+260, task_tops[1]+80, 80, 25, "không", ANN)

# ── Ring Buffer  (spans below T1 and T3) ──────────────────────────────────
rb_x, rb_y = col_xs[1]+20, task_tops[1]+455
rb_w, rb_h = 1060, 90
V(rb_x, rb_y, rb_w, rb_h, "Ring Buffer  J[0] … J[99]", GRP)
# cell slots
slot_w = 65
for si, lab in enumerate(["J[0]","J[1]","J[2]","…","J[98]","J[99]"]):
    V(rb_x+20+si*slot_w, rb_y+30, slot_w-4, 40, lab, FLOW)
V(rb_x+20,               rb_y+72, 80, 16, "← I4 (read)", ANN)
V(rb_x+rb_w-100,         rb_y+72, 80, 16, "I5 (write) →", ANN)

# Arrow: T1 writes to buffer
E(t1_buf, V(rb_x+400, rb_y, 1, 1, "", "point;x=0;y=0;"), "", ARRD)

# ── TASK3 ────────────────────────────────────────────────────────────────
t3 = V(col_xs[2], task_tops[2], COL_W-20, 35, "TASK3  (C = 35 ms)", CTRL)
E(main, t3)
t3_chk = V(col_xs[2]+60, task_tops[2]+60, 200, 60, "I4 < I5 ?", DEC)
t3_drv = V(col_xs[2]+30, task_tops[2]+155, 240, 55, "DriveA  J[I4]", FLOW)
t3_inc = V(col_xs[2]+30, task_tops[2]+235, 240, 55, "I4 + 1", FLOW)
E(t3, t3_chk)
E(t3_chk, t3_drv, "có")
E(t3_drv, t3_inc)
V(col_xs[2]+280, task_tops[2]+80, 80, 25, "không", ANN)

# ── GET_JOINT ─────────────────────────────────────────────────────────────
gj = V(col_xs[3], task_tops[3], COL_W-20, 35, "GET_JOINT  (C = 100 ms)", CTRL)
E(main, gj)
gj_read = V(col_xs[3]+30, task_tops[3]+60,  240, 55, "CURJNT\n(6-axis position)", FLOW)
gj_send = V(col_xs[3]+30, task_tops[3]+145, 240, 55, "Send UART:\nj1,j2,j3,j4,j5,j6\\r", FLOW)
gj_wait = V(col_xs[3]+30, task_tops[3]+220, 240, 45, "Wait 100 ms", FLOW)
E(gj, gj_read)
E(gj_read, gj_send)
E(gj_send, gj_wait)

# I1 flag annotation
V(col_xs[0]+80, task_tops[0]+310, 440, 20,
  "──── cờ I1 chia sẻ giữa TASK0 ↔ TASK1CRC ────", ANN)


# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 3 — HW Interface Startup Sequence
# Position: (80, 1250) → (1250, 2100)
# ══════════════════════════════════════════════════════════════════════════════
X3, Y3 = 80, 1250
W3 = 1170

ttl(X3, Y3, W3, "3. Luồng khởi động Hardware Interface")
section(X3, Y3, W3, 870, "")

SH = 80    # step box height
SW = 320   # step box width
DH = 65    # description box height

def startup_step(x, y, func, desc_lines):
    box = V(x, y, SW, SH, func, HWI)
    dy = y
    for line in desc_lines:
        V(x + SW + 20, dy, W3 - SW - 40, 22, line, ANN)
        dy += 24
    return box

sy = Y3 + 20
s1 = startup_step(X3+30, sy,
    "on_init()",
    ["▸ Đọc HardwareInfo từ URDF (<ros2_control>)",
     "▸ Khởi tạo vector trạng thái/lệnh theo số trục",
     "▸ Khai báo ROS parameters"])

sy += SH + 30
s2 = startup_step(X3+30, sy,
    "export_state_interfaces()\nexport_command_interfaces()",
    ["▸ Cung cấp state & command interfaces cho Resource Manager",
     "▸ Controller Manager phân phối interfaces cho controller",
     "▸ Mỗi command interface chỉ 1 controller sở hữu"])

sy += SH + 30
s3 = startup_step(X3+30, sy,
    "on_configure()",
    ["▸ Đọc yaml params: motor_id, limits, zero, gear_ratio…",
     "▸ Khởi tạo Motor Driver / Servo Driver",
     "▸ Mở kết nối UART (device, baudrate)"])

sy += SH + 30
s4 = startup_step(X3+30, sy,
    "on_activate()",
    ["▸ Xoay cánh tay về vị trí gốc (homing)",
     "▸ Tạo thread đọc UART liên tục (readToBuffer)"])

E(s1, s2)
E(s2, s3)
E(s3, s4)


# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 4 — Write Flow (DensoInterface → RC5)
# Position: (1320, 1250) → (2700, 2100)
# ══════════════════════════════════════════════════════════════════════════════
X4, Y4 = 1320, 1250
W4 = 1380

ttl(X4, Y4, W4, "4. Luồng điều khiển (Write) — DensoInterface")
section(X4, Y4, W4, 870, "")

BW = 280   # block width
BH = 60    # block height
bx = X4 + 50
by = Y4 + 25

# "for each joint" annotation
V(bx, by, BW+60, 22, "┌── For each joint (i = 0 … 5) ──", ANN)
by += 26

w_thr  = V(bx+60, by, 200, 70, "diff ≥ 0.001 rad ?", DEC)
by += 100

w_trend = V(bx+20, by, BW, BH, "Trend Learning\n(xu hướng tăng/giảm)", FLOW)
by += BH + 20

w_set   = V(bx+20, by, BW, BH, "setJointPosition(i, cmd)", HWI)
by += BH + 30

V(bx, by, BW+60, 22, "└── end for ──────────────────────────────────", ANN)
by += 30

w_wcmd  = V(bx+20, by, BW, BH, "writeCommand()\n→ collect 6 joint values", HWI)
by += BH + 20

w_spos  = V(bx+20, by, BW, BH, "sendPosition(joints[])\n→ build UART string", DRV)
by += BH + 20

w_smsg  = V(bx+20, by, BW, BH, "sendMsg()\n→ J1,J2,J3,J4,J5,J6#LEN", DRV)
by += BH + 20

w_rc5   = V(bx+20, by, BW, BH, "RC5 Controller", HW)

# "skip" branch
skip_x = bx + BW + 80
skip_lbl = V(skip_x, Y4+70, 120, 26, "không: skip", ANN)

E(w_thr, w_trend, "có")
E(w_trend, w_set)
E(w_set, w_wcmd, "", ARRD)   # dashed to indicate "after loop"
E(w_wcmd, w_spos)
E(w_spos, w_smsg)
E(w_smsg, w_rc5)


# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 5 — Read Flow (RC5 → DensoInterface)
# Position: (2800, 1250) → (4050, 2100)
# ══════════════════════════════════════════════════════════════════════════════
X5, Y5 = 2800, 1250
W5 = 1250

ttl(X5, Y5, W5, "5. Luồng đọc (Read) — DensoInterface")
section(X5, Y5, W5, 870, "")

rx = X5 + 50
ry = Y5 + 25

r_rc5   = V(rx+20, ry,       BW, BH, "RC5 Controller\n(gửi joint state mỗi 100ms)", HW)
ry += BH + 20
r_uart  = V(rx+20, ry,       BW, BH, "UART Buffer\n(readToBuffer thread)", DRV)
ry += BH + 20

V(rx, ry, BW+60, 22, "┌── while buffer not empty ──", ANN)
ry += 26

r_get   = V(rx+20, ry,       BW, BH, "getFromBuffer()\n→ uart string", DRV)
ry += BH + 20

r_dec   = V(rx+20, ry,       BW, BH, "decodeMessage()\n→ double[6]", DRV)
ry += BH + 20

r_store = V(rx+20, ry,       BW, BH, "Store in JointConfig[i]", HWI)
ry += BH + 25

V(rx, ry, BW+60, 22, "└── end while ──────────────────────────────", ANN)
ry += 30

r_getj  = V(rx+20, ry,       BW, BH, "getJointPosition(i)", HWI)
ry += BH + 20

r_state = V(rx+20, ry,       BW, BH, "joint_position_[i]\n(state interface updated)", CTRL)

E(r_rc5,   r_uart)
E(r_uart,  r_get)
E(r_get,   r_dec)
E(r_dec,   r_store)
E(r_store, r_getj, "", ARRD)
E(r_getj,  r_state)


# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 6 — VR Application Architecture
# Position: (4150, 80) → (6100, 1160)
# ══════════════════════════════════════════════════════════════════════════════
X6, Y6 = 4150, 80
W6 = 1950

ttl(X6, Y6, W6, "6. Kiến trúc ứng dụng VR (Unity + Meta Quest 3)")
section(X6, Y6, W6, 1080, "")

# ── ROS2 PC (left) ────────────────────────────────────────────────────────
ros2_pc = V(X6+20, Y6+330, 280, 200,
             "PC Controller\n(Ubuntu 22.04)\nROS2 Humble\n+ MoveIt2\n+ RosBridge\n  Server :9090",
             "rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontStyle=1;fontSize=12;")

# ── ROS Connector (centre) ────────────────────────────────────────────────
conn = V(X6+520, Y6+400, 240, 90,
         "ROS Connector\n(WebSocket / RosBridge)",
         "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontStyle=1;fontSize=12;")

E(ros2_pc, conn, "WebSocket", ARRB)

# ── Subscribers (top-right of connector) ──────────────────────────────────
sub_y = Y6 + 130
sub_x = X6 + 900
jsub  = V(sub_x, sub_y,      300, 55, "Joint State Subscriber\n(/joint_states)", HWI)
isub  = V(sub_x, sub_y+75,   300, 55, "Compressed Image Subscriber\n(/camera/compressed)", HWI)
E(conn, jsub,  "subscribe", ARRD)
E(conn, isub,  "subscribe", ARRD)

# ── Publishers / Clients (bottom-right of connector) ──────────────────────
pub_y = Y6 + 320
jjog  = V(sub_x, pub_y,       300, 50, "Joint Jog Publisher\n(delta_joint_cmds)", APP)
twist = V(sub_x, pub_y+65,    300, 50, "Twist Stamped Publisher\n(delta_twist_cmds)", APP)
trig  = V(sub_x, pub_y+130,   300, 50, "Trigger Service Consumer\n(start/stop servo)", APP)
grip  = V(sub_x, pub_y+195,   300, 50, "Gripper Command Action Client", APP)
mtp   = V(sub_x, pub_y+260,   300, 50, "Move To Pose Action Client", APP)
for pub in [jjog, twist, trig, grip, mtp]:
    E(pub, conn, "publish/call", ARRD)

# ── UI Panels + 3D Models (right column) ──────────────────────────────────
ui_x = X6 + 1340
ui_y = Y6 + 50
pan_con  = V(ui_x, ui_y,       260, 55, "Connect Panel\n(IP, port, connect button)", FLOW)
pan_srv  = V(ui_x, ui_y+75,    260, 55, "MoveIt-Servo Panel\n(joint / XYZ mode)", FLOW)
pan_jrot = V(ui_x, ui_y+150,   260, 55, "Joint Rotate Panel\n(grab & rotate each joint)", FLOW)
pan_grab = V(ui_x, ui_y+225,   260, 55, "Grab Rotate Panel\n(grab object & rotate)", FLOW)
mod_den  = V(ui_x, ui_y+330,   260, 55, "Denso Robot 3D Model\n(live joint sync)", HW)
mod_fut  = V(ui_x, ui_y+405,   260, 55, "Future Denso Robot 3D\n(Grab Interactable)", HW)

# Data flow: subscriber → 3D model
E(jsub, mod_den, "joint angles", ARRD)

# Panel → publisher linkages (dashed)
E(pan_con,  conn,  "", ARRD)
E(pan_srv,  jjog,  "", ARRD)
E(pan_srv,  twist, "", ARRD)
E(pan_srv,  trig,  "", ARRD)
E(pan_jrot, grip,  "", ARRD)
E(pan_grab, mtp,   "", ARRD)

# Camera image → raw image display
raw_img = V(ui_x, ui_y+480, 260, 50, "Raw Image Display\n(compressed → Texture2D)", FLOW)
E(isub, raw_img, "", ARRD)

# ── Group labels ──────────────────────────────────────────────────────────
V(sub_x-10,  Y6+90,  50, 20, "Sub", ANN)
V(sub_x-10,  pub_y-25, 50, 20, "Pub", ANN)
V(ui_x-10,   ui_y-25,  120, 20, "UI / 3D Models", ANN)


# ══════════════════════════════════════════════════════════════════════════════
# Assemble XML
# ══════════════════════════════════════════════════════════════════════════════
cells_xml = "\n".join(cells)

NEW_TRANG2 = f'''\
  <diagram id="GCY5zNjh8045J0asGFp4" name="Trang-2">
    <mxGraphModel grid="1" page="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" pageScale="1" pageWidth="1654" pageHeight="2339" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
{cells_xml}
      </root>
    </mxGraphModel>
  </diagram>'''

# ══════════════════════════════════════════════════════════════════════════════
# Patch Thesis.drawio
# ══════════════════════════════════════════════════════════════════════════════
import os, pathlib

repo = pathlib.Path(__file__).resolve().parent.parent
drawio_path = repo / "Thesis.drawio"

content = drawio_path.read_text(encoding="utf-8")

# Replace everything between <diagram ... name="Trang-2"> and </diagram>
pattern = r'(<diagram\b[^>]*name="Trang-2"[^>]*>).*?(</diagram>)'
replacement = NEW_TRANG2
new_content = re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)

if new_content == content:
    print("ERROR: Pattern not matched — Trang-2 not found!")
else:
    drawio_path.write_text(new_content, encoding="utf-8")
    print(f"OK — Trang-2 replaced with {len(cells)} cells.")
    print(f"Saved to: {drawio_path}")
