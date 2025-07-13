from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup, Extension

# Define the extension module
ext_modules = [
    Pybind11Extension(
        "win_check_cpp",
        ["win_check_cplus.cpp"],
        include_dirs=[
            # Path to pybind11 headers
            "C:\Python\Python311",
            "C:\Python\Python311\Lib\site-packages\pybind11\include\pybind11",
        ],
        language='c++',
        cxx_std=17,
    ),
]

setup(
    name="win_check_cpp",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.7",
)