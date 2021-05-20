from setuptools import setup, find_packages

setup(
    name='influence map',
    version='0.1',
    packages=find_packages(exclude=['assets', 'demos', 'misc']),
    install_requires=['networkx', 'seaborn', 'requests',
        'django==2.0.4', 'numpy', 'elasticsearch_dsl==6.2.1', 'pyhocon', 'unidecode',
        'multiprocess', 'psycopg2']
)
