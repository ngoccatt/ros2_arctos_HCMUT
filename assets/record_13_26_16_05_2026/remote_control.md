arctos@arctos-HP-EliteDesk-705-G4-DM-35W-TAA:~/ros2_ws$ ros2 launch denso_remote_control remote_control.launch.py 
[INFO] [launch]: All log files can be found below /home/arctos/.ros/log/2026-05-16-13-14-22-552634-arctos-HP-EliteDesk-705-G4-DM-35W-TAA-154623
[INFO] [launch]: Default logging verbosity is set to INFO
[INFO] [launch.user]: Launching remoteControl with...
[INFO] [launch.user]: use_sim_time: true
[INFO] [remote_control_server_executer-1]: process started with pid [154624]
[remote_control_server_executer-1] [WARN] [1778912062.894545506] [rcl.logging_rosout]: Publisher already registered for provided node name. If this is due to multiple nodes with the same name then all logs for that logger name will go out over the existing publisher. As soon as any node with that name is destructed it will unregister the publisher, preventing any further logs for that name from being published on the rosout topic.
[remote_control_server_executer-1] [INFO] [1778912062.905003015] [moveit_rdf_loader.rdf_loader]: Loaded robot model in 0 seconds
[remote_control_server_executer-1] [INFO] [1778912062.905042899] [moveit_robot_model.robot_model]: Loading robot model 'arctos'...
[remote_control_server_executer-1] [INFO] [1778912063.078181097] [move_group_interface]: Ready to take commands for planning group denso_arm.
[remote_control_server_executer-1] [INFO] [1778912063.079361971] [moveit_ros.current_state_monitor]: Listening to joint states on topic 'joint_states'
[remote_control_server_executer-1] [INFO] [1778912254.741349046] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 0.000000 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1778912254.742016213] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778912254.742352401] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778912254.742603380] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778912254.743186821] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778912254.842132852] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778912254.843166794] [move_group_interface]: time taken to generate plan: 0.0140443 seconds
[remote_control_server_executer-1] [INFO] [1778912254.843398467] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778912254.844673140] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778912258.922187450] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778912258.922792992] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778912267.677526313] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 -0.541163 1.882308 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1778912267.677829600] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778912267.677950325] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778912267.678140882] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778912267.678626349] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778912267.746142244] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778912267.746416156] [move_group_interface]: time taken to generate plan: 0.014193 seconds
[remote_control_server_executer-1] [INFO] [1778912267.746555175] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778912267.747656634] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778912274.022316868] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778912274.022601550] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778912283.193834890] [remote_control_server_executer]: Received goal request with Joint position: 1.635838 -0.541163 1.882308 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1778912283.194092903] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778912283.194267659] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778912283.194481088] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778912283.194977056] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778912283.246553975] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778912283.247324856] [move_group_interface]: time taken to generate plan: 0.015988 seconds
[remote_control_server_executer-1] [INFO] [1778912283.247433179] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778912283.248234446] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778912289.422113495] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778912289.422329248] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778912289.454938140] [remote_control_server_executer]: Received goal request with Joint position: 1.635838 -0.541163 1.882308 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1778912289.455167529] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778912289.455283386] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778912289.455463663] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778912289.455934443] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778912289.539085213] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778912289.539317417] [move_group_interface]: time taken to generate plan: 0.0144283 seconds
[remote_control_server_executer-1] [INFO] [1778912289.539412284] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778912289.539975898] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778912291.522125816] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778912291.522980243] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778912300.326677111] [remote_control_server_executer]: Received goal request with Joint position: -1.333282 -0.541163 1.882308 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1778912300.326939792] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778912300.327070898] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778912300.327295858] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778912300.328720141] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778912300.450427847] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778912300.450793961] [move_group_interface]: time taken to generate plan: 0.0146692 seconds
[remote_control_server_executer-1] [INFO] [1778912300.450902444] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778912300.452009424] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778912311.122094960] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778912311.122499216] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778912326.285475751] [remote_control_server_executer]: Received goal request with Joint position: -1.333282 -0.541163 1.882308 0.000000 0.221516 -1.843211
[remote_control_server_executer-1] [INFO] [1778912326.285757839] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778912326.285864658] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778912326.286027212] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778912326.286466383] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778912326.339901040] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778912326.340411043] [move_group_interface]: time taken to generate plan: 0.0132393 seconds
[remote_control_server_executer-1] [INFO] [1778912326.340561204] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778912326.341261323] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778912329.921758010] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778912329.923006514] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778912338.409823810] [remote_control_server_executer]: Received goal request with Joint position: -1.333282 -0.541163 1.882308 0.000000 -0.172695 -0.049362
[remote_control_server_executer-1] [INFO] [1778912338.411262230] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778912338.411470159] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778912338.411657198] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778912338.412213188] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778912338.440568933] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778912338.441449019] [move_group_interface]: time taken to generate plan: 0.0145001 seconds
[remote_control_server_executer-1] [INFO] [1778912338.441631650] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778912338.442524099] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778912341.922979928] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778912341.924259130] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778912346.583559066] [remote_control_server_executer]: Received goal request with Joint position: -0.102805 -0.541163 1.882308 0.000000 -0.172695 -0.049362
[remote_control_server_executer-1] [INFO] [1778912346.583845822] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778912346.584001123] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778912346.584202980] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778912346.584711070] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778912346.643897122] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778912346.643962244] [move_group_interface]: time taken to generate plan: 0.0148876 seconds
[remote_control_server_executer-1] [INFO] [1778912346.644073923] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778912346.644814768] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778912351.521796652] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778912351.522879697] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778912356.265205786] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 0.000000 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1778912356.265469599] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778912356.265573403] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778912356.265803934] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778912356.266259506] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778912356.353320985] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778912356.354325704] [move_group_interface]: time taken to generate plan: 0.024522 seconds
[remote_control_server_executer-1] [INFO] [1778912356.354457250] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778912356.355364868] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778912362.621932700] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778912362.622574560] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778912387.877566726] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 0.000000 0.000000 1.298622 0.037658
[remote_control_server_executer-1] [INFO] [1778912387.877832353] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778912387.877974649] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778912387.878203687] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778912387.878721095] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778912387.950411197] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778912387.951310780] [move_group_interface]: time taken to generate plan: 0.0238216 seconds
[remote_control_server_executer-1] [INFO] [1778912387.951422208] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778912387.952025186] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778912391.522046453] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778912391.522903707] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778912402.871254184] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 1.625911 0.000000 1.570796 0.037658
[remote_control_server_executer-1] [INFO] [1778912402.871526243] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778912402.871659582] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778912402.871899561] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778912402.872760161] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778912402.943905383] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778912402.944402233] [move_group_interface]: time taken to generate plan: 0.0143441 seconds
[remote_control_server_executer-1] [INFO] [1778912402.944739864] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778912402.945990624] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778912408.521819726] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778912408.523184699] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778912440.046553745] [remote_control_server_executer]: Received goal request with Joint position: -0.157869 0.522680 2.146712 0.000000 0.568772 0.037658
[remote_control_server_executer-1] [INFO] [1778912440.046794616] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778912440.046923577] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778912440.047118572] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778912440.047623857] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778912440.139168927] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778912440.140149271] [move_group_interface]: time taken to generate plan: 0.0139166 seconds
[remote_control_server_executer-1] [INFO] [1778912440.140226035] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778912440.140754593] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778912443.122342221] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778912443.122906777] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778912453.420152581] [remote_control_server_executer]: Received goal request with Joint position: -0.001454 0.522680 2.146712 0.000000 0.568772 0.037658
[remote_control_server_executer-1] [INFO] [1778912453.420449256] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778912453.420585040] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778912453.420807055] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778912453.421586974] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778912453.536276596] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778912453.536546231] [move_group_interface]: time taken to generate plan: 0.012689 seconds
[remote_control_server_executer-1] [INFO] [1778912453.536616492] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778912453.537145081] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778912454.922646365] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778912454.923821684] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778912471.782937480] [remote_control_server_executer]: Received goal request with Joint position: -0.001454 0.626540 2.279217 0.000000 0.307419 0.037658
[remote_control_server_executer-1] [INFO] [1778912471.783940917] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778912471.784096238] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778912471.784341707] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778912471.784880115] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778912471.836234455] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778912471.837180364] [move_group_interface]: time taken to generate plan: 0.0126399 seconds
[remote_control_server_executer-1] [INFO] [1778912471.837310638] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778912471.837926741] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778912473.421898671] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778912473.422658934] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778912480.605031285] [remote_control_server_executer]: Received goal request with Joint position: -0.001454 0.626540 2.135449 0.000000 0.307419 0.037658
[remote_control_server_executer-1] [INFO] [1778912480.605289267] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778912480.605392160] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778912480.605565144] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778912480.606028681] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778912480.639487368] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778912480.639945295] [move_group_interface]: time taken to generate plan: 0.0145292 seconds
[remote_control_server_executer-1] [INFO] [1778912480.640030304] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778912480.640522726] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778912481.921983741] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778912481.922430757] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778912496.057771004] [remote_control_server_executer]: Received goal request with Joint position: -0.001454 0.717496 2.044825 0.000000 0.307419 0.037658
[remote_control_server_executer-1] [INFO] [1778912496.058084922] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778912496.058219283] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778912496.058425840] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778912496.059356501] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778912496.137482739] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778912496.138073575] [move_group_interface]: time taken to generate plan: 0.0136101 seconds
[remote_control_server_executer-1] [INFO] [1778912496.138259362] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778912496.138905742] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778912497.322680880] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778912497.323276916] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778912520.430497997] [remote_control_server_executer]: Received goal request with Joint position: -0.001454 0.776324 2.087368 0.000000 0.307419 0.037658
[remote_control_server_executer-1] [INFO] [1778912520.430796556] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778912520.430919676] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778912520.431106746] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778912520.431569963] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778912520.536329778] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778912520.536797573] [move_group_interface]: time taken to generate plan: 0.0132958 seconds
[remote_control_server_executer-1] [INFO] [1778912520.536896358] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778912520.537275938] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778912521.521685739] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778912521.522596634] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778912529.552404881] [remote_control_server_executer]: Received goal request with Joint position: -0.001454 0.776324 1.988333 0.000000 0.307419 0.037658
[remote_control_server_executer-1] [INFO] [1778912529.552796825] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778912529.553021445] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778912529.553268257] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778912529.553838605] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778912529.646102869] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778912529.647054090] [move_group_interface]: time taken to generate plan: 0.0229156 seconds
[remote_control_server_executer-1] [INFO] [1778912529.647203499] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778912529.647829230] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778912530.822145848] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778912530.823031154] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778912568.535181763] [remote_control_server_executer]: Received goal request with Joint position: -0.001454 0.830739 2.014956 0.000000 0.307419 0.037658
[remote_control_server_executer-1] [INFO] [1778912568.535437341] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778912568.535551615] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778912568.535735309] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778912568.536221679] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778912568.636944099] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778912568.637924754] [move_group_interface]: time taken to generate plan: 0.0136252 seconds
[remote_control_server_executer-1] [INFO] [1778912568.638179441] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778912568.638937560] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778912569.622195610] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778912569.623323351] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778912575.723375009] [remote_control_server_executer]: Received goal request with Joint position: -0.001454 0.830739 1.897570 0.000000 0.307419 0.037658
[remote_control_server_executer-1] [INFO] [1778912575.723746134] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778912575.723851822] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778912575.724005930] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778912575.724453358] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778912575.838405084] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778912575.838999036] [move_group_interface]: time taken to generate plan: 0.0151362 seconds
[remote_control_server_executer-1] [INFO] [1778912575.839090948] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778912575.839530250] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778912577.022113595] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778912577.023144795] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778912601.206821927] [remote_control_server_executer]: Received goal request with Joint position: -0.001454 0.307402 1.122574 0.000000 1.570796 0.037658
[remote_control_server_executer-1] [INFO] [1778912601.207090410] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778912601.207200235] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778912601.207391924] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778912601.207840023] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778912601.240199068] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778912601.241408652] [move_group_interface]: time taken to generate plan: 0.0140716 seconds
[remote_control_server_executer-1] [INFO] [1778912601.241570255] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778912601.242311162] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778912604.721885258] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778912604.722215466] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778912624.394025693] [remote_control_server_executer]: Received goal request with Joint position: 1.645803 -0.416633 1.890298 0.000000 1.570796 0.037658
[remote_control_server_executer-1] [INFO] [1778912624.394576664] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778912624.394795804] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778912624.395169905] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778912624.395831724] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778912624.442017739] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778912624.442537592] [move_group_interface]: time taken to generate plan: 0.0143412 seconds
[remote_control_server_executer-1] [INFO] [1778912624.442702270] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778912624.443714816] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778912630.622337302] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778912630.623278223] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778912643.626004186] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 0.000000 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1778912643.626361545] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778912643.626649434] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778912643.626997044] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778912643.627744574] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778912643.743721155] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778912643.744684459] [move_group_interface]: time taken to generate plan: 0.0144044 seconds
[remote_control_server_executer-1] [INFO] [1778912643.744827727] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778912643.746113144] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778912650.021983831] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778912650.022401564] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778912692.024770193] [remote_control_server_executer]: Received goal request with Joint position: -1.204020 -0.317186 1.689897 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1778912692.025053343] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778912692.025177526] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778912692.025361921] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778912692.025859933] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778912692.142267230] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778912692.142802382] [move_group_interface]: time taken to generate plan: 0.0143578 seconds
[remote_control_server_executer-1] [INFO] [1778912692.142927807] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778912692.144064546] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778912697.821854159] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778912697.822308479] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778912704.302109005] [remote_control_server_executer]: Received goal request with Joint position: -1.688397 -0.317186 1.689897 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1778912704.302415308] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778912704.302538319] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778912704.302706043] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778912704.303413888] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778912704.339208464] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778912704.340084224] [move_group_interface]: time taken to generate plan: 0.0141596 seconds
[remote_control_server_executer-1] [INFO] [1778912704.340274280] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778912704.341080479] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778912706.721617473] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778912706.722878624] [remote_control_server_executer]: Goal succeeded
[remote_control_server_executer-1] [INFO] [1778912718.866534964] [remote_control_server_executer]: Received goal request with Joint position: 0.000000 0.000000 0.000000 0.000000 0.000000 0.000000
[remote_control_server_executer-1] [INFO] [1778912718.867073432] [remote_control_server_executer]: Executing goal
[remote_control_server_executer-1] [INFO] [1778912718.867252738] [remote_control_server_executer]: Planning...
[remote_control_server_executer-1] [INFO] [1778912718.867467190] [move_group_interface]: MoveGroup action client/server ready
[remote_control_server_executer-1] [INFO] [1778912718.867971654] [move_group_interface]: Planning request accepted
[remote_control_server_executer-1] [INFO] [1778912718.947284273] [move_group_interface]: Planning request complete!
[remote_control_server_executer-1] [INFO] [1778912718.948025231] [move_group_interface]: time taken to generate plan: 0.0148711 seconds
[remote_control_server_executer-1] [INFO] [1778912718.948126711] [remote_control_server_executer]: Executing...
[remote_control_server_executer-1] [INFO] [1778912718.949024291] [move_group_interface]: Execute request accepted
[remote_control_server_executer-1] [INFO] [1778912725.324465079] [move_group_interface]: Execute request success!
[remote_control_server_executer-1] [INFO] [1778912725.325477454] [remote_control_server_executer]: Goal succeeded

