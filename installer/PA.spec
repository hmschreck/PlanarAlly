# -*- mode: python -*-
import os
import sys

install_dir = os.path.dirname(os.path.abspath(sys.argv[1]))


def _(arg):
    return os.path.join(install_dir, arg)


block_cipher = None


a = Analysis([_('install.py')],
             pathex=[install_dir],
             datas=[
    (_('selectfolder.png'), ''),
],
    hiddenimports=['winshell'],
    hookspath=None,
    runtime_hooks=None,
    excludes=None,
    cipher=block_cipher)
pyz = PYZ(a.pure,
          cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='configurePA.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True)
