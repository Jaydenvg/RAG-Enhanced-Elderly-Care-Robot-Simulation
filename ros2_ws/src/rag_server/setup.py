from setuptools import setup, find_packages

package_name = 'rag_server'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'pyyaml'],
    zip_safe=True,
    author='Jayden Varghese George',
    author_email='jayden@heriot-watt.ac.uk',
    maintainer='Jayden Varghese George',
    maintainer_email='jayden@heriot-watt.ac.uk',
    url='https://github.com/Jaydenvg/RAG-Enhanced-Elderly-Care-Robot-Simulation',
    description='RAG Server for Elderly Care Robot - Document Loader and Semantic Search',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
		'rag_server_node=rag_server.rag_server_node:main',
        ],
    },
)
