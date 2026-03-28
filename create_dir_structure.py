import os

# Define the Ascenda structure
project_root = r"C:\code\AI\ascenda"
folders = [
    "backend/app/core",
    "backend/app/services",
    "backend/app/api",
    "frontend/src",
]

for folder in folders:
    os.makedirs(os.path.join(project_root, folder), exist_ok=True)

# Create empty __init__.py files to make them Python modules
open(os.path.join(project_root, "backend/app/__init__.py"), 'a').close()
open(os.path.join(project_root, "backend/app/core/__init__.py"), 'a').close()
open(os.path.join(project_root, "backend/app/services/__init__.py"), 'a').close()

print(f"🚀 Ascenda structure created at {project_root}")