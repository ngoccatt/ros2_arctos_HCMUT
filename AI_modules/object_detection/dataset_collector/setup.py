from setuptools import find_packages, setup

package_name = "dataset_collector"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="namdiep-239",
    maintainer_email="namdiep239@gmail.com",
    description="ROS2 node for collecting cube detection dataset via eye-in-hand webcam",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "capture_node = dataset_collector.capture_node:main",
        ],
    },
)
