"""
Solomon AI Refactor Script — Automated Code Extraction
Parses server.py and creates organized module files.
"""
import re, os, textwrap

SERVER_PATH = "/app/backend/server.py"

with open(SERVER_PATH, "r") as f:
    lines = f.readlines()
    content = "".join(lines)

# ── Step 1: Extract all Pydantic model classes ──
# Find class definitions that inherit from BaseModel
model_pattern = re.compile(
    r'^(class \w+\((?:BaseModel|[A-Z]\w+Base)\):.*?)(?=\n(?:class |# ====|@api_router|async def |def (?!__))|\Z)',
    re.MULTILINE | re.DOTALL
)

models = []
for m in model_pattern.finditer(content):
    cls_text = m.group(1).rstrip()
    # Get class name
    cls_name = re.match(r'class (\w+)', cls_text).group(1)
    models.append((cls_name, cls_text))

print(f"Found {len(models)} model classes")

# ── Step 2: Identify route functions by @api_router prefix ──
route_pattern = re.compile(
    r'(@api_router\.(?:get|post|put|delete|patch)\("(/[^"]+)"\).*?(?=\n@api_router\.|# =====|\Z))',
    re.DOTALL
)

# Group routes by module prefix
route_groups = {}
prefix_map = {
    '/auth/': 'auth',
    '/admin/members': 'people', '/admin/people': 'people', '/admin/households': 'people',
    '/admin/leads': 'people', '/admin/permissions': 'people', '/admin/roles': 'people',
    '/people': 'people',
    '/admin/events': 'events', '/admin/calendar': 'events', '/admin/registrations': 'events',
    '/admin/giving': 'giving', '/donations': 'giving', '/batches': 'giving', '/funds': 'giving',
    '/admin/groups': 'groups', '/group-types': 'groups',
    '/admin/service': 'services', '/admin/songs': 'services', '/admin/volunteers': 'services',
    '/music-stand': 'services',
    '/admin/checkin': 'checkins', '/admin/kids': 'checkins',
    '/admin/communications': 'communications', '/admin/notifications': 'communications',
    '/sms/': 'communications',
    '/admin/media': 'media',
    '/admin/cafe': 'cafe',
    '/admin/merch': 'merch',
    '/admin/pathways': 'courses', '/admin/courses': 'courses',
    '/admin/reports': 'reports', '/reports/': 'reports',
    '/admin/settings': 'settings', '/admin/api-keys': 'settings',
    '/admin/smart-lists': 'workflows', '/admin/workflows': 'workflows', '/admin/forms': 'workflows',
    '/portal/': 'portal',
    '/solomon/': 'solomon',
    '/platform/': 'platform',
    '/solomonpay/': 'payments', '/payment/': 'payments', '/admin/payment': 'payments',
    '/webhook/stripe': 'payments', '/checkout/': 'payments',
    '/v1/agent': 'agent_api',
    '/health': 'public', '/search': 'public', '/tenant': 'public', '/register/': 'public',
    '/public/': 'public',
}

# Count routes per prefix  
route_count = 0
for m in route_pattern.finditer(content):
    path = m.group(2)
    route_count += 1
    
    module = 'misc'
    for prefix, mod in prefix_map.items():
        if path.startswith(prefix):
            module = mod
            break
    
    route_groups.setdefault(module, [])
    route_groups[module].append(path)

print(f"\nFound {route_count} routes across {len(route_groups)} modules:")
for mod, routes in sorted(route_groups.items(), key=lambda x: -len(x[1])):
    print(f"  {mod}: {len(routes)} routes")

# ── Step 3: Compute line ranges for each section ──
# Find all section markers
section_markers = []
for i, line in enumerate(lines):
    if line.startswith("# ====="):
        section_markers.append((i, line.strip()))
    elif line.startswith("@api_router."):
        # Extract method and path
        match = re.match(r'@api_router\.\w+\("(/[^"]+)"', line)
        if match:
            section_markers.append((i, f"ROUTE: {match.group(1)}"))

print(f"\nSection markers: {len(section_markers)}")
print("\nRefactor analysis complete. Files will be generated in Phase R3.")
