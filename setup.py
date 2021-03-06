#!/usr/bin/python
import sys
import numpy
import yaml
import os
import platform

from Cython.Distutils import build_ext
from setuptools import setup, find_packages, Extension


name = 'chisurf'
settings = {
    'version': 'NA'
}

settings_file = os.path.join(
    './chisurf/settings/',
    'settings_chisurf.yaml'
)
with open(settings_file) as fp:
    settings.update(yaml.safe_load(fp))


args = sys.argv[1:]
# Always use build_ext --inplace
if args.count("build_ext") > 0 and args.count("--inplace") == 0:
    sys.argv.insert(sys.argv.index("build_ext")+1, "--inplace")


def make_extension(ext):
    """generate an Extension object from its dotted name
    """
    name = (ext[0])[2:-4]
    name = name.replace("/", ".")
    name = name.replace("\\", ".")
    sources = ext[0:]

    if platform.system() == "Darwin":
        extra_compile_args = ["-O3", "-stdlib=libc++"]
        extra_link_args = ["-stdlib=libc++"]
    else:
        extra_compile_args = []
        extra_link_args = []

    return Extension(
        name,
        sources=sources,
        include_dirs=[numpy.get_include(), "."],
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
        libraries=list(),
        library_dirs=["."],
        language="c++"
    )


# and build up the set of Extension objects
eList = [
    [
        './chisurf/fluorescence/simulation/_simulation.pyx',
        './chisurf/math/rand/mt19937cok.cpp'
    ],
    [
        './chisurf/fluorescence/av/fps.pyx',
        './chisurf/fluorescence/av/mt19937cok.cpp'
    ],
    [
        './chisurf/structure/potential/cPotentials.pyx'
    ],
    [
        './chisurf/math/reaction/_reaction.pyx'
    ]
]

extensions = [make_extension(extension) for extension in eList]


setup(
    name=name,
    version=settings['version'],
    description="Fluorescence-Fitting",
    author="Thomas-Otavio Peulen",
    author_email='thomas.otavio.peulen@gmail.com',
    url='https://fluorescence-tools.github.io/chisurf/',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Win64 (MS Windows)',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.7',
        'Topic :: Scientific/Engineering',
    ],
    keywords='fluorescence single-molecule spectroscopy',
    packages=find_packages(
        include=(name + "*",)
    ),
    package_dir={
        name: name
    },
    include_package_data=True,
    package_data={
        '': [
            '*.json',
            '*.yaml',
            '*.ui',
            '*.png',
            '*.svg',
            '*.css', '*.qss'
            '*.csv', '*.npy', '*.dat'
            '*.dll',
            '*.so'
        ]
    },
    install_requires=[
        'numpy',
        'slugify',
        'sip',
        'PyQt5',
        'emcee',
        'numba',
        'scipy',
        'pyqtgraph',
        'PyYAML',
        'tables',
        'numexpr',
        'matplotlib',
        'python-docx',
        'deprecation',
        'pyopencl',
        'qdarkstyle',
        'qtpy',
        'mrcfile',
        'qtconsole',
        'ipython',
        'docx',
        'mdtraj'
    ],
    setup_requires=[
        "cython",
        'numpy',
        'PyYAML',
        'setuptools'
    ],
    ext_modules=extensions,
    cmdclass={
        'build_ext': build_ext
    },
    entry_points={
        "gui_scripts": [
            "chisurf=chisurf.gui:gui"
        ]
    }
)
