# How to maintain this folder

## Regenerate the moveit_config package

This folder is generated using [moveit_setup_assistant](https://moveit.picknik.ai/main/doc/examples/setup_assistant/setup_assistant_tutorial.html) package.

If there's any updated related to the robot's description, this package should be updated.

Remember to source the ros2_ws before running moveit_setup_assistant, then select artos.xacro in the denso_description/urdf folder. Follow the steps in the tutorial and generate the entire new moveit_config package. Merge necessary changes.

## Regenerate gazebo model.

No needed. the gazebo model is automatically generated.

