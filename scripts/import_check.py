import importlib
try:
    m = importlib.import_module('routes.mobile')
    print('OK', m)
except Exception as e:
    import traceback
    traceback.print_exc()
