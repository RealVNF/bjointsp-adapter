import os

from setuptools import setup, find_packages

requirements = [
    'pyyaml>=5.1',
    'common-utils',
    'bjointsp',
    'coord-sim',
    'tqdm'
]

test_requirements = [
    'flake8'
]

setup(
    name='bjointsp-adapter',
    version='0.0.2',
    description='Works as an adapter between BJointSP as the coordination algo and coord-simulator.',
    url='https://github.com/RealVNF/bjointsp-adapter',
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
