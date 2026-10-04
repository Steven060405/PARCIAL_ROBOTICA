from launch import LaunchDescription
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():

    moveit_config = (
        MoveItConfigsBuilder(
            "jetcobot",
            package_name="jetcobot_moveit"
        )
        .to_moveit_configs()
    )

    planificador = Node(
        package="planificador_item2",
        executable="planificador_moveit",
        name="planificador_moveit",
        output="screen",
        parameters=[
            moveit_config.to_dict()
        ],
    )

    return LaunchDescription([
        planificador
    ])
