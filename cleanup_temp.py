import os
base = os.path.dirname(os.path.abspath(__file__))
to_delete = [
    'powershell.cmd',
    'install_venv_deps.py',
    'verify_system.py',
    'test_connection.py',
    # Redundant requirements files (main app uses requirements.txt)
    'requirements_backend.txt',
    'requirements_food_ai.txt',
    # Redundant duplicate startup scripts
    'RUN_ALL.bat',
    'SETUP_AND_RUN.bat',
    'start_server.bat',
    'start_server.sh',
    'run.bat',
    # Redundant duplicate data files at root level
    'Fresh_Juice_Product_Prices.csv',
    'Fresh_Juice_Product_Prices.xlsx',
    # Redundant duplicate docs (many overlapping README files)
    'BACKEND_OPTIONS.md',
    'BACKEND_QUICK_REFERENCE.md',
    'BACKEND_SETUP.md',
    'COMPLETE_SETUP_GUIDE.md',
    'FOOD_AI_ARCHITECTURE.md',
    'FOOD_AI_README.md',
    'FOOD_AI_SETUP.md',
    'FRONTEND_BACKEND_INTEGRATION.md',
    'QUICK_REFERENCE.md',
    'README_AI_FOOD_SYSTEM.md',
    'README_COMPLETE.md',
]
deleted = []
for f in to_delete:
    path = os.path.join(base, f)
    if os.path.exists(path):
        os.remove(path)
        deleted.append(f)
        print(f"DELETED: {f}")
    else:
        print(f"SKIP (not found): {f}")

print(f"\nDeleted {len(deleted)} files.")
