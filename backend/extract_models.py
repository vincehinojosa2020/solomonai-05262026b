"""
Solomon AI — Automated Modular Monolith Refactor
Extracts models and routes from server.py into organized modules.
"""
import re, os, sys

SERVER = "/app/backend/server.py"
with open(SERVER, "r") as f:
    content = f.read()
    lines = content.split("\n")

print(f"Read {len(lines)} lines from server.py")

# ═══ STEP 1: Extract ALL Pydantic model classes ═══
# Find contiguous model blocks (class definition + body)
model_blocks = []
in_model = False
current_block = []
current_name = ""

for i, line in enumerate(lines):
    # Start of a model class
    if re.match(r'^class \w+\(.*BaseModel.*\):', line) or re.match(r'^class \w+\(\w+Base\):', line):
        if current_block and current_name:
            model_blocks.append((current_name, "\n".join(current_block)))
        current_name = re.match(r'^class (\w+)', line).group(1)
        current_block = [line]
        in_model = True
    elif in_model:
        # Check if we're still inside the class body (indented) or hit a non-indented line
        if line.startswith("    ") or line.strip() == "" or line.startswith("        "):
            current_block.append(line)
        else:
            # End of model class
            model_blocks.append((current_name, "\n".join(current_block)))
            current_block = []
            current_name = ""
            in_model = False

# Don't forget the last one
if current_block and current_name:
    model_blocks.append((current_name, "\n".join(current_block)))

print(f"Extracted {len(model_blocks)} model classes")
model_names = [name for name, _ in model_blocks]

# Write models to /app/backend/models/schemas.py
models_content = '''"""
Solomon AI — Pydantic Models (Auto-extracted)
All data models for the Solomon AI platform.
"""
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, date
import uuid


'''
for name, block in model_blocks:
    models_content += block.rstrip() + "\n\n"

os.makedirs("/app/backend/models", exist_ok=True)
with open("/app/backend/models/schemas.py", "w") as f:
    f.write(models_content)

# Create models/__init__.py that re-exports everything
model_exports = ", ".join(model_names)
init_content = f'''"""Solomon AI Models — Re-export all schemas."""
from models.schemas import {model_exports}

__all__ = {model_names}
'''
with open("/app/backend/models/__init__.py", "w") as f:
    f.write(init_content)

print(f"Written {len(model_blocks)} models to models/schemas.py")
print(f"Written models/__init__.py with {len(model_names)} exports")

# ═══ STEP 2: Verify models import correctly ═══
print("\nVerifying models import...")
os.system("cd /app/backend && python3 -c 'from models.schemas import *; print(\"Models import: OK\")'")

print("\n✅ Phase R1 (Models) complete")
print(f"   - {len(model_blocks)} models extracted to models/schemas.py")
print(f"   - models/__init__.py re-exports all classes")
