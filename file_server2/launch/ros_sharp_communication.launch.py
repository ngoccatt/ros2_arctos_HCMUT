# © Siemens AG, 2024
# Author: Mehmet Emre Cakal (emre.cakal@siemens.com)

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# <http://www.apache.org/licenses/LICENSE-2.0>.
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import FrontendLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Define launch arguments
    port_arg = DeclareLaunchArgument('port', 
                                     default_value='9090', 
                                     description='Port number for ROS communication (default: 9090)')
    
    fragment_timeout_arg = DeclareLaunchArgument('fragment_timeout',
                                                  default_value='600', 
                                                  description='Timeout for fragment reassembly in seconds (default: 600)')
    
    unregister_timeout_arg = DeclareLaunchArgument('unregister_timeout',
                                                   default_value='10.0',
                                                   description='Timeout for unregistering in seconds (default: 10.0)')
    
    max_message_size_arg = DeclareLaunchArgument('max_message_size',
                                                 default_value='100000000',
                                                 description='Maximum message size in bytes (default: 10000000)')

    default_call_service_timeout_arg = DeclareLaunchArgument('default_call_service_timeout',
                                                            default_value='0.0',
                                                            description='Default timeout for calling services in seconds (default: 5.0). ' \
                                                            'If not specified, service calls will block indefinitely if no response is received' \
                                                            ' but since this is a "file server" node, it gonna take a long time to run. better put on infinite timeout.')

    call_services_in_new_thread_arg = DeclareLaunchArgument('call_services_in_new_thread',
                                                            default_value='false',
                                                            description='Whether to call services in a new thread (default: false). ' \
                                                            'If false, service calls will block the main thread' \
                                                            ' but since this is a "file server" node, it gonna take a long time to run. better put on main thread.')
    
    send_action_goals_in_new_thread_arg = DeclareLaunchArgument('send_action_goals_in_new_thread',
                                                            default_value='false',
                                                            description='if false, sending action goals will block the main thread.' \
                                                            ' but since this is a "file server" node, it gonna take a long time to run. better put on main thread.')

    pkg_rosbridge_server = get_package_share_directory('rosbridge_server')

    rosbridge_server_launch = PathJoinSubstitution(
        [pkg_rosbridge_server, 'launch', 'rosbridge_websocket_launch.xml'])

    return LaunchDescription([
        port_arg,
        fragment_timeout_arg,
        unregister_timeout_arg,
        max_message_size_arg,
        default_call_service_timeout_arg,
        call_services_in_new_thread_arg,
        send_action_goals_in_new_thread_arg,

        IncludeLaunchDescription(
            FrontendLaunchDescriptionSource([rosbridge_server_launch]),
            launch_arguments={
                'port': LaunchConfiguration('port'),
                'fragment_timeout': LaunchConfiguration('fragment_timeout'),
                'unregister_timeout': LaunchConfiguration('unregister_timeout'),
                'max_message_size': LaunchConfiguration('max_message_size'),
                'default_call_service_timeout': LaunchConfiguration('default_call_service_timeout'),
                'call_services_in_new_thread': LaunchConfiguration('call_services_in_new_thread'),
                'send_action_goals_in_new_thread': LaunchConfiguration('send_action_goals_in_new_thread')
            }.items()
        ),
        
        Node(
            package='file_server2',
            executable='file_server2_node',
            output='screen'
        )
        
    ])

