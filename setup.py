#
#  Execute this after a change of samplerbox_audio.pyx
#  with command "python setup.py build_ext --inplace"
#
#   SamplerBox extended by HansEhv (https://github.com/hansehv)
#   see docs at https://homspace.nl/samplerbox

from distutils.core import setup
from Cython.Build import cythonize
import numpy

setup (
    ext_modules = cythonize("samplerbox_audio.pyx"),
    include_dirs = [numpy.get_include()],
)
