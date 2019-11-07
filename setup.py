import os

from setuptools import setup, find_packages

os.system('pip install git+https://github.com/RealVNF/coord-env-interface.git')
os.system('pip install git+https://github.com/RealVNF/coordination-simulation.git')
os.system('pip install git+https://github.com/CN-UPB/B-JointSP.git@dev')
requirements = [
    'pyyaml>=5.1',
    'coord-interface',
    'bjointsp',
    'coord-sim'
]

test_requirements = [
    'flake8'
]

setup(
    name='bjointsp-adapter',
    version='0.0.2',
    description='Works as an adapter between BJointSP as the coordination algo and coord-simulator.',
    url='https://github.com/RealVNF/bjointsp-adapter',
    author='Stefan Schneider',
    author_email='stefan.schneider@upb.de',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    install_requires=requirements + test_requirements,
    test_requirements=test_requirements,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'bjointsp-adapter=adapter.adapter:main',
        ],
    },
)
