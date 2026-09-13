WORKFLOW_CONFIG = {
    "entry": "route_event",
    "exit": "end",
    "nodes": [
        "route_event",
        "process_assignment_pdf",
        "classify_email_reply",
        "apply_crm_update",
        "send_driver_details_ack",
        "schedule_delivery_followup",
        "send_on_track_carrier_ack",
        "notify_customer",
        "end",
    ],
    "edges": [
        ["process_assignment_pdf", "end"],
        ["send_driver_details_ack", "schedule_delivery_followup"],
        ["schedule_delivery_followup", "end"],
        ["send_on_track_carrier_ack", "end"],
    ],
    "routers": {
        "route_event": {
            "router": "event_type",
            "map": {
                "pdf_assignment": "process_assignment_pdf",
                "email_reply": "classify_email_reply",
                "unknown": "end",
            },
        },
        "classify_email_reply": {
            "router": "classification",
            "map": {
                "driver_details": "apply_crm_update",
                "delivery_delay": "apply_crm_update",
                "delivery_status": "apply_crm_update",
                "insufficient": "end",
                "skip": "end",
            },
        },
        "apply_crm_update": {
            "router": "crm_next",
            "map": {
                "ack": "send_driver_details_ack",
                "on_track_ack": "send_on_track_carrier_ack",
                "notify": "notify_customer",
                "end": "end",
            },
        },
        "notify_customer": {
            "router": "always_end",
            "map": {"end": "end"},
        },
    },
}
