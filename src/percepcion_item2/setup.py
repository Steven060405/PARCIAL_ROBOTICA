from setuptools import find_packages, setup

package_name = 'percepcion_item2'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name]
        ),
        (
            'share/' + package_name,
            ['package.xml']
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='equipo',
    maintainer_email='equipo@esan.edu.pe',
    description='Percepcion por camara para Pregunta 2',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'percepcion_camara = percepcion_item2.percepcion_camara:main',
        ],
    },
)
