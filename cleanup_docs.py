import os
import sys

files_to_remove = [
    'FRONTEND_SETUP_GUIDE.md',
    'IMPLEMENTATION_SUMMARY.md', 
    'PROJECT_COMPLETION_STATUS.md'
]

os.chdir('d:\\digital-bank')

for f in files_to_remove:
    try:
        if os.path.exists(f):
            os.remove(f)
            print(f'✓ Removed {f}')
    except Exception as e:
        print(f'✗ Failed to remove {f}: {e}')

print('\nCleanup complete')
