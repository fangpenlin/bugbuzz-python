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
    author='Victor Lin',
    author_email='hello@victorlin.me',
    url='https://github.com/victorlin/bugbuzz-python',
    description='Easy to use web-base online debugger',
    keywords='debugger debug pdb',
    license='MIT',
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
