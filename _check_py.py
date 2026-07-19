import py_compile, sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
files = [
    'backend/services/history.py',
    'backend/routers/ai.py',
    'backend/config.py',
    'backend/routers/settings.py',
]
all_ok = True
for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print(f + ': OK')
    except py_compile.PyCompileError as e:
        print(f + ': ERROR - ' + str(e))
        all_ok = False
if all_ok:
    print('\nAll Python syntax checks passed!')
else:
    sys.exit(1)
