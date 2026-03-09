import sys, os, importlib.util
print('CWD:', os.getcwd())
print('sys.path[0]:', sys.path[0])
print('find_spec app:', importlib.util.find_spec('app'))
try:
    import app
    print('OK imported app')
except Exception as e:
    print('IMPORT ERROR:', type(e), e)
    import traceback
    traceback.print_exc()
