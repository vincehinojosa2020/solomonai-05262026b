#!/usr/bin/env python3
"""
Post-generation fixup script.
- Removes inline definitions of functions that are now in core/helpers.py
- Adds proper imports
- Fixes get_current_user references to use get_current_portal_user
"""
import re
import os

ROUTES_DIR = "/app/backend/routes"

# Functions that are now in core/helpers.py and should be imported, not defined inline
HELPER_FUNCTIONS_TO_REMOVE = [
    "def extract_youtube_id",
    "def generate_pickup_code",
    "def compute_health_score",
    "async def get_tenant_giving_metrics",
    "async def calculate_attendance_streak",
    "def _load_competitor_knowledge",
    "_load_competitor_knowledge()",
    "COMPETITOR_KNOWLEDGE = ",
    "SOLOMON_SYSTEM_PROMPT = ",
    "async def get_church_context",
    "def generate_next_steps_certificate_pdf",
    "async def evaluate_member_next_steps_membership",
    "async def get_next_steps_required_course_ids",
    "DEFAULT_MERCH_EMBED_URL = ",
    "DEFAULT_NEXT_STEPS_URL = ",
    "AGENT_PERMISSIONS = ",
    "ANOMALY_THRESHOLDS = ",
    "AUTH_RATE_LIMIT = {}",
    "AUTH_RATE_LIMIT_MAX = ",
    "AUTH_RATE_LIMIT_WINDOW = ",
    "def check_rate_limit(",
    "def hash_api_key(",
    "def generate_api_key(",
    "async def validate_agent_api_key(",
    "def check_agent_permission(",
    "async def transcribe_audio_with_whisper(",
    "async def summarize_meeting_with_claude(",
    "async def notify_meeting_event(",
    "def serialize_doc(",
    "def duration_to_seconds(",
    "async def send_welcome_email(",
]

# Also remove redundant core function redefinitions
CORE_FUNCTIONS_TO_REMOVE = [
    "async def get_current_member_user(",
    "async def get_current_admin_user(",
    "async def get_current_portal_user(",
    "# get_current_admin_user: imported from core",
    "# Multi-tenant config",
    "# get_current_member_user: imported from core",
]

# Functions to strip from route files (their entire body)
FUNCTIONS_TO_STRIP_BODY = {
    "extract_youtube_id", "generate_pickup_code", "compute_health_score",
    "get_tenant_giving_metrics", "calculate_attendance_streak",
    "_load_competitor_knowledge", "get_church_context",
    "generate_next_steps_certificate_pdf", "evaluate_member_next_steps_membership",
    "get_next_steps_required_course_ids", "check_rate_limit",
    "hash_api_key", "generate_api_key", "validate_agent_api_key",
    "check_agent_permission", "transcribe_audio_with_whisper",
    "summarize_meeting_with_claude", "notify_meeting_event",
    "serialize_doc", "duration_to_seconds", "send_welcome_email",
    "get_current_member_user", "get_current_admin_user", "get_current_portal_user",
}


def remove_function_definitions(content, func_names):
    """Remove entire function definitions (def ... until next top-level statement)."""
    lines = content.split('\n')
    result = []
    skip_until_dedent = False
    skip_func_name = None
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        if skip_until_dedent:
            # Check if we've left the function body
            if stripped and not stripped.startswith('#') and not line.startswith(' ') and not line.startswith('\t'):
                # We've hit a new top-level statement
                skip_until_dedent = False
                skip_func_name = None
                # Don't skip this line
            else:
                i += 1
                continue
        
        # Check if this line starts a function we want to remove
        should_skip = False
        for func_name in func_names:
            if (f"def {func_name}(" in stripped or f"async def {func_name}(" in stripped) and not line.startswith(' '):
                should_skip = True
                skip_func_name = func_name
                break
        
        if should_skip:
            skip_until_dedent = True
            i += 1
            continue
        
        # Remove standalone invocations of _load_competitor_knowledge()
        if stripped == "_load_competitor_knowledge()":
            i += 1
            continue
            
        result.append(line)
        i += 1
    
    return '\n'.join(result)


def remove_constant_blocks(content):
    """Remove multi-line constant definitions like SOLOMON_SYSTEM_PROMPT = triple-quote..."""
    # Remove SOLOMON_SYSTEM_PROMPT = """..."""
    content = re.sub(r'SOLOMON_SYSTEM_PROMPT\s*=\s*""".*?"""', '', content, flags=re.DOTALL)
    
    # Remove COMPETITOR_KNOWLEDGE = ""
    content = re.sub(r'^COMPETITOR_KNOWLEDGE\s*=\s*""$', '', content, flags=re.MULTILINE)
    
    # Remove AGENT_PERMISSIONS = {  ... }
    content = re.sub(r'^AGENT_PERMISSIONS\s*=\s*\{[^}]+\}', '', content, flags=re.MULTILINE | re.DOTALL)
    
    # Remove ANOMALY_THRESHOLDS = { ... }
    content = re.sub(r'^ANOMALY_THRESHOLDS\s*=\s*\{[^}]+\}', '', content, flags=re.MULTILINE | re.DOTALL)
    
    # Remove DEFAULT_MERCH_EMBED_URL = "..."
    content = re.sub(r'^DEFAULT_MERCH_EMBED_URL\s*=\s*"[^"]*"', '', content, flags=re.MULTILINE)
    
    # Remove DEFAULT_NEXT_STEPS_URL = "..."
    content = re.sub(r'^DEFAULT_NEXT_STEPS_URL\s*=\s*"[^"]*"', '', content, flags=re.MULTILINE)
    
    # Remove AUTH_RATE_LIMIT = {}
    content = re.sub(r'^AUTH_RATE_LIMIT\s*=\s*\{\}', '', content, flags=re.MULTILINE)
    content = re.sub(r'^AUTH_RATE_LIMIT_MAX\s*=\s*\d+', '', content, flags=re.MULTILINE)
    content = re.sub(r'^AUTH_RATE_LIMIT_WINDOW\s*=\s*\d+', '', content, flags=re.MULTILINE)
    
    return content


def fix_get_current_user_calls(content):
    """Replace get_current_user(request) calls with get_current_portal_user(request)."""
    # Only replace direct calls, not the function definition
    content = content.replace(
        'await get_current_user(request)',
        'await get_current_portal_user(request)'
    )
    return content


def clean_excessive_blank_lines(content):
    """Reduce 3+ consecutive blank lines to 2."""
    return re.sub(r'\n{4,}', '\n\n\n', content)


def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_len = len(content)
    
    # Remove function definitions
    content = remove_function_definitions(content, FUNCTIONS_TO_STRIP_BODY)
    
    # Remove constant blocks
    content = remove_constant_blocks(content)
    
    # Fix get_current_user references
    content = fix_get_current_user_calls(content)
    
    # Clean up blank lines
    content = clean_excessive_blank_lines(content)
    
    if len(content) != original_len:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed {os.path.basename(filepath)}: {original_len} -> {len(content)} chars")
    else:
        print(f"No changes: {os.path.basename(filepath)}")


def main():
    for filename in sorted(os.listdir(ROUTES_DIR)):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(ROUTES_DIR, filename)
            process_file(filepath)


if __name__ == '__main__':
    main()
