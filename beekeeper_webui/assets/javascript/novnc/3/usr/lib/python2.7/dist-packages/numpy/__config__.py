# This file is generated by /build/python-numpy-XaNT5J/python-numpy-1.13.3/setup.py
# It contains system_info results at the time of building this package.
__all__ = ["get_info","show"]

blas_info={'libraries': ['blas', 'blas'], 'library_dirs': ['/usr/lib/x86_64-linux-gnu'], 'language': 'c', 'define_macros': [('HAVE_CBLAS', None)], 'include_dirs': ['/usr/local/include', '/usr/include']}
atlas_3_10_blas_info={}
lapack_info={'libraries': ['lapack', 'lapack'], 'library_dirs': ['/usr/lib/x86_64-linux-gnu'], 'language': 'f77'}
atlas_3_10_blas_threads_info={}
atlas_threads_info={}
blas_opt_info={'libraries': ['blas', 'blas'], 'library_dirs': ['/usr/lib/x86_64-linux-gnu'], 'define_macros': [('NO_ATLAS_INFO', 1), ('HAVE_CBLAS', None)], 'language': 'c', 'include_dirs': ['/usr/local/include', '/usr/include']}
blis_info={}
atlas_blas_threads_info={}
openblas_info={}
lapack_opt_info={'libraries': ['lapack', 'lapack', 'blas', 'blas'], 'library_dirs': ['/usr/lib/x86_64-linux-gnu'], 'define_macros': [('NO_ATLAS_INFO', 1), ('HAVE_CBLAS', None)], 'language': 'c', 'include_dirs': ['/usr/local/include', '/usr/include']}
openblas_lapack_info={}
atlas_3_10_threads_info={}
atlas_info={}
atlas_3_10_info={}
lapack_mkl_info={}
blas_mkl_info={}
atlas_blas_info={}

def get_info(name):
    g = globals()
    return g.get(name, g.get(name + "_info", {}))

def show():
    for name,info_dict in globals().items():
        if name[0] == "_" or type(info_dict) is not type({}): continue
        print(name + ":")
        if not info_dict:
            print("  NOT AVAILABLE")
        for k,v in info_dict.items():
            v = str(v)
            if k == "sources" and len(v) > 200:
                v = v[:60] + " ...\n... " + v[-60:]
            print("    %s = %s" % (k,v))
    