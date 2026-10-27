"""numpy2 compat shims for nptyping/cadquery on numpy>=2.

numpy2 removed the scalar aliases (bool8, int0, object0, str0, uint0...).
nptyping (a cadquery dep) still references them. Idempotent apply.
"""
def apply():
    import numpy as np
    pairs = {'bool8': np.bool_, 'object0': np.object_, 'str0': np.str_,
             'int0': np.int64, 'uint0': np.uint64, 'float_': np.float64,
             'complex_': np.complex128, 'unicode_': np.str_,
             'longfloat': np.longdouble, 'longcomplex': np.clongdouble,
             'singlecomplex': np.complex64, 'cfloat': np.complex64, 'void0': np.void,
             'clongfloat': np.clongdouble,
             'unicode0': np.str_, 'float0': np.float64, 'singlecomplex': np.float64, 'cfloat': np.float64, 'clongfloat': np.float64}
    for name, val in pairs.items():
        try:
            if not hasattr(np, name):
                setattr(np, name, val)
        except Exception:
            pass
    return np
