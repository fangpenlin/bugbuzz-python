from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages  # noqa: E402

version = '0.0.0'
try:
    from bugbuzz import __version__
    version = __version__
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
    author='Fang-Pen Lin',
    author_email='hello@fangpenlin.com',
    url='https://github.com/fangpenlin/bugbuzz-python',
    description='Easy to use web-base online debugger',
    classifiers=[
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Topic :: Software Development :: Debuggers",
    ],
    keywords='debugger debug pdb',
    license='MIT',
    version=version,
    packages=find_packages(exclude=('tests', )),
    package_data={'': ['LICENSE'], 'bugbuzz/packages/requests': ['*.pem']},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'pycrypto',
        'future',
    ],
    extras_require=dict(
        tests=tests_require,
    ),
    tests_require=tests_require,
)
