# -*- mode: python -*-
a = Analysis(['bin/detectorgui.py'],
             pathex=['HOME/workspace/eqpickertool'],
             hiddenimports=['scipy.special._ufuncs_cxx'],
             hookspath=['.'],
             runtime_hooks=None)

a.binaries = [x for x in a.binaries if not x[0].startswith("wx")]

a.binaries = a.binaries - TOC([
 ('libnvidia-glcore', '', ''),
 ('libnvidia-tls', '', ''),
 ('tk85.dll', '', ''),
 ('_sqlite3', '', ''),
 ('_ssl', '', ''),
 ('_tkinter', '', '')])


pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts + [('O','','OPTION')],
          exclude_binaries=True,
          name='detectorgui.exe',
          debug=False,
          strip=False,
          upx=True,
          console=False,
          icon='res/image/app.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='detectorgui')
