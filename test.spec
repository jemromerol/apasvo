# -*- mode: python -*-
a = Analysis(['test.exe', 'bin/detectorgui.py'],
             pathex=['/home/alcapaya/workspace/P-phase Picker/eqpickertool'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='test',
          debug=False,
          strip=None,
          upx=True,
          console=True )
