from setuptools import setup, find_packages

setup(
    name='influence map',
    version='0.1',
    packages=find_packages(exclude=['assets', 'demos', 'misc']),
    install_requires=['networkx', 'seaborn', 'requests',
        'django', 'numpy', 'elasticsearch_dsl', 'pyhocon', 'unidecode',
        'multiprocess']
)
