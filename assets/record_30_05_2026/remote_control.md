arctos@arctos-HP-EliteDesk-705-G4-DM-35W-TAA:~/ros2_ws$ ros2 launch denso_remote_control remote_control.launch.py 
[INFO] [launch]: All log files can be found below /home/arctos/.ros/log/2026-05-30-11-27-59-701083-arctos-HP-EliteDesk-705-G4-DM-35W-TAA-10996
[INFO] [launch]: Default logging verbosity is set to INFO
[INFO] [launch.user]: Launching remoteControl with...
[INFO] [launch.user]: use_sim_time: true
[INFO] [remote_control_server_executer-1]: process started with pid [10997]
[remote_control_server_executer-1] [WARN] [1780115280.038335691] [rcl.logging_rosout]: Publisher already registered for provided node name. If this is due to multiple nodes with the same name then all logs for that logger name will go out over the existing publisher. As soon as any node with that name is destructed it will unregister the publisher, preventing any further logs for that name from being published on the rosout topic.
[remote_control_server_executer-1] [INFO] [1780115280.048430300] [moveit_rdf_loader.rdf_loader]: Loaded robot model in 0 seconds
[remote_control_server_executer-1] [INFO] [1780115280.048471017] [moveit_robot_model.robot_model]: Loading robot model 'denso'...
[remote_control_server_executer-1] [INFO] [1780115280.223916777] [move_group_interface]: Ready to take commands for planning group denso_arm.
[remote_control_server_executer-1] [INFO] [1780115280.224696475] [moveit_ros.current_state_monitor]: Listening to joint states on topic 'joint_states'
^C[WARNING] [launch]: user interrupted with ctrl-c (SIGINT)
[remote_control_server_executer-1] [INFO] [1780116219.873648814] [rclcpp]: signal_handler(SIGINT/SIGTERM)
[INFO] [remote_control_server_executer-1]: process has finished cleanly [pid 10997]
arctos@arctos-HP-EliteDesk-705-G4-DM-35W-TAA:~/ros2_ws$ ros2 launch denso_remote_control remote_control.launch.py 
[INFO] [launch]: All log files can be found below /home/arctos/.ros/log/2026-05-30-11-45-54-213573-arctos-HP-EliteDesk-705-G4-DM-35W-TAA-24815
[INFO] [launch]: Default logging verbosity is set to INFO
[INFO] [launch.user]: Launching remoteControl with...
[INFO] [launch.user]: use_sim_time: true
[INFO] [remote_control_server_executer-1]: process started with pid [24832]
[remote_control_server_executer-1] [WARN] [1780116354.581215903] [rcl.logging_rosout]: Publisher already registered for provided node name. If this is due to multiple nodes with the same name then all logs for that logger name will go out over the existing publisher. As soon as any node with that name is destructed it will unregister the publisher, preventing any further logs for that name from being published on the rosout topic.
[remote_control_server_executer-1] [INFO] [1780116354.591562940] [moveit_rdf_loader.rdf_loader]: Loaded robot model in 0 seconds
[remote_control_server_executer-1] [INFO] [1780116354.591603406] [moveit_robot_model.robot_model]: Loading robot model 'denso'...
[remote_control_server_executer-1] [INFO] [1780116354.772298209] [move_group_interface]: Ready to take commands for planning group denso_arm.
[remote_control_server_executer-1] [INFO] [1780116354.772856105] [moveit_ros.current_state_monitor]: Listening to joint states on topic 'joint_states'
[remote_control_server_executer-1] [INFO] [1780117607.887303104] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 0.000000 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1780117607.887992714] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1780117607.888423867] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1780117607.888717211] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1780117607.889308405] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1780117607.993543067] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1780117607.994376890] [move_group_interface]: time taken to generate plan: 0.014012 seconds
[remote_control_server_executer-1] [INFO] [1780117607.994488450] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1780117607.995263672] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1780117612.672729460] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1780117612.673966943] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1780118284.359003254] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 0.000000 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1780118284.359241060] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1780118284.359347970] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1780118284.359537786] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1780118284.360575833] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1780118284.395974809] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1780118284.396096267] [move_group_interface]: time taken to generate plan: 0.0148975 seconds
[remote_control_server_executer-1] [INFO] [1780118284.396191916] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1780118284.397025109] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1780118289.573605950] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1780118289.574372317] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1780118297.300273144] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 1.578515 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1780118297.300506783] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1780118297.300621868] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1780118297.300822905] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1780118297.301305851] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1780118297.391041265] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1780118297.392021533] [move_group_interface]: time taken to generate plan: 0.0123449 seconds
[remote_control_server_executer-1] [INFO] [1780118297.392132050] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1780118297.392834548] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1780118302.776656089] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1780118302.777337037] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1780118310.190797812] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 0.257392 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1780118310.191071765] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1780118310.191197181] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1780118310.191389201] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1780118310.191894228] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1780118310.292411624] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1780118310.292517242] [move_group_interface]: time taken to generate plan: 0.0138405 seconds
[remote_control_server_executer-1] [INFO] [1780118310.292656524] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1780118310.293655637] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1780118314.972314441] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1780118314.973233946] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1780118676.299736037] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 0.000000 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1780118676.299969154] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1780118676.300064152] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1780118676.300217609] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1780118676.300639560] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1780118676.395091750] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1780118676.395479456] [move_group_interface]: time taken to generate plan: 0.0156336 seconds
[remote_control_server_executer-1] [INFO] [1780118676.395571990] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1780118676.396251823] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1780118682.473008078] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1780118682.473683684] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1780118708.624554183] [remote_control_server_executer]: Received goal request with Joint position: 0.524954 -0.347112 1.449162 0.937325 0.649984 0.000000
[remote_control_server_executer-1] [INFO] [1780118708.624947810] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1780118708.625168363] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1780118708.625559877] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1780118708.626485411] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1780118708.694468760] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1780118708.694861636] [move_group_interface]: time taken to generate plan: 0.0141735 seconds
[remote_control_server_executer-1] [INFO] [1780118708.695019873] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1780118708.695953682] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1780118713.774649207] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1780118713.775911101] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1780118724.678529011] [remote_control_server_executer]: Received goal request with Joint position: 0.524954 -0.347112 1.449162 0.937325 0.649984 -1.322391
[remote_control_server_executer-1] [INFO] [1780118724.678745056] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1780118724.678842038] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1780118724.678997208] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1780118724.679445739] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1780118724.791129537] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1780118724.791453404] [move_group_interface]: time taken to generate plan: 0.0142047 seconds
[remote_control_server_executer-1] [INFO] [1780118724.791612742] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1780118724.792891789] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1780118727.772379291] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1780118727.773518896] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1780118732.933003685] [remote_control_server_executer]: Received goal request with Joint position: 0.524954 -0.347112 1.449162 0.937325 0.649984 -0.776949
[remote_control_server_executer-1] [INFO] [1780118732.933286084] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1780118732.933460941] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1780118732.933720718] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1780118732.934548599] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1780118732.987053475] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1780118732.987752074] [move_group_interface]: time taken to generate plan: 0.0123784 seconds
[remote_control_server_executer-1] [INFO] [1780118732.987853534] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1780118732.988359131] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1780118734.972271753] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1780118734.972887617] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1780118745.367513404] [remote_control_server_executer]: Received goal request with Joint position: -1.012058 -0.347112 1.449162 0.937325 0.649984 -0.776949
[remote_control_server_executer-1] [INFO] [1780118745.367783420] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1780118745.367888858] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1780118745.368080226] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1780118745.368533004] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1780118745.388739430] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1780118745.389521324] [move_group_interface]: time taken to generate plan: 0.0114952 seconds
[remote_control_server_executer-1] [INFO] [1780118745.389667588] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1780118745.390473659] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1780118751.272919176] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1780118751.273268791] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1780118787.226300159] [remote_control_server_executer]: Received goal request with Joint position: -0.026032 -0.055422 2.162096 -0.028295 0.913661 0.132470
[remote_control_server_executer-1] [INFO] [1780118787.226769829] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1780118787.226938956] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1780118787.227136355] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1780118787.227680925] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1780118787.292318070] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1780118787.292393682] [move_group_interface]: time taken to generate plan: 0.0143704 seconds
[remote_control_server_executer-1] [INFO] [1780118787.292483951] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1780118787.293365172] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1780118791.372504880] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1780118791.372690357] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1780118799.247338148] [remote_control_server_executer]: Received goal request with Joint position: -0.026032 -0.055422 1.455620 -0.028295 0.872584 0.132470
[remote_control_server_executer-1] [INFO] [1780118799.247684307] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1780118799.247831082] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1780118799.248295011] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1780118799.249099658] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1780118799.299403421] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1780118799.299751623] [move_group_interface]: time taken to generate plan: 0.0236479 seconds
[remote_control_server_executer-1] [INFO] [1780118799.299848184] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1780118799.300434993] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1780118802.173035852] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1780118802.173995740] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1780118808.244609921] [remote_control_server_executer]: Received goal request with Joint position: -0.026032 -0.055422 1.455620 -0.028295 1.570796 0.132470
[remote_control_server_executer-1] [INFO] [1780118808.244886149] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1780118808.245029497] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1780118808.245221307] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1780118808.246091978] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1780118808.288994635] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1780118808.289521101] [move_group_interface]: time taken to generate plan: 0.0136135 seconds
[remote_control_server_executer-1] [INFO] [1780118808.289682373] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1780118808.290384008] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1780118810.672434468] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1780118810.673354491] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1780118817.348478221] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 0.000000 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1780118817.348823137] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1780118817.348961106] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1780118817.349179645] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1780118817.349811078] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1780118817.395472552] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1780118817.395489925] [move_group_interface]: time taken to generate plan: 0.0144064 seconds
[remote_control_server_executer-1] [INFO] [1780118817.395612174] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1780118817.396625282] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1780118822.474100903] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1780118822.474789703] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1780118876.543755736] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 1.553287 -0.760620 1.412522 -0.070480
[remote_control_server_executer-1] [INFO] [1780118876.544100682] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1780118876.544240324] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1780118876.544388762] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1780118876.544844425] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1780118876.595212769] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1780118876.595820317] [move_group_interface]: time taken to generate plan: 0.0147214 seconds
[remote_control_server_executer-1] [INFO] [1780118876.596131210] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1780118876.597066422] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1780118881.873787585] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1780118881.875175585] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1780118903.074513460] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.552659 1.742763 -0.013610 0.729511 -0.070480
[remote_control_server_executer-1] [INFO] [1780118903.074817269] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1780118903.074984041] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1780118903.075202500] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1780118903.077198409] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1780118903.191723677] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1780118903.192682984] [move_group_interface]: time taken to generate plan: 0.0153738 seconds
[remote_control_server_executer-1] [INFO] [1780118903.192784965] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1780118903.193301543] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1780118905.773962012] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1780118905.774231627] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1780118918.260878781] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.552659 0.762456 -0.013610 0.729511 -0.070480
[remote_control_server_executer-1] [INFO] [1780118918.261128118] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1780118918.261225230] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1780118918.261377586] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1780118918.261822198] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1780118918.290559303] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1780118918.291250107] [move_group_interface]: time taken to generate plan: 0.0134477 seconds
[remote_control_server_executer-1] [INFO] [1780118918.291408844] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1780118918.292000722] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1780118921.972383552] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1780118921.972657996] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1780118949.214922330] [remote_control_server_executer]: Received goal request with Joint position: 0.875548 -0.545478 2.040604 -0.013610 0.071324 -0.070480
[remote_control_server_executer-1] [INFO] [1780118949.215205430] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1780118949.215324904] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1780118949.215521522] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1780118949.215948882] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1780118949.292849131] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1780118949.293086295] [move_group_interface]: time taken to generate plan: 0.0144992 seconds
[remote_control_server_executer-1] [INFO] [1780118949.293205669] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1780118949.293837903] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1780118953.872655885] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1780118953.872961147] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1780118968.322245108] [remote_control_server_executer]: Received goal request with Joint position: -0.735610 -0.545478 2.040604 -0.013610 0.071324 -0.070480
[remote_control_server_executer-1] [INFO] [1780118968.323093096] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1780118968.323294353] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1780118968.323470082] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1780118968.324904729] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1780118968.393992202] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1780118968.394669491] [move_group_interface]: time taken to generate plan: 0.0134386 seconds
[remote_control_server_executer-1] [INFO] [1780118968.394866009] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1780118968.396135246] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1780118974.472780929] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1780118974.474056057] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1780118995.016758472] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 0.000000 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1780118995.017025482] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1780118995.017173970] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1780118995.017382190] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1780118995.017920328] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1780118995.104287460] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1780118995.104920646] [move_group_interface]: time taken to generate plan: 0.0234862 seconds
[remote_control_server_executer-1] [INFO] [1780118995.105035731] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1780118995.106502388] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1780119001.772661666] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1780119001.773853939] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1780119058.801883086] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 1.625585 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1780119058.802212302] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1780119058.802354182] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1780119058.802591753] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1780119058.803093567] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1780119058.893261800] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1780119058.893417116] [move_group_interface]: time taken to generate plan: 0.0142517 seconds
[remote_control_server_executer-1] [INFO] [1780119058.893520091] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1780119058.894227466] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1780119064.472391359] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1780119064.472791970] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1780119132.604181431] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 1.625585 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1780119132.604517859] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1780119132.604670439] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1780119132.604857885] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1780119132.605310543] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1780119132.690829149] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1780119132.691579663] [move_group_interface]: time taken to generate plan: 0.0138574 seconds
[remote_control_server_executer-1] [INFO] [1780119132.691699450] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1780119132.692272457] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1780119135.772296087] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1780119135.772934067] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1780119140.581021951] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 0.000000 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1780119140.581750753] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1780119140.581942918] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1780119140.582177473] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1780119140.583099521] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1780119140.693528497] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1780119140.694594949] [move_group_interface]: time taken to generate plan: 0.0149286 seconds
[remote_control_server_executer-1] [INFO] [1780119140.694741377] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1780119140.695583715] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1780119146.272521090] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1780119146.273531487] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1780120109.859332381] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 1.415668 0.000000 1.421954 0.000000
[remote_control_server_executer-1] [INFO] [1780120109.859650519] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1780120109.859820739] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1780120109.860042946] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1780120109.861077189] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1780120109.893650346] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1780120109.893885177] [move_group_interface]: time taken to generate plan: 0.014251 seconds
[remote_control_server_executer-1] [INFO] [1780120109.894033375] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1780120109.894976988] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1780120114.872317256] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1780120114.873421000] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1780120171.070442968] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 1.415668 0.000000 1.421954 0.000000
[remote_control_server_executer-1] [INFO] [1780120171.070744053] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1780120171.070859650] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1780120171.071029980] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1780120171.072052962] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1780120171.188409228] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1780120171.189160208] [move_group_interface]: time taken to generate plan: 0.0134009 seconds
[remote_control_server_executer-1] [INFO] [1780120171.189305010] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1780120171.189925566] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1780120173.672380144] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1780120173.673000800] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1780120180.180026155] [remote_control_server_executer]: Received goal request with Joint position: -1.057473 0.000000 1.415668 0.000000 1.505645 0.000000
[remote_control_server_executer-1] [INFO] [1780120180.180336167] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1780120180.180434030] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1780120180.180617505] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1780120180.181173920] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1780120180.292104621] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1780120180.292782755] [move_group_interface]: time taken to generate plan: 0.013797 seconds
[remote_control_server_executer-1] [INFO] [1780120180.292986057] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1780120180.295001442] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1780120184.572175803] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1780120184.573684296] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1780120189.833807508] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 0.000000 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1780120189.834120286] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1780120189.834238027] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1780120189.834400863] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1780120189.834913195] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1780120189.904941727] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1780120189.905720540] [move_group_interface]: time taken to generate plan: 0.0256818 seconds
[remote_control_server_executer-1] [INFO] [1780120189.905894837] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1780120189.907588448] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1780120194.872607797] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1780120194.873386389] [remote_control_server_executer]: Goal succeeded
