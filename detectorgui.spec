# -*- mode: python -*-
a = Analysis(['bin/detectorgui.py'],
             pathex=['/home/alcapaya/workspace/P-phase Picker/eqpickertool'],
             hiddenimports=['scipy.special._ufuncs_cxx'],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts + [('O','','OPTION')],
          a.binaries,
          a.zipfiles,
          a.datas,
          name='detectorgui',
          debug=False,
          strip=None,
          upx=True,
          console=True )
