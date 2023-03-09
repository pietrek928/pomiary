from sys import version_info

from setuptools import Extension, setup, find_packages


def get_boost_libs():
    a, b = version_info[:2]
    return f'boost_python{a}{b}',


def get_numpy_libs():
    a, b = version_info[:2]
    return f'boost_numpy{a}{b}',


setup(
    name='meas_analyzer',
    description='Measure analyzer',
    author='pietrek',
    packages=find_packages(exclude=('docs',)),
    setup_requires=[
        'wheel',
        'setuptools',
    ],
    install_requires=[
        'pydantic',
        'pysqlite3',
        'numpy',
        'matplotlib',
    ],
    ext_modules=[
        Extension(
            f'meas_analyzer.meas_extractor', ['meas_analyzer/meas.cc'],
            define_macros=[],
            libraries=get_boost_libs() + get_numpy_libs(),
            extra_compile_args=['-s', '-std=c++17'],
        ),
    ],
    include_package_data=False,
    version='0.1.0',
)
