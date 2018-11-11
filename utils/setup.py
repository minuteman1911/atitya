from distutils.core import setup
from Cython.Build import cythonize

setup(name='Kobe extensions',
      ext_modules=cythonize("functools_modified.py" , annotate=True))
