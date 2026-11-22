"""Typed shapes of the Shortn API's request fields and responses.

Every response is returned as the decoded JSON (plain ``dict`` and ``list``
objects); these ``TypedDict`` classes describe the documented keys for type
checkers and editors. Keys the API adds later are still in the dicts.
All classes are ``total=False``: a key can be missing.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional, TypedDict, Union

# --------------------------------------------------------------------------
# Shared


# A time the SDK sends as RFC 3339 in UTC: an RFC 3339 string, a datetime (naive ones count
# as UTC) or a date (midnight UTC).
DateTimeInput = Union[str, datetime, date]

class Pagination(TypedDict, total=False):
    limit: int
    offset: int
    count: int
    has_more: bool
    next_offset: Optional[int]
    #: Sent only when the request asked for it (``include_total=True``).
    total: int


class TagRef(TypedDict, total=False):
    public_id: str
    name: str
    color: str


class TeamRef(TypedDict, total=False):
    team_id: int
    team_public_id: str
    team_name: str


class MessageResponse(TypedDict, total=False):
    message: str


class SuccessResponse(TypedDict, total=False):
    success: bool
    workspace_wide: bool
    team_public_ids: List[str]
    team_names: List[str]
    teams: List[TeamRef]


# --------------------------------------------------------------------------
# Links


class GeoOverride(TypedDict):
    target: str
    url: str


class ABVariantInput(TypedDict, total=False):
    url: str
    split_percent: int


class LinkAttribution(TypedDict, total=False):
    type: Literal["workspace", "workspace_member", "team", "external_partner", "campaign", "custom"]
    user_public_id: str
    team_public_id: str
    partner_public_id: str
    external_id: str
    label: str


class LinkCreateParams(TypedDict, total=False):
    """Optional fields of ``POST /links``; ``url`` and ``title`` are arguments."""

    description: str
    custom_code: str
    short_domain: str
    workspace_public_id: str
    team_public_ids: List[str]
    team_public_id: str
    tag_public_ids: List[str]
    utm_template_id: str
    utm_source: str
    utm_medium: str
    utm_campaign: str
    utm_term: str
    utm_content: str
    utm_id: str
    starts_at: DateTimeInput
    expires_at: DateTimeInput
    expiration_action: Literal["suspended", "archive"]
    access_mode: Literal["password", "jit"]
    password: str
    access_duration_hours: int
    jit_allowlist: List[str]
    targeting_geo_overrides: List[GeoOverride]
    language_targets: Dict[str, str]
    device_targets: Dict[str, str]
    os_targets: Dict[str, str]
    browser_targets: Dict[str, str]
    mobile_target_ios: str
    mobile_target_android: str
    targeting_priority: List[str]
    ab_variants: List[ABVariantInput]
    ab_destination: str
    ab_split_percent: int
    conversion_enabled: bool
    conversion_attribution_model: Literal["inherit", "first_touch", "last_touch"]
    conversion_attribution_window_days: int
    attribution: LinkAttribution
    preview_title: str
    preview_description: str
    preview_image: str
    preview_custom: bool
    cloaking_enabled: bool


class LinkUpdateParams(TypedDict, total=False):
    """Fields ``PATCH /links/{public_id}`` changes; any other field is refused."""

    title: str
    description: str
    url: str
    short_code: str
    domain: str
    status: Literal["active", "suspended", "archived", "scheduled"]
    active: bool
    team_public_ids: List[str]
    team_public_id: str


class CreatedLink(TypedDict, total=False):
    public_id: str
    short_url: str
    short_code: str
    original_url: str
    title: str
    link_status: str
    security_verdict: str
    security_risk_score: int
    security_reason_codes: List[str]
    expires_at: str


class Link(TypedDict, total=False):
    public_id: str
    original_url: str
    short_code: str
    domain: str
    title: str
    description: str
    clicks: int
    active: bool
    status: str
    security_status: str
    workspace_public_id: str
    workspace_name: str
    tags: List[TagRef]
    starts_at: str
    expires_at: str
    created_at: str
    updated_at: str


class LinkList(TypedDict, total=False):
    data: List[Link]
    pagination: Pagination


class LinkResponse(TypedDict, total=False):
    data: Link


class ABWinnerResponse(TypedDict, total=False):
    winner: str
    test: int
    destination: str


class LinkAnalytics(TypedDict, total=False):
    total_clicks: int
    unique_clicks: int
    clicks_by_country: Dict[str, int]


# --------------------------------------------------------------------------
# Workspaces


class Workspace(TypedDict, total=False):
    public_id: str
    name: str
    slug: str
    description: str
    is_personal: bool
    active: bool
    role: str
    team_count: int
    member_count: int
    link_count: int
    created_at: str
    updated_at: str


class WorkspaceList(TypedDict, total=False):
    data: List[Workspace]


class WorkspaceResponse(TypedDict, total=False):
    data: Workspace


# --------------------------------------------------------------------------
# Tags


class TagUpdateParams(TypedDict, total=False):
    name: str
    color: str
    team_public_ids: List[str]


class Tag(TypedDict, total=False):
    id: int
    public_id: str
    user_id: int
    workspace_id: int
    workspace_wide: bool
    name: str
    color: str
    team_public_ids: List[str]
    team_names: List[str]
    url_count: int
    created_at: str
    updated_at: str


class TagList(TypedDict, total=False):
    tags: Optional[List[Tag]]


class TagDeleteResponse(TypedDict, total=False):
    message: str
    links_updated: int


# --------------------------------------------------------------------------
# UTM templates


class UTMTemplateParams(TypedDict, total=False):
    name: str
    utm_source: str
    utm_medium: str
    utm_campaign: str
    utm_term: str
    utm_content: str
    utm_id: str
    team_public_ids: List[str]


class UTMTemplateUpdateParams(UTMTemplateParams, total=False):
    workspace_public_id: str
    lost_access_action: Literal["remove", "copy"]


class UTMTemplate(TypedDict, total=False):
    public_id: str
    workspace_public_id: str
    team_public_id: str
    team_name: str
    team_public_ids: List[str]
    team_names: List[str]
    workspace_wide: bool
    name: str
    utm_source: str
    utm_medium: str
    utm_campaign: str
    utm_term: str
    utm_content: str
    utm_id: str
    created_at: str
    updated_at: str


class UTMTemplateList(TypedDict, total=False):
    data: List[UTMTemplate]


class UTMTemplateResponse(TypedDict, total=False):
    data: UTMTemplate
    move_impact: Dict[str, Any]


class UTMTemplateDeleteResponse(TypedDict, total=False):
    data: Dict[str, Any]


# --------------------------------------------------------------------------
# Destinations


class Destination(TypedDict, total=False):
    id: int
    public_id: str
    name: str
    type: str
    value: str
    team_public_id: str
    team_name: str
    team_public_ids: List[str]
    team_names: List[str]
    workspace_wide: bool
    created_at: str


DestinationType = Literal["email", "webhook", "slack", "discord", "msteams"]


# --------------------------------------------------------------------------
# Teams


class Team(TypedDict, total=False):
    id: int
    public_id: str
    name: str
    slug: str
    description: str
    workspace_id: int
    workspace_public_id: str
    owner_user_id: int
    active: bool
    member_count: int
    link_count: int
    template_count: int
    created_at: str
    updated_at: str


class TeamList(TypedDict, total=False):
    teams: List[Team]


class CreatedTeam(TypedDict, total=False):
    id: int
    slug: str
    public_id: str


# --------------------------------------------------------------------------
# Domains


class Domain(TypedDict, total=False):
    id: int
    domain: str
    is_owner: bool
    owner_name: str
    can_manage: bool
    access_label: str
    status: str
    dns_status: str
    tls_status: str
    provisioning_status: str
    tls_phase: str
    is_active: bool
    is_verified: bool
    ssl_enabled: bool
    ready: bool
    links_using: int
    team_assignment_count: int
    created_at: str
    verified_at: str
    verification_token: str
    verification_failure_count: int
    workspace_public_ids: List[str]
    dns: Dict[str, Any]


class DomainList(TypedDict, total=False):
    data: List[Domain]


class DomainResponse(TypedDict, total=False):
    domain: Domain


class DomainVerifyResponse(TypedDict, total=False):
    domain: Domain
    verification: Dict[str, Any]


class DomainDeleteResponse(TypedDict, total=False):
    deleted: bool
    id: int
    domain: Domain


# --------------------------------------------------------------------------
# Reports and alerts


class ReportRuleParams(TypedDict, total=False):
    """Fields of ``POST`` and ``PATCH /reports/rules``."""

    workspace_public_id: str
    report_type: str
    schedule_type: Literal["every_x", "event"]
    interval_seconds: int
    initial_run_at: DateTimeInput
    report_name: str
    definition_json: Dict[str, Any]
    destination_public_ids: List[str]
    team_public_ids: List[str]
    include_unassigned_links: bool
    link_public_ids: List[str]
    enabled: bool


class ReportRule(TypedDict, total=False):
    public_id: str
    name: str
    workspace_public_id: str
    workspace_name: str
    team_public_id: str
    team_name: str
    team_public_ids: List[str]
    team_names: List[str]
    workspace_wide: bool
    include_unassigned_links: bool
    schedule_type: str
    schedule_interval_seconds: Optional[int]
    next_run_at: Optional[str]
    enabled: bool
    trigger_count: int
    report_name: str
    report_query_type: str
    created_at: str
    destinations: List[Dict[str, Any]]
    definition: Dict[str, Any]


class ReportRuleList(TypedDict, total=False):
    data: List[ReportRule]


class ReportRuleResponse(TypedDict, total=False):
    data: ReportRule


# --------------------------------------------------------------------------
# Conversions


class LeadParams(TypedDict, total=False):
    event_name: str
    lead_category: Literal[
        "signup", "form_submission", "newsletter_signup", "trial_started", "add_to_cart", "checkout_started", "custom"
    ]
    event_quantity: int
    metadata: Dict[str, Any]
    occurred_at: DateTimeInput
    test_mode: bool
    event_type: str


class SaleParams(TypedDict, total=False):
    event_name: str
    amount_cents: int
    amount: str
    settlement_amount_cents: int
    settlement_currency: str
    invoice_id: str
    payment_processor: str
    idempotency_key: str
    metadata: Dict[str, Any]
    occurred_at: DateTimeInput
    test_mode: bool
    event_type: str


class RefundParams(TypedDict, total=False):
    event_name: str
    amount_cents: int
    amount: str
    currency: str
    payment_processor: str
    reason: str
    idempotency_key: str
    metadata: Dict[str, Any]
    occurred_at: DateTimeInput
    test_mode: bool
    event_type: str


class ConversionEvent(TypedDict, total=False):
    public_id: str
    event_type: str
    event_name: str
    lead_category: str
    event_origin: str
    #: The lead recorded with a sale when the click had none yet (``event_origin`` "inferred").
    inferred_lead: ConversionEvent
    duplicate: bool
    is_test: bool
    url_public_id: str
    short_code: str
    click_id: str
    amount_cents: int
    amount: str
    currency: str
    currency_decimals: int
    payment_processor: str
    invoice_id: str
    #: On a refund: the public ID of the refunded sale.
    sale_id: str
    refund_id: str
    reason: str
    refunded_amount_cents: int
    remaining_amount_cents: int
    refund_status: str
    attribution: Dict[str, Any]
    reporting: Dict[str, Any]
    occurred_at: str
    created_at: str


class ConversionResult(TypedDict, total=False):
    type: Literal["lead", "sale", "refund"]
    event: ConversionEvent


class ConversionValidation(TypedDict, total=False):
    valid: bool
    dry_run: bool
    result: Dict[str, Any]


class ConversionSummary(TypedDict, total=False):
    data: Dict[str, Any]


class ConversionReport(TypedDict, total=False):
    data: List[Dict[str, Any]]
    totals: Dict[str, Any]
    pagination: Pagination
    date_range: Dict[str, Any]
    interval: str
    environment: str


class ConversionEventList(TypedDict, total=False):
    data: List[ConversionEvent]
    pagination: Pagination
    date_range: Dict[str, Any]
    environment: str


Environment = Literal["live", "test"]


# --------------------------------------------------------------------------
# Public helpers


class URLValidation(TypedDict, total=False):
    valid: bool
    normalized: str
    code: str
    error: str


class PlanCatalog(TypedDict, total=False):
    plans: Dict[str, Dict[str, Any]]
