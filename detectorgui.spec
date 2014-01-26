# -*- mode: python -*-
a = Analysis(['bin/detectorgui.py'],
             pathex=['/home/alcapaya/workspace/eqpickertool'],
             hiddenimports=['scipy.special._ufuncs_cxx'],
             hookspath=['.'],
             runtime_hooks=None)

#a.binaries = [x for x in a.binaries if not x[0].startswith("PyQt4")]

pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='detectorgui',
          debug=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='detectorgui')
