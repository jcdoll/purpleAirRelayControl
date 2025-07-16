import subprocess
import sys

cmd = [
    sys.executable,
    '-m',
    'pytest',
    'esp32/tests/host/',
    '--cov=esp32',
    '--cov-branch',
    '--cov-report=term-missing'
]

print('Running quality check:', ' '.join(cmd))
result = subprocess.run(cmd)

sys.exit(result.returncode) 