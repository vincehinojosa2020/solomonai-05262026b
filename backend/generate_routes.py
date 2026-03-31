#!/usr/bin/env python3
"""
Master Route File Generator for Solomon AI.
Reads extracted route code from /tmp/ and generates complete route modules
with proper imports in /app/backend/routes/.
"""
import re
import os

# ═══ Import templates per domain ═══
ROUTE_HEADERS = {
    "auth": '''"""Solomon AI — Auth Routes"""
from fastapi import APIRouter, HTTPException, Request, Response
from datetime import datetime, timezone
from typing import Optional
import uuid
import hashlib
import logging
import os

from core import (
    db, DEFAULT_TENANT_ID, ROLE_TEMPLATES, check_rate_limit_v2,
    get_permissions_for_user, get_session_token_from_request,
    get_current_admin_user, get_current_portal_user,
    logger,
)
from core.helpers import send_welcome_email, serialize_doc, check_rate_limit
from models.schemas import (
    SessionRequest, EmailLoginRequest, UserRegistrationRequest, User,
)

router = APIRouter()
''',

    "portal": '''"""Solomon AI — Portal (Member-Facing) Routes"""
from fastapi import APIRouter, HTTPException, Request, Response, UploadFile, File, Form, Query
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
import uuid
import random
import logging
import os

from core import (
    db, DEFAULT_TENANT_ID,
    get_current_portal_user, get_current_member_user,
    require_tenant, audit_log, check_idempotency, store_idempotency,
    logger,
)
from core.helpers import (
    serialize_doc, DEFAULT_MERCH_EMBED_URL, DEFAULT_NEXT_STEPS_URL,
    evaluate_member_next_steps_membership, get_next_steps_required_course_ids,
    generate_next_steps_certificate_pdf, notify_meeting_event,
)
from models.schemas import (
    PortalProfileUpdate, WatchProgressUpdate,
    AttendanceCheckinRequest, KidsCheckinRequest,
    ChildCreate, Child, Checkin, Event, Fund, Group, GroupMember,
    LeadershipNote, LeadershipNoteCreate, MerchOrderCreate,
    CafeOrderCreate, PastorMeetingBooking, PastorMeeting,
    PathwaysProgressUpdate, PrayerRequestAliasCreate,
    VideoNote, VideoNoteCreate, VideoNoteUpdate, VideoNoteShare,
    VolunteerSignupRequest, Service, User,
)

router = APIRouter()
''',

    "admin_pathways": '''"""Solomon AI — Admin Pathways & Next Steps Routes"""
from fastapi import APIRouter, HTTPException, Request, Response
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import uuid
import logging

from core import db, get_current_admin_user, require_tenant, logger
from core.helpers import (
    serialize_doc, duration_to_seconds,
    evaluate_member_next_steps_membership,
)
from models.schemas import (
    ThinkificUpdate, NextStepsApprovalRequest,
    PathwaysCourse, PathwaysCourseCreate, PathwaysCourseUpdate,
    PathwaysLesson, PathwaysLessonCreate, PathwaysLessonUpdate,
    PathwaysEnrollment, PathwaysEnrollmentRequest,
    Tenant,
)

router = APIRouter()
''',

    "admin_merch": '''"""Solomon AI — Admin Merch Routes"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from typing import Optional
import uuid
import logging

from core import db, get_current_admin_user, require_tenant, logger
from core.helpers import serialize_doc, DEFAULT_MERCH_EMBED_URL
from models.schemas import (
    MerchProduct, MerchProductCreate, MerchProductUpdate,
    MerchSettingsUpdate, Tenant,
)

router = APIRouter()
''',

    "admin_checkins": '''"""Solomon AI — Admin Kids Check-In Routes"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import uuid
import random
import logging

from core import db, DEFAULT_TENANT_ID, get_current_admin_user, require_tenant, logger
from core.helpers import serialize_doc
from models.schemas import Child, Checkin, Group

router = APIRouter()
''',

    "admin_cafe": '''"""Solomon AI — Admin Cafe Routes"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from typing import Optional
import uuid
import logging

from core import db, get_current_admin_user, require_tenant, logger
from core.helpers import serialize_doc
from models.schemas import (
    CafeItem, CafeItemCreate, CafeItemUpdate,
    CafeSettingsUpdate, Tenant,
)

router = APIRouter()
''',

    "admin_meetings": '''"""Solomon AI — Admin Meetings Routes"""
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path
import uuid
import logging

from core import db, get_current_admin_user, require_tenant, logger
from core.helpers import (
    serialize_doc, transcribe_audio_with_whisper,
    summarize_meeting_with_claude, notify_meeting_event,
)
from models.schemas import (
    PastorMeetingSlot, PastorMeetingSlotCreate,
    PastorMeetingUpdate, Tenant,
)

router = APIRouter()
''',

    "admin_comms": '''"""Solomon AI — Admin Communications, SMS, Notifications, Notes, Prayer Routes"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import uuid
import logging

from core import (
    db, DEFAULT_TENANT_ID,
    get_current_admin_user, require_permission, require_tenant,
    logger,
)
from core.helpers import serialize_doc
from models.schemas import Communication, Attendance, Event, Group, Tenant

router = APIRouter()
''',

    "admin_media": '''"""Solomon AI — Admin Media Routes"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from typing import Optional
import uuid
import logging

from core import db, DEFAULT_TENANT_ID, get_current_admin_user, require_tenant, logger
from core.helpers import serialize_doc
from models.schemas import MediaCategory, MediaVideo, MediaVideoCreate, Tenant

router = APIRouter()
''',

    "admin_people": '''"""Solomon AI — Admin People, Members, Households, Roles Routes"""
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import uuid
import csv
import io
import logging

from core import (
    db, DEFAULT_TENANT_ID, PERMISSION_REGISTRY, ROLE_TEMPLATES,
    get_current_admin_user, require_permission, require_tenant,
    get_permissions_for_user, audit_log,
    logger,
)
from core.helpers import serialize_doc
from models.schemas import Household, User

router = APIRouter()
''',

    "admin_groups": '''"""Solomon AI — Admin Groups Routes"""
from fastapi import APIRouter, HTTPException, Request, Query
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import uuid
import logging

from core import db, get_current_admin_user, require_tenant, logger
from core.helpers import serialize_doc
from models.schemas import Group, Attendance, Event, Person, Tenant

router = APIRouter()
''',

    "admin_events": '''"""Solomon AI — Admin Events, Calendar, Registrations Routes"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import uuid
import logging

from core import db, get_current_admin_user, require_tenant, logger
from core.helpers import serialize_doc
from models.schemas import Event, Tenant

router = APIRouter()
''',

    "admin_giving": '''"""Solomon AI — Admin Giving Routes"""
from fastapi import APIRouter, HTTPException, Request, Response
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import uuid
import logging

from core import (
    db, DEFAULT_TENANT_ID,
    get_current_admin_user, require_permission, require_tenant,
    logger,
)
from core.helpers import serialize_doc
from models.schemas import Fund, Group, Person, Tenant

router = APIRouter()
''',

    "admin_services": '''"""Solomon AI — Admin Services, Songs, Volunteers, Templates Routes"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from typing import Optional, List
import uuid
import logging

from core import (
    db, DEFAULT_TENANT_ID,
    require_permission, get_current_admin_user, require_tenant,
    logger,
)
from core.helpers import serialize_doc
from models.schemas import Service

router = APIRouter()
''',

    "admin_settings": '''"""Solomon AI — Admin Settings, Branding, API Keys, Dashboard, War Room Routes"""
from fastapi import APIRouter, HTTPException, Request, Query
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
import uuid
import logging

from core import (
    db, DEFAULT_TENANT_ID,
    get_current_admin_user, require_permission, require_tenant,
    audit_log,
    logger,
)
from core.helpers import (
    serialize_doc, generate_api_key, AGENT_PERMISSIONS,
)
from models.schemas import (
    AgentAPIKey, AgentAPIKeyCreate,
    Fund, Group, Service, Tenant,
)

router = APIRouter()
''',

    "admin_workflows": '''"""Solomon AI — Admin Workflows, Forms, Smart Lists Routes"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import uuid
import logging

from core import db, get_current_admin_user, require_tenant, logger
from core.helpers import serialize_doc

router = APIRouter()
''',

    "reports": '''"""Solomon AI — Reports Routes"""
from fastapi import APIRouter, HTTPException, Request, Response
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import uuid
import csv
import io
import logging

from core import (
    db, DEFAULT_TENANT_ID,
    require_permission, audit_log,
    logger,
)
from core.helpers import serialize_doc
from models.schemas import Attendance, Child, Fund, Group, Person, Service, User

router = APIRouter()
''',

    "payments": '''"""Solomon AI — Payments, SolomonPay, Stripe Webhook Routes"""
from fastapi import APIRouter, HTTPException, Request, Response
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import uuid
import logging
import os

from core import db, DEFAULT_TENANT_ID, logger
from core.helpers import serialize_doc
from models.schemas import Donation, Fund, User

try:
    from emergentintegrations.payments.stripe.checkout import (
        StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
    )
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False

router = APIRouter()
''',

    "platform": '''"""Solomon AI — Platform Admin, Seed Routes"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
import uuid
import hashlib
import logging
import random
import os

from core import (
    db, DEFAULT_TENANT_ID, ROLE_TEMPLATES,
    get_permissions_for_user, audit_log,
    logger,
)
from core.helpers import serialize_doc, DEFAULT_MERCH_EMBED_URL
from models.schemas import (
    Attendance, Donation, Fund, Group, Service, User,
)

router = APIRouter()
''',

    "agent": '''"""Solomon AI — v1 Agent API Routes"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import uuid
import logging

from core import db, logger
from core.helpers import (
    serialize_doc, validate_agent_api_key, check_agent_permission,
    ANOMALY_THRESHOLDS,
)

router = APIRouter()
''',

    "solomon": '''"""Solomon AI — Solomon Chat Routes"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import uuid
import logging
import os

from core import db, get_current_portal_user, require_tenant, logger
from core.helpers import serialize_doc
from models.schemas import SolomonChatRequest, SolomonChatResponse

from emergentintegrations.llm.chat import LlmChat, UserMessage

router = APIRouter()
''',

    "public_api": '''"""Solomon AI — Public API Routes (People, Groups, Events, Tenants, etc.)"""
from fastapi import APIRouter, HTTPException, Request, Response, Query
from datetime import datetime, timezone, timedelta, date
from typing import Optional, List, Dict, Any
import uuid
import logging
import json
import os

from core import (
    db, DEFAULT_TENANT_ID,
    get_current_admin_user, get_current_member_user,
    get_tenant_by_subdomain, require_tenant, audit_log,
    logger,
)
from core.helpers import serialize_doc, DEFAULT_MERCH_EMBED_URL
from models.schemas import (
    Attendance, Communication, Donation, DonationBase, DonationBatch,
    Event, Fund, Group, Household, Person, PersonCreate,
    Service, Tenant, TenantBase, User,
)

router = APIRouter()
''',
}


def main():
    output_dir = "/app/backend/routes"
    os.makedirs(output_dir, exist_ok=True)

    for domain, header in ROUTE_HEADERS.items():
        extracted_path = f"/tmp/extracted_{domain}.py"
        if not os.path.exists(extracted_path):
            print(f"SKIP: {extracted_path} not found")
            continue

        with open(extracted_path, 'r') as f:
            route_code = f.read()

        # The extracted code has @router. decorators (already replaced by extraction script)
        output_path = os.path.join(output_dir, f"{domain}.py")
        with open(output_path, 'w') as f:
            f.write(header)
            f.write("\n")
            f.write(route_code)

        line_count = len(open(output_path).readlines())
        route_count = route_code.count("@router.")
        print(f"Created {output_path}: {route_count} routes, {line_count} lines")


if __name__ == "__main__":
    main()
