# -*- mode: python -*-
a = Analysis(['bin/generator.py'],
             pathex=['/home/alcapaya/workspace/eqpickertool'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='generator',
          debug=False,
          strip=None,
          upx=True,
          console=True )
