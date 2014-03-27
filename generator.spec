# -*- mode: python -*-
a = Analysis(['bin/generator.py'],
             pathex=['/eqpickertool'],
             hiddenimports=['scipy.special._ufuncs_cxx'])

data = Tree('./bfirls', prefix='bfirls')
data += Tree('./docs', prefix='docs')
data += [('COPYING.LESSER.txt', 'COPYING.LESSER.txt', 'DATA'),
                ('COPYING.txt', 'COPYING.txt', 'DATA'),
                ('README', 'README', 'DATA'),
                ('README.md', 'README.md', 'DATA')]

pyz = PYZ(a.pure)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='generator.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               data,
               strip=None,
               upx=True,
               name='generator')

