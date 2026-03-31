#!/usr/bin/env python3
"""
Route Extraction Script for Solomon AI
Parses server.py and extracts route handlers into domain-specific files.
"""
import re
import sys
from collections import defaultdict

ROUTE_DOMAIN_MAP = {
    # Auth
    '/auth/': 'auth',
    # Portal
    '/portal/': 'portal',
    # Admin sub-domains
    '/admin/pathways/': 'admin_pathways',
    '/admin/next-steps/': 'admin_pathways',
    '/admin/thinkific': 'admin_pathways',
    '/admin/merch/': 'admin_merch',
    '/admin/kids/': 'admin_checkins',
    '/admin/checkin/': 'admin_checkins',
    '/admin/cafe/': 'admin_cafe',
    '/admin/meetings/': 'admin_meetings',
    '/admin/members/': 'admin_people',
    '/admin/households': 'admin_people',
    '/admin/people/': 'admin_people',
    '/admin/roles/': 'admin_people',
    '/admin/groups/': 'admin_groups',
    '/admin/registrations/': 'admin_events',
    '/admin/events/': 'admin_events',
    '/admin/calendar/': 'admin_events',
    '/admin/giving/': 'admin_giving',
    '/admin/services/': 'admin_services',
    '/admin/songs/': 'admin_services',
    '/admin/service-types': 'admin_services',
    '/admin/volunteers/': 'admin_services',
    '/admin/media/': 'admin_media',
    '/admin/communications/': 'admin_comms',
    '/admin/sunday-morning/': 'admin_comms',
    '/admin/prayer/': 'admin_comms',
    '/admin/notifications/': 'admin_comms',
    '/admin/workflows': 'admin_workflows',
    '/admin/forms': 'admin_workflows',
    '/admin/smart-lists': 'admin_workflows',
    '/admin/settings/': 'admin_settings',
    '/admin/api-keys': 'admin_settings',
    '/admin/audit-log': 'admin_settings',
    '/admin/qr/': 'admin_settings',
    '/admin/dashboard': 'admin_settings',
    '/admin/attendance/': 'admin_settings',
    '/admin/war-room': 'admin_settings',
    '/admin/reports/': 'reports',
    '/admin/notes': 'admin_comms',
    # Reports
    '/reports/': 'reports',
    # Payments
    '/payments/': 'payments',
    '/solomonpay/': 'payments',
    '/webhook/': 'payments',
    # Platform admin
    '/platform/': 'platform',
    '/seed': 'platform',
    '/seed-platform': 'platform',
    # Agent API
    '/v1/agent/': 'agent',
    # Solomon AI chat
    '/solomon/': 'solomon',
    # Public/misc routes
    '/people': 'public_api',
    '/households': 'public_api',
    '/groups': 'public_api',
    '/group-types': 'public_api',
    '/services': 'public_api',
    '/service-types': 'public_api',
    '/attendance': 'public_api',
    '/funds': 'public_api',
    '/giving/': 'public_api',
    '/donations': 'public_api',
    '/batches': 'public_api',
    '/events': 'public_api',
    '/communications': 'public_api',
    '/forms/': 'public_api',
    '/register/': 'public_api',
    '/tenants': 'public_api',
    '/tenant': 'public_api',
    '/dashboard/': 'public_api',
    '/search': 'public_api',
    '/churches/': 'public_api',
    '/music-stand/': 'public_api',
    '/leads/': 'public_api',
    '/sms/': 'admin_comms',
    '/health': 'public_api',
    '/clear-site-data': 'public_api',
    '/waitlist/': 'public_api',
    '/demo-requests': 'public_api',
}

def classify_route(path):
    """Determine which domain file a route belongs to."""
    # Try longest prefix match first
    candidates = []
    for prefix, domain in ROUTE_DOMAIN_MAP.items():
        if path.startswith(prefix) or path == prefix.rstrip('/'):
            candidates.append((len(prefix), domain))
    if candidates:
        candidates.sort(reverse=True)
        return candidates[0][1]
    # Root route
    if path == '/':
        return 'public_api'
    print(f"WARNING: Unclassified route: {path}", file=sys.stderr)
    return 'public_api'

def parse_server():
    with open('server.py', 'r') as f:
        lines = f.readlines()
    
    total = len(lines)
    
    # Find all @api_router decorator positions
    route_positions = []
    for i, line in enumerate(lines):
        m = re.match(r'^@api_router\.(get|post|put|patch|delete)\("([^"]+)"', line)
        if m:
            method = m.group(1)
            path = m.group(2)
            route_positions.append((i, method, path))
    
    print(f"Found {len(route_positions)} route decorators")
    
    # For each route, find the function body (from decorator to next top-level definition)
    route_blocks = []
    for idx, (line_num, method, path) in enumerate(route_positions):
        start = line_num
        
        # Find end: next @api_router, or next top-level def/class/assignment
        if idx + 1 < len(route_positions):
            end = route_positions[idx + 1][0]
        else:
            # Last route - find the end
            end = total
            for j in range(line_num + 2, total):
                stripped = lines[j].rstrip()
                if stripped and not stripped.startswith(' ') and not stripped.startswith('#') and not stripped.startswith('"""'):
                    # Check if it's a new top-level definition
                    if re.match(r'^(def |async def |class |@|app\.|from |import |[A-Z_]+ =)', stripped):
                        end = j
                        break
        
        # Trim trailing blank lines
        while end > start and lines[end-1].strip() == '':
            end -= 1
        end += 1  # Include one blank line
        
        block = ''.join(lines[start:end])
        domain = classify_route(path)
        route_blocks.append({
            'start': start,
            'end': end,
            'method': method,
            'path': path,
            'domain': domain,
            'code': block,
        })
    
    # Group by domain
    domains = defaultdict(list)
    for rb in route_blocks:
        domains[rb['domain']].append(rb)
    
    # Print summary
    print("\n=== Route Distribution ===")
    for domain, blocks in sorted(domains.items(), key=lambda x: -len(x[1])):
        paths = [b['path'] for b in blocks]
        print(f"\n{domain}: {len(blocks)} routes")
        for p in paths[:5]:
            print(f"  {p}")
        if len(paths) > 5:
            print(f"  ... and {len(paths)-5} more")
    
    return domains, route_blocks

if __name__ == '__main__':
    domains, blocks = parse_server()
    
    # Write route files
    for domain, blocks_list in domains.items():
        code_parts = []
        for b in blocks_list:
            # Replace @api_router with @router
            code = b['code'].replace('@api_router.', '@router.')
            code_parts.append(code)
        
        filepath = f'/tmp/extracted_{domain}.py'
        with open(filepath, 'w') as f:
            f.write('\n'.join(code_parts))
        print(f"Wrote {filepath} ({len(blocks_list)} routes, {sum(len(b['code'].splitlines()) for b in blocks_list)} lines)")
