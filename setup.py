from setuptools import setup, find_packages

setup(
    name='influence map',
    version='0.1',
    packages=find_packages(exclude=['assets', 'demos', 'misc']),
    install_requires=['requests', 'numpy', 'numba', 'pandas',
        'flask', 'flask-cors', 'elasticsearch_dsl', 'unidecode']
)
