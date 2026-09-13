# -*- coding: utf-8 -*-
import sys
import os
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    import builtins
    _orig_open = builtins.open
    def _utf8_open(*args, **kwargs):
        if args and isinstance(args[0], (str, os.PathLike)):
            mode = args[1] if len(args) > 1 else kwargs.get('mode', 'r')
            if isinstance(mode, str) and 'b' not in mode and 'encoding' not in kwargs:
                kwargs['encoding'] = 'utf-8'
                kwargs['errors'] = 'ignore'
        return _orig_open(*args, **kwargs)
    builtins.open = _utf8_open
