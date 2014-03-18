# -*- mode: python -*-
a = Analysis(['bin/detectorgui.py'],
             pathex=['/eqpickertool'],
             hiddenimports=['scipy.special._ufuncs_cxx', 'PySide.phonon'],
             hookspath=['.'])

pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts + [('O','','OPTION')],
          exclude_binaries=True,
          name='detectorgui.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True,
          icon='res/images/app.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='detectorgui')
