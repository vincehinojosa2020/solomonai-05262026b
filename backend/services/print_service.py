"""Solomon AI — Print Service Scaffolding
Supports label printing for check-in (Brother QL, Zebra ZD/GK, Dymo LabelWriter).
Stubbed until physical printers are connected.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from core import db

logger = logging.getLogger("solomon.print")


LABEL_TEMPLATES = {
    "child_checkin": {
        "width": 62,  # mm
        "height": 29,
        "fields": ["child_name", "parent_name", "room", "security_code", "allergies", "timestamp"],
    },
    "name_tag": {
        "width": 62,
        "height": 29,
        "fields": ["name", "role", "campus"],
    },
    "visitor": {
        "width": 62,
        "height": 29,
        "fields": ["name", "date", "campus", "welcome_message"],
    },
}


def generate_zpl(label_data: dict, template: str = "child_checkin") -> str:
    """Generate ZPL (Zebra Programming Language) for Zebra printers."""
    t = LABEL_TEMPLATES.get(template, LABEL_TEMPLATES["child_checkin"])
    name = label_data.get("child_name", label_data.get("name", ""))
    parent = label_data.get("parent_name", "")
    room = label_data.get("room", "")
    code = label_data.get("security_code", "")
    allergies = label_data.get("allergies", "")
    ts = label_data.get("timestamp", datetime.now(timezone.utc).strftime("%I:%M %p"))

    zpl = f"""^XA
^CF0,40^FO50,30^FD{name}^FS
^CF0,25^FO50,80^FDParent: {parent}^FS
^CF0,30^FO50,115^FDRoom: {room}^FS
^CF0,60^FO400,30^FD{code}^FS
{"^CF0,20^FO50,155^FDALLERGIES: " + allergies + "^FS" if allergies else ""}
^CF0,18^FO400,155^FD{ts}^FS
^XZ"""
    return zpl


def generate_label_preview(label_data: dict, template: str = "child_checkin") -> dict:
    """Generate a preview-friendly representation of the label."""
    t = LABEL_TEMPLATES.get(template, LABEL_TEMPLATES["child_checkin"])
    return {
        "template": template,
        "width_mm": t["width"],
        "height_mm": t["height"],
        "fields": {f: label_data.get(f, "") for f in t["fields"]},
        "preview_text": _format_preview(label_data, template),
    }


def _format_preview(data: dict, template: str) -> str:
    if template == "child_checkin":
        return f"{data.get('child_name', '')} | Room: {data.get('room', '')} | Code: {data.get('security_code', '')} | Parent: {data.get('parent_name', '')}"
    elif template == "name_tag":
        return f"{data.get('name', '')} | {data.get('role', '')}"
    return str(data)


async def get_available_printers(tenant_id: str) -> list:
    """Get configured printers for a tenant."""
    printers = await db.printers.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(20)
    return printers


async def add_printer(tenant_id: str, config: dict) -> dict:
    """Add a printer configuration."""
    import uuid
    printer = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "name": config.get("name", "Label Printer"),
        "type": config.get("type", "zebra"),  # zebra, brother, dymo
        "connection": config.get("connection", "network"),  # network, usb
        "ip_address": config.get("ip_address", ""),
        "port": config.get("port", 9100),
        "station_id": config.get("station_id", ""),
        "label_template": config.get("label_template", "child_checkin"),
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.printers.insert_one(printer)
    return {k: v for k, v in printer.items() if k != "_id"}


async def print_label(label_data: dict, printer_id: str = None, tenant_id: str = "") -> dict:
    """Send label to printer. Currently stubbed — returns preview."""
    printer = None
    if printer_id:
        printer = await db.printers.find_one({"id": printer_id, "tenant_id": tenant_id}, {"_id": 0})

    preview = generate_label_preview(label_data)
    zpl = generate_zpl(label_data) if (printer and printer.get("type") == "zebra") else None

    # Log print job
    job = {
        "tenant_id": tenant_id,
        "printer_id": printer_id,
        "label_data": label_data,
        "status": "preview" if not printer else "queued",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.print_jobs.insert_one(job)

    if not printer:
        return {"status": "preview", "preview": preview, "message": "No printer configured — showing preview only"}

    # TODO: When physical printer is connected, send ZPL/raster data here
    return {"status": "queued", "preview": preview, "printer": printer.get("name"), "message": f"Label queued for {printer.get('name')}"}


async def test_print(printer_id: str, tenant_id: str) -> dict:
    """Send test label to printer."""
    test_data = {
        "child_name": "Test Child",
        "parent_name": "Test Parent",
        "room": "Room 101",
        "security_code": "ABC123",
        "allergies": "",
        "timestamp": datetime.now(timezone.utc).strftime("%I:%M %p"),
    }
    return await print_label(test_data, printer_id, tenant_id)
