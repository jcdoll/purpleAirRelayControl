import subprocess
import sys

cmd = [
    sys.executable,
    '-m',
    'pytest',
    'esp32/tests/host/',
    '--cov=esp32',
    '--cov-branch',
    '--cov-report=term-missing',
]

print('Running quality check:', ' '.join(cmd))
result = subprocess.run(cmd)

sys.exit(result.returncode)

cmd_style = [sys.executable, '-m', 'black', '--check', 'esp32']
cmd_isort = [sys.executable, '-m', 'isort', '--check', 'esp32']
cmd_flake = [sys.executable, '-m', 'flake8', 'esp32']

print('\nRunning style checks...')
for c in (cmd_style, cmd_isort, cmd_flake):
    print(' '.join(c))
    res = subprocess.run(c)
    if res.returncode != 0:
        sys.exit(res.returncode)
