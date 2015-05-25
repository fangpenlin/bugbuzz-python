from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

version = '0.0.0'
try:
    import bugbuzz
    version = bugbuzz.__version__
except ImportError:
    pass


tests_require = [
    'mock',
    'pytest',
    'pytest-cov',
    'pytest-xdist',
    'pytest-capturelog',
    'pytest-mock',
]

setup(
    name='bugbuzz',
    version=version,
    packages=find_packages(),
    install_requires=[
        'pycrypto',
    ],
    extras_require=dict(
        tests=tests_require,
    ),
    tests_require=tests_require,
)
