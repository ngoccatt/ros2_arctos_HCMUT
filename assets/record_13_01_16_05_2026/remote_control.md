arctos@arctos-HP-EliteDesk-705-G4-DM-35W-TAA:~/ros2_ws$ ros2 launch denso_remote_control remote_control.launch.py 
[INFO] [launch]: All log files can be found below /home/arctos/.ros/log/2026-05-16-12-32-53-299545-arctos-HP-EliteDesk-705-G4-DM-35W-TAA-123671
[INFO] [launch]: Default logging verbosity is set to INFO
[INFO] [launch.user]: Launching remoteControl with...
[INFO] [launch.user]: use_sim_time: true
[INFO] [remote_control_server_executer-1]: process started with pid [123692]
[remote_control_server_executer-1] [WARN] [1778909573.656010813] [rcl.logging_rosout]: Publisher already registered for provided node name. If this is due to multiple nodes with the same name then all logs for that logger name will go out over the existing publisher. As soon as any node with that name is destructed it will unregister the publisher, preventing any further logs for that name from being published on the rosout topic.
[remote_control_server_executer-1] [INFO] [1778909573.666957894] [moveit_rdf_loader.rdf_loader]: Loaded robot model in 0 seconds
[remote_control_server_executer-1] [INFO] [1778909573.667005434] [moveit_robot_model.robot_model]: Loading robot model 'arctos'...
[remote_control_server_executer-1] [INFO] [1778909573.852420829] [move_group_interface]: Ready to take commands for planning group denso_arm.
[remote_control_server_executer-1] [INFO] [1778909573.853323148] [moveit_ros.current_state_monitor]: Listening to joint states on topic 'joint_states'
[remote_control_server_executer-1] [INFO] [1778910078.612146183] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 0.000000 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1778910078.612837038] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910078.613166371] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910078.613374959] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910078.613949198] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910078.714362531] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910078.715035864] [move_group_interface]: time taken to generate plan: 0.0131734 seconds
[remote_control_server_executer-1] [INFO] [1778910078.715158201] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910078.716131192] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910083.094834508] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910083.095441578] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910106.052479821] [remote_control_server_executer]: Received goal request with Joint position: -1.321494 0.000000 0.000000 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1778910106.052732081] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910106.052826276] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910106.052973911] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910106.053368886] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910106.115759797] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910106.116508872] [move_group_interface]: time taken to generate plan: 0.0125288 seconds
[remote_control_server_executer-1] [INFO] [1778910106.116625248] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910106.117312257] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910111.294679778] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910111.295751784] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910126.684130945] [remote_control_server_executer]: Received goal request with Joint position: -1.321494 -0.881263 2.001208 0.000000 0.394485 0.000000
[remote_control_server_executer-1] [INFO] [1778910126.684358388] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910126.684472972] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910126.684626447] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910126.685040829] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910126.719008740] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910126.719464930] [move_group_interface]: time taken to generate plan: 0.0157345 seconds
[remote_control_server_executer-1] [INFO] [1778910126.719575445] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910126.720485410] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910133.294556020] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910133.295151078] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910146.777402973] [remote_control_server_executer]: Received goal request with Joint position: -1.321494 -0.881263 2.001208 0.000000 0.394485 -1.630721
[remote_control_server_executer-1] [INFO] [1778910146.777628623] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910146.777734290] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910146.777907032] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910146.778400040] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910146.823411832] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910146.824480793] [move_group_interface]: time taken to generate plan: 0.0243662 seconds
[remote_control_server_executer-1] [INFO] [1778910146.824652172] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910146.825697128] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910150.094737424] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910150.095987392] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910171.399600256] [remote_control_server_executer]: Received goal request with Joint position: 1.320250 -0.881263 2.001208 0.000000 0.394485 -1.630721
[remote_control_server_executer-1] [INFO] [1778910171.399815197] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910171.399945650] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910171.400140914] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910171.400671673] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910171.520568981] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910171.520872556] [move_group_interface]: time taken to generate plan: 0.0144898 seconds
[remote_control_server_executer-1] [INFO] [1778910171.520958847] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910171.521839037] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910180.994554077] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910180.995074697] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910191.133783606] [remote_control_server_executer]: Received goal request with Joint position: 1.320250 -0.881263 2.001208 0.000000 0.446513 0.138172
[remote_control_server_executer-1] [INFO] [1778910191.134099665] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910191.134296222] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910191.134531150] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910191.135210917] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910191.210285945] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910191.211131511] [move_group_interface]: time taken to generate plan: 0.0123066 seconds
[remote_control_server_executer-1] [INFO] [1778910191.211385234] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910191.212398372] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910194.694659522] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910194.695051092] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910199.982366738] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 0.000000 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1778910199.982610672] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910199.982730416] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910199.982929076] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910199.983471958] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910200.017707024] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910200.018331518] [move_group_interface]: time taken to generate plan: 0.0141943 seconds
[remote_control_server_executer-1] [INFO] [1778910200.018474284] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910200.019466173] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910206.595173741] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910206.596404355] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910253.620927410] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 0.000000 0.000000 1.247025 0.000000
[remote_control_server_executer-1] [INFO] [1778910253.621195861] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910253.621335101] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910253.621540233] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910253.622045476] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910253.714122880] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910253.714819109] [move_group_interface]: time taken to generate plan: 0.0154746 seconds
[remote_control_server_executer-1] [INFO] [1778910253.715007600] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910253.715889365] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910257.194635568] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910257.195428166] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910274.312974758] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 0.000000 0.000000 1.247025 -1.519066
[remote_control_server_executer-1] [INFO] [1778910274.313273996] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910274.313412104] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910274.313607508] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910274.314177332] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910274.413674832] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910274.414793339] [move_group_interface]: time taken to generate plan: 0.013826 seconds
[remote_control_server_executer-1] [INFO] [1778910274.414988343] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910274.416137708] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910277.595416956] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910277.596172636] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910292.379770218] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 0.000000 -1.465138 1.485080 -0.064679
[remote_control_server_executer-1] [INFO] [1778910292.380550394] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910292.380693381] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910292.380862998] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910292.381288472] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910292.414984264] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910292.415890495] [move_group_interface]: time taken to generate plan: 0.0141056 seconds
[remote_control_server_executer-1] [INFO] [1778910292.416036056] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910292.416750369] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910296.294558132] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910296.295580640] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910306.679670080] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 0.000000 -1.465138 0.008276 -0.269675
[remote_control_server_executer-1] [INFO] [1778910306.679959450] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910306.680080716] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910306.680274548] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910306.680773119] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910306.714757559] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910306.715655194] [move_group_interface]: time taken to generate plan: 0.0140529 seconds
[remote_control_server_executer-1] [INFO] [1778910306.715749891] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910306.717823191] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910310.595806344] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910310.596541376] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910326.552943533] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 1.557166 0.042884 0.008276 -0.269675
[remote_control_server_executer-1] [INFO] [1778910326.553327820] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910326.553453976] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910326.553641406] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910326.554109249] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910326.615741217] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910326.615782063] [move_group_interface]: time taken to generate plan: 0.0140531 seconds
[remote_control_server_executer-1] [INFO] [1778910326.615878363] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910326.618026863] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910331.994693157] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910331.995054592] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910368.795590820] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.590580 2.166641 -0.023802 0.388187 -0.269675
[remote_control_server_executer-1] [INFO] [1778910368.795875502] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910368.796013149] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910368.796199136] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910368.796623218] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910368.911001345] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910368.911259908] [move_group_interface]: time taken to generate plan: 0.0132164 seconds
[remote_control_server_executer-1] [INFO] [1778910368.911364142] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910368.912253002] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910371.494781051] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910371.495975252] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910430.249791498] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.674441 2.166641 -0.053928 0.388187 -0.269675
[remote_control_server_executer-1] [INFO] [1778910430.250084084] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910430.250211262] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910430.250403030] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910430.250882887] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910430.311655331] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910430.312073292] [move_group_interface]: time taken to generate plan: 0.0155864 seconds
[remote_control_server_executer-1] [INFO] [1778910430.312194148] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910430.312800411] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910431.395025686] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910431.396206011] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910437.154919735] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.674441 2.102174 -0.053928 0.388187 -0.269675
[remote_control_server_executer-1] [INFO] [1778910437.155192806] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910437.155316988] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910437.155576202] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910437.156532950] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910437.222157739] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910437.222302890] [move_group_interface]: time taken to generate plan: 0.0242067 seconds
[remote_control_server_executer-1] [INFO] [1778910437.222482706] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910437.223447760] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910438.294968858] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910438.295747774] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910474.692596581] [remote_control_server_executer]: Received goal request with Joint position: 0.094291 0.674441 2.102174 -0.053928 0.388187 -0.269675
[remote_control_server_executer-1] [INFO] [1778910474.692891112] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910474.692987482] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910474.693150266] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910474.693568278] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910474.709255282] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910474.709435710] [move_group_interface]: time taken to generate plan: 0.0129433 seconds
[remote_control_server_executer-1] [INFO] [1778910474.709559010] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910474.710736241] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910475.895937414] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910475.896979261] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910487.678370666] [remote_control_server_executer]: Received goal request with Joint position: 0.094291 0.745129 2.102174 -0.053928 0.388187 -0.269675
[remote_control_server_executer-1] [INFO] [1778910487.678601337] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910487.678710922] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910487.678863337] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910487.679272923] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910487.710763546] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910487.711310258] [move_group_interface]: time taken to generate plan: 0.013576 seconds
[remote_control_server_executer-1] [INFO] [1778910487.711401007] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910487.711852131] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910488.794755364] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910488.795672719] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910508.868461223] [remote_control_server_executer]: Received goal request with Joint position: 0.094291 0.255553 1.134803 -0.053928 0.388187 -0.269675
[remote_control_server_executer-1] [INFO] [1778910508.868729074] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910508.868830153] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910508.869001574] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910508.869474308] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910508.913070605] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910508.913097054] [move_group_interface]: time taken to generate plan: 0.0122062 seconds
[remote_control_server_executer-1] [INFO] [1778910508.913948216] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910508.914880229] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910512.594923825] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910512.596451853] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910518.328756181] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 0.000000 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1778910518.329053487] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910518.329169934] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910518.329357245] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910518.329841931] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910518.415087506] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910518.416011424] [move_group_interface]: time taken to generate plan: 0.0145598 seconds
[remote_control_server_executer-1] [INFO] [1778910518.416154552] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910518.417354385] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910523.194589343] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910523.195553596] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910563.990073225] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 0.000000 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1778910563.990403633] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910563.990525511] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910563.990699807] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910563.991158465] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910564.009671795] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910564.010195845] [move_group_interface]: time taken to generate plan: 0.013655 seconds
[remote_control_server_executer-1] [INFO] [1778910564.010345145] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910564.010832226] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910564.994633631] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910564.995146230] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910615.292567347] [remote_control_server_executer]: Received goal request with Joint position: 0.177474 0.451251 2.033056 0.000536 0.659276 0.000000
[remote_control_server_executer-1] [INFO] [1778910615.292919105] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910615.293037216] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910615.293201674] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910615.293646566] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910615.317772309] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910615.318844625] [move_group_interface]: time taken to generate plan: 0.0136384 seconds
[remote_control_server_executer-1] [INFO] [1778910615.318938110] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910615.319794282] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910621.994794052] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910621.995540438] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910637.780904723] [remote_control_server_executer]: Received goal request with Joint position: 0.177474 0.570613 2.016143 0.000536 0.659276 0.000000
[remote_control_server_executer-1] [INFO] [1778910637.781188974] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910637.781310101] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910637.781505737] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910637.782222829] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910637.812780464] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910637.812987401] [move_group_interface]: time taken to generate plan: 0.0159954 seconds
[remote_control_server_executer-1] [INFO] [1778910637.813109420] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910637.813558049] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910638.994905375] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910638.995767959] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910646.089399681] [remote_control_server_executer]: Received goal request with Joint position: 0.287792 0.570613 2.016143 0.000536 0.659276 0.000000
[remote_control_server_executer-1] [INFO] [1778910646.089680316] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910646.089786766] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910646.089953979] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910646.090373243] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910646.111308884] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910646.111643039] [move_group_interface]: time taken to generate plan: 0.0150879 seconds
[remote_control_server_executer-1] [INFO] [1778910646.111753907] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910646.112353408] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910647.294813331] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910647.296081404] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910651.250033233] [remote_control_server_executer]: Received goal request with Joint position: 0.159687 0.570613 2.016143 0.000536 0.659276 0.000000
[remote_control_server_executer-1] [INFO] [1778910651.250649867] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910651.250794748] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910651.251046770] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910651.251656020] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910651.311266763] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910651.311759775] [move_group_interface]: time taken to generate plan: 0.0139531 seconds
[remote_control_server_executer-1] [INFO] [1778910651.311897824] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910651.312463953] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910652.595059867] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910652.596013361] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910836.794438630] [remote_control_server_executer]: Received goal request with Joint position: 1.687988 0.000000 1.452787 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1778910836.794768699] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910836.794877653] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910836.795036290] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910836.795454233] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910836.917192413] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910836.917768993] [move_group_interface]: time taken to generate plan: 0.01501 seconds
[remote_control_server_executer-1] [INFO] [1778910836.917921970] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910836.918927423] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910842.995629851] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910842.996691189] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910872.629554499] [remote_control_server_executer]: Received goal request with Joint position: 0.781552 -0.219933 2.157591 -0.321461 -0.114377 0.000000
[remote_control_server_executer-1] [INFO] [1778910872.629838250] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910872.629959838] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910872.630130287] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910872.630565753] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910872.725246996] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910872.725408940] [move_group_interface]: time taken to generate plan: 0.0249397 seconds
[remote_control_server_executer-1] [INFO] [1778910872.725505811] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910872.726924850] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910876.494994863] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910876.495478699] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910887.118502920] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 0.000000 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1778910887.118875298] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910887.119036009] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910887.119299362] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910887.120084263] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910887.221564513] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910887.222683599] [move_group_interface]: time taken to generate plan: 0.0173727 seconds
[remote_control_server_executer-1] [INFO] [1778910887.222854770] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910887.223787878] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910894.296169756] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910894.297263936] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910929.984228337] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 0.000000 -1.630689 -1.570796 0.000000
[remote_control_server_executer-1] [INFO] [1778910929.984522478] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910929.984638976] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910929.984799928] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910929.985253838] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910930.013407751] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910930.014272020] [move_group_interface]: time taken to generate plan: 0.0127835 seconds
[remote_control_server_executer-1] [INFO] [1778910930.014438562] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910930.015414952] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910934.195961055] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910934.196585114] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910942.193250334] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 0.000000 -1.630689 1.570796 0.000000
[remote_control_server_executer-1] [INFO] [1778910942.193553232] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910942.193672656] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910942.193869875] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910942.194527968] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910942.316306277] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910942.317088944] [move_group_interface]: time taken to generate plan: 0.0139537 seconds
[remote_control_server_executer-1] [INFO] [1778910942.317214059] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910942.318215244] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910949.395768785] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910949.396592028] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910952.797543726] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 0.000000 -1.630689 1.570796 0.000000
[remote_control_server_executer-1] [INFO] [1778910952.797836534] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910952.797954415] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910952.798129694] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910952.798942236] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910952.909468127] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910952.910335112] [move_group_interface]: time taken to generate plan: 0.0126022 seconds
[remote_control_server_executer-1] [INFO] [1778910952.910514387] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910952.911149758] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910954.794761558] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910954.795643190] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778910959.002696926] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 0.000000 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1778910959.003055398] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778910959.003163982] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778910959.003346654] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778910959.003998596] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778910959.114804555] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778910959.115576422] [move_group_interface]: time taken to generate plan: 0.014236 seconds
[remote_control_server_executer-1] [INFO] [1778910959.115704923] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778910959.116397270] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778910963.296051385] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778910963.297233390] [remote_control_server_executer]: Goal succeeded
^C[WARNING] [launch]: user interrupted with ctrl-c (SIGINT)
[remote_control_server_executer-1] [INFO] [1778911202.534897798] [rclcpp]: signal_handler(SIGINT/SIGTERM)
[INFO] [remote_control_server_executer-1]: process has finished cleanly [pid 123692]
