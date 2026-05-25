#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

from denso_hardware_interface.msg import JointCommand
from std_msgs.msg import Float64MultiArray


class JointCommandNode(Node):
    def __init__(self):
        super().__init__("joint_command_node")

        # Danh sách joint theo đúng thứ tự controller expects
        self.joint_order = [
            "joint_1",
            "joint_2",
            "joint_3",
            "joint_4",
            "joint_5",
            "joint_6"
        ]

        # Prepare zero vector
        self.current_cmd = [0.0] * len(self.joint_order)

        # Publisher → ros2_control
        self.cmd_pub = self.create_publisher(
            Float64MultiArray,
            "/denso_arm_controller/commands",
            10
        )

        # Subscriber → user input channel
        self.sub = self.create_subscription(
            JointCommand,
            "/cmd_joint",
            self.command_callback,
            10
        )

        self.get_logger().info("Joint Command Node started.")

    def command_callback(self, msg: JointCommand):
        joint_name = msg.joint_name
        target = msg.target_position

        self.get_logger().info(f"Received cmd: {joint_name} → {target}")

        # Find index
        if joint_name not in self.joint_order:
            self.get_logger().error(f"Joint '{joint_name}' is NOT valid!")
            return

        idx = self.joint_order.index(joint_name)
        self.current_cmd[idx] = target

        # Publish updated vector
        out = Float64MultiArray()
        out.data = self.current_cmd

        self.cmd_pub.publish(out)
        self.get_logger().info(f"Published: {out.data}")


def main(args=None):
    rclpy.init(args=args)
    node = JointCommandNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
