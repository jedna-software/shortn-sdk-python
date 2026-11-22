"""Resource groups of the Shortn API. Reach them through a :class:`~shortn_sdk.Shortn` client."""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional, Sequence, Union

from .client import path

if TYPE_CHECKING:
    from typing_extensions import Unpack

    from .client import Shortn
    from .types import (
        ABWinnerResponse,
        ConversionEventList,
        ConversionReport,
        ConversionResult,
        ConversionSummary,
        ConversionValidation,
        CreatedLink,
        CreatedTeam,
        Destination,
        DestinationType,
        DomainDeleteResponse,
        DomainList,
        DomainResponse,
        DomainVerifyResponse,
        Environment,
        LeadParams,
        LinkAnalytics,
        LinkCreateParams,
        LinkList,
        LinkResponse,
        LinkUpdateParams,
        MessageResponse,
        PlanCatalog,
        RefundParams,
        ReportRuleList,
        ReportRuleParams,
        ReportRuleResponse,
        SaleParams,
        SuccessResponse,
        Tag,
        TagDeleteResponse,
        TagList,
        TagUpdateParams,
        Team,
        TeamList,
        URLValidation,
        UTMTemplateDeleteResponse,
        UTMTemplateList,
        UTMTemplateParams,
        UTMTemplateResponse,
        UTMTemplateUpdateParams,
        Workspace,
        WorkspaceList,
        WorkspaceResponse,
    )

DateArg = Union[str, date]
IDList = Union[Sequence[str], str]


class _Resource:
    def __init__(self, client: Shortn) -> None:
        self._client = client

    def _get(self, route: str, query: Mapping[str, Any] | None = None) -> Any:
        return self._client.request("GET", route, query=query)

    def _post(self, route: str, body: Mapping[str, Any] | None = None) -> Any:
        return self._client.request("POST", route, body=body)

    def _put(self, route: str, body: Mapping[str, Any] | None = None) -> Any:
        return self._client.request("PUT", route, body=body)

    def _patch(self, route: str, body: Mapping[str, Any] | None = None) -> Any:
        return self._client.request("PATCH", route, body=body)

    def _delete(self, route: str, query: Mapping[str, Any] | None = None) -> Any:
        return self._client.request("DELETE", route, query=query)


class LinksResource(_Resource):
    """``/links``: create, read, update, suspend and re-enable links. Scopes ``links:read``, ``links:write``."""

    def list(self, *, limit: int | None = None, offset: int | None = None) -> LinkList:
        """``GET /links``: links, newest first. Follow ``pagination.next_offset`` for more."""
        return self._get("/links", {"limit": limit, "offset": offset})

    def get(self, public_id: str) -> LinkResponse:
        """``GET /links/{public_id}``: one link under ``data``."""
        return self._get(path("links", public_id))

    def create(self, *, url: str, title: str, **params: Unpack[LinkCreateParams]) -> CreatedLink:
        """``POST /links``: create a link. Every optional field of the API is a keyword argument."""
        return self._post("/links", {"url": url, "title": title, **params})

    def update(self, public_id: str, **params: Unpack[LinkUpdateParams]) -> MessageResponse:
        """``PATCH /links/{public_id}``: change the fields you pass."""
        return self._patch(path("links", public_id), params)

    def delete(self, public_id: str) -> MessageResponse:
        """``DELETE /links/{public_id}``: suspend the link. It keeps its analytics and can be re-enabled."""
        return self._delete(path("links", public_id))

    def enable(self, public_id: str) -> MessageResponse:
        """``POST /links/{public_id}/enable``: make a suspended link active again."""
        return self._post(path("links", public_id, "enable"))

    def set_ab_winner(self, public_id: str, *, variant: str) -> ABWinnerResponse:
        """``POST /links/{public_id}/ab/winner``: end the A/B test; ``variant`` is the winner's letter."""
        return self._post(path("links", public_id, "ab", "winner"), {"variant": variant})


class AnalyticsResource(_Resource):
    """``/analytics``: link click totals. Scope ``analytics:read``; counts toward the analytics rate limit."""

    def link(self, public_id: str, *, query: Mapping[str, Any] | None = None) -> LinkAnalytics:
        """``GET /analytics/links/{public_id}``: all-time totals and clicks by country.

        The endpoint takes no query parameters today; ``query`` passes any you need through as is.
        """
        return self._get(path("analytics", "links", public_id), query)


class WorkspacesResource(_Resource):
    """``/workspaces``: the workspaces the key can reach. Scope ``workspaces:read``."""

    def list(self) -> WorkspaceList:
        """``GET /workspaces``."""
        return self._get("/workspaces")

    def get(self, public_id: str) -> WorkspaceResponse:
        """``GET /workspaces/{public_id}``: one active workspace under ``data``."""
        return self._get(path("workspaces", public_id))


class TagsResource(_Resource):
    """A workspace's tags. Scopes ``tags:read``, ``tags:write``."""

    def list(
        self,
        workspace_id: str,
        *,
        team_public_ids: IDList | None = None,
        team: str | None = None,
        report_scope: bool | None = None,
    ) -> TagList:
        """``GET /workspaces/{workspace_id}/tags``, sorted by name. ``team="none"`` lists workspace-wide tags only."""
        query = {"team_public_ids": team_public_ids, "team": team, "report_scope": report_scope}
        return self._get(path("workspaces", workspace_id, "tags"), query)

    def create(
        self,
        workspace_id: str,
        *,
        name: str,
        color: str,
        team_public_ids: List[str] | None = None,
    ) -> Tag:
        """``POST /workspaces/{workspace_id}/tags``."""
        body = {"name": name, "color": color, "team_public_ids": team_public_ids}
        return self._post(path("workspaces", workspace_id, "tags"), body)

    def get(self, tag_id: str) -> Tag:
        """``GET /tags/{tag_id}``."""
        return self._get(path("tags", tag_id))

    def update(self, tag_id: str, **params: Unpack[TagUpdateParams]) -> Tag:
        """``PUT /tags/{tag_id}``: change ``name``/``color``, or replace ``team_public_ids`` (not both at once)."""
        return self._put(path("tags", tag_id), params)

    def delete(self, tag_id: str) -> TagDeleteResponse:
        """``DELETE /tags/{tag_id}``: also removes the tag from its links."""
        return self._delete(path("tags", tag_id))


class UTMTemplatesResource(_Resource):
    """A workspace's UTM templates. Scopes ``utm-templates:read``, ``utm-templates:write``."""

    def list(
        self,
        workspace_id: str,
        *,
        include_team_scoped: bool | None = None,
        team_public_ids: IDList | None = None,
    ) -> UTMTemplateList:
        """``GET /workspaces/{workspace_id}/utm-templates``: workspace-wide templates unless asked for more."""
        query = {"include_team_scoped": include_team_scoped, "team_public_ids": team_public_ids}
        return self._get(path("workspaces", workspace_id, "utm-templates"), query)

    def create(self, workspace_id: str, **params: Unpack[UTMTemplateParams]) -> UTMTemplateResponse:
        """``POST /workspaces/{workspace_id}/utm-templates``."""
        return self._post(path("workspaces", workspace_id, "utm-templates"), params)

    def update(self, template_id: str, **params: Unpack[UTMTemplateUpdateParams]) -> UTMTemplateResponse:
        """``PUT /utm-templates/{template_id}``: replaces the template; pass every value to keep."""
        return self._put(path("utm-templates", template_id), params)

    def delete(self, template_id: str, *, links: str | None = None) -> UTMTemplateDeleteResponse:
        """``DELETE /utm-templates/{template_id}``. ``links`` is ``"keep"`` (the API's default) or ``"clear"``."""
        return self._delete(path("utm-templates", template_id), {"links": links})


class DestinationsResource(_Resource):
    """Where a workspace's reports and alerts are sent. Scopes ``destinations:read``, ``destinations:write``."""

    def list(self, workspace_id: str) -> List[Destination]:
        """``GET /workspaces/{workspace_id}/destinations``: a JSON array."""
        return self._get(path("workspaces", workspace_id, "destinations"))

    def create(
        self,
        workspace_id: str,
        *,
        name: str,
        type: DestinationType | str,
        config: Mapping[str, Any],
        team_public_ids: List[str] | None = None,
    ) -> Destination:
        """``POST /workspaces/{workspace_id}/destinations``.

        ``config`` is ``{"to": [...]}`` for ``email`` and ``{"webhook_url": "https://..."}`` for the others.
        """
        body = {"name": name, "type": type, "config": config, "team_public_ids": team_public_ids}
        return self._post(path("workspaces", workspace_id, "destinations"), body)

    def update(
        self,
        workspace_id: str,
        destination_id: str,
        *,
        name: str,
        type: DestinationType | str,
        config: Mapping[str, Any] | None = None,
        team_public_ids: List[str] | None = None,
    ) -> SuccessResponse:
        """``PUT /workspaces/{workspace_id}/destinations/{destination_id}``: ``name`` and ``type`` are required."""
        body = {"name": name, "type": type, "config": config, "team_public_ids": team_public_ids}
        return self._put(path("workspaces", workspace_id, "destinations", destination_id), body)

    def delete(self, workspace_id: str, destination_id: str) -> SuccessResponse:
        """``DELETE /workspaces/{workspace_id}/destinations/{destination_id}``."""
        return self._delete(path("workspaces", workspace_id, "destinations", destination_id))


class TeamsResource(_Resource):
    """A workspace's teams. Scopes ``teams:read``, ``teams:write``.

    A team is read, changed and archived by its ``slug``. When the key reaches several
    workspaces with the same slug, pass ``workspace`` (a workspace public ID).
    """

    def list(self, workspace_id: str) -> TeamList:
        """``GET /workspaces/{workspace_id}/teams``: active teams, newest first."""
        return self._get(path("workspaces", workspace_id, "teams"))

    def create(self, workspace_id: str, *, name: str, description: str | None = None) -> CreatedTeam:
        """``POST /workspaces/{workspace_id}/teams``: answers ``id``, ``slug`` and ``public_id``."""
        return self._post(path("workspaces", workspace_id, "teams"), {"name": name, "description": description})

    def get(self, slug: str, *, workspace: str | None = None) -> Team:
        """``GET /teams/{slug}``."""
        return self._get(path("teams", slug), {"workspace": workspace})

    def update(
        self,
        slug: str,
        *,
        name: str | None = None,
        description: str | None = None,
        workspace: str | None = None,
    ) -> Team:
        """``PUT /teams/{slug}``: rename or describe the team. The slug stays."""
        route = path("teams", slug)
        return self._client.request(
            "PUT", route, query={"workspace": workspace}, body={"name": name, "description": description}
        )

    def delete(self, slug: str, *, workspace: str | None = None) -> SuccessResponse:
        """``DELETE /teams/{slug}``: archive the team. Refused while resources are still assigned to it."""
        return self._delete(path("teams", slug), {"workspace": workspace})


class DomainsResource(_Resource):
    """Custom domains, by numeric ``id``. Scopes ``domains:read``, ``domains:write`` (account-wide key)."""

    def list(self) -> DomainList:
        """``GET /domains``."""
        return self._get("/domains")

    def create(self, *, domain: str) -> DomainResponse:
        """``POST /domains``: add a domain, then create its DNS records and :meth:`verify` it."""
        return self._post("/domains", {"domain": domain})

    def verify(self, domain_id: Union[int, str]) -> DomainVerifyResponse:
        """``POST /domains/{domain_id}/verify``: check the DNS records now."""
        return self._post(path("domains", domain_id, "verify"))

    def delete(self, domain_id: Union[int, str]) -> DomainDeleteResponse:
        """``DELETE /domains/{domain_id}``: only the owner, and only once no link uses it."""
        return self._delete(path("domains", domain_id))


class ReportsResource(_Resource):
    """Scheduled report and alert rules. Scopes ``reports:read``, ``reports:write``."""

    def list_rules(
        self,
        *,
        workspace_public_id: str | None = None,
        schedule_types: IDList | None = None,
        link_public_ids: IDList | None = None,
        team_public_ids: IDList | None = None,
    ) -> ReportRuleList:
        """``GET /reports/rules``. ``schedule_types`` takes ``"every_x"`` (reports) and ``"event"`` (alerts)."""
        query = {
            "workspace_public_id": workspace_public_id,
            "schedule_types": schedule_types,
            "link_public_ids": link_public_ids,
            "team_public_ids": team_public_ids,
        }
        return self._get("/reports/rules", query)

    def get_rule(self, rule_id: str) -> ReportRuleResponse:
        """``GET /reports/rules/{rule_id}``: the rule under ``data``, with its ``definition``."""
        return self._get(path("reports", "rules", rule_id))

    def create_rule(self, **params: Unpack[ReportRuleParams]) -> ReportRuleResponse:
        """``POST /reports/rules``. Needs ``report_type`` (``"custom_builder_v1"``) and ``definition_json``."""
        return self._post("/reports/rules", params)

    def update_rule(self, rule_id: str, **params: Unpack[ReportRuleParams]) -> ReportRuleResponse:
        """``PATCH /reports/rules/{rule_id}``: change what you pass, such as ``enabled=False``."""
        return self._patch(path("reports", "rules", rule_id), params)

    def delete_rule(self, rule_id: str) -> None:
        """``DELETE /reports/rules/{rule_id}``: answers ``204`` with no body."""
        self._delete(path("reports", "rules", rule_id))


class ConversionsResource(_Resource):
    """Leads, sales and refunds, and conversion reporting. Scopes ``conversions:write``, ``conversions:read``.

    Writes carrying an ``idempotency_key`` are retried on network errors, ``429`` and ``503``;
    writes without one are sent once. Writes with ``test_mode=True`` are always sent once:
    the API doesn't deduplicate test events.
    """

    def track_lead(self, *, click_id: str, idempotency_key: str, **params: Unpack[LeadParams]) -> ConversionResult:
        """``POST /conversions/leads``: record a lead."""
        return self._post("/conversions/leads", _lead_body(click_id, idempotency_key, params))

    def validate_lead(self, *, click_id: str, idempotency_key: str, **params: Unpack[LeadParams]) -> ConversionValidation:
        """``POST /conversions/leads/validations``: run the lead checks without recording anything."""
        return self._post("/conversions/leads/validations", _lead_body(click_id, idempotency_key, params))

    def track_sale(self, *, click_id: str, currency: str, **params: Unpack[SaleParams]) -> ConversionResult:
        """``POST /conversions/sales``: record a sale. Send ``invoice_id`` or ``idempotency_key``."""
        return self._post("/conversions/sales", {"click_id": click_id, "currency": currency, **params})

    def validate_sale(self, *, click_id: str, currency: str, **params: Unpack[SaleParams]) -> ConversionValidation:
        """``POST /conversions/sales/validations``: run the sale checks without recording anything."""
        return self._post("/conversions/sales/validations", {"click_id": click_id, "currency": currency, **params})

    def track_refund(self, *, invoice_id: str, refund_id: str, **params: Unpack[RefundParams]) -> ConversionResult:
        """``POST /conversions/refunds``: refund (part of) the sale named by ``invoice_id``."""
        return self._post("/conversions/refunds", {"invoice_id": invoice_id, "refund_id": refund_id, **params})

    def validate_refund(
        self, *, invoice_id: str, refund_id: str, **params: Unpack[RefundParams]
    ) -> ConversionValidation:
        """``POST /conversions/refunds/validations``: run the refund checks without recording anything."""
        body = {"invoice_id": invoice_id, "refund_id": refund_id, **params}
        return self._post("/conversions/refunds/validations", body)

    def summary(self, **query: Any) -> ConversionSummary:
        """``GET /conversions/summary``: all-time live totals under ``data``."""
        return self._get("/conversions/summary", query)

    def attribution(
        self,
        *,
        from_: DateArg | None = None,
        to: DateArg | None = None,
        environment: Environment | None = None,
        limit: int | None = None,
    ) -> ConversionReport:
        """``GET /conversions/attribution``: one row per attribution target. ``from_`` is sent as ``from``."""
        query = {"from": from_, "to": to, "environment": environment, "limit": limit}
        return self._get("/conversions/attribution", query)

    def timeline(
        self,
        *,
        from_: DateArg | None = None,
        to: DateArg | None = None,
        environment: Environment | None = None,
        interval: str | None = None,
    ) -> ConversionReport:
        """``GET /conversions/timeline``: one point per ``interval`` (``day``, ``week`` or ``month``)."""
        query = {"from": from_, "to": to, "environment": environment, "interval": interval}
        return self._get("/conversions/timeline", query)

    def events(
        self,
        *,
        from_: DateArg | None = None,
        to: DateArg | None = None,
        environment: Environment | None = None,
        limit: int | None = None,
        offset: int | None = None,
        event_type: str | None = None,
        lead_category: str | None = None,
        event_origin: str | None = None,
        link: str | None = None,
        event: str | None = None,
        q: str | None = None,
        include_total: bool | None = None,
    ) -> ConversionEventList:
        """``GET /conversions/events``: events, newest first, with ``pagination``."""
        query = {
            "from": from_,
            "to": to,
            "environment": environment,
            "limit": limit,
            "offset": offset,
            "event_type": event_type,
            "lead_category": lead_category,
            "event_origin": event_origin,
            "link": link,
            "event": event,
            "q": q,
            "include_total": include_total,
        }
        return self._get("/conversions/events", query)


def _lead_body(click_id: str, idempotency_key: str, params: Mapping[str, Any]) -> Dict[str, Any]:
    return {"click_id": click_id, "idempotency_key": idempotency_key, **params}


_SNAKE = re.compile(r"_([a-z])")


def _camel(name: str) -> str:
    return _SNAKE.sub(lambda match: match.group(1).upper(), name)


class PublicResource(_Resource):
    """Endpoints that need no API key. A client without a key can call these."""

    def validate_url(self, url: str) -> URLValidation:
        """``GET /validate``: whether ``url`` can be a destination, and its normalized form."""
        return self._client.request("GET", "/validate", query={"url": url}, auth=False)

    def qr_code(
        self,
        *,
        url: str,
        format: str | None = None,
        size: str | None = None,
        **options: Optional[Union[str, bool, Sequence[str]]],
    ) -> bytes:
        """``GET /qr``: the QR code image for ``url``, as bytes (PNG unless ``format`` says ``svg`` or ``jpg``).

        Other options take snake_case or the API's camelCase names: ``color_mode`` or
        ``colorMode``, ``fg``, ``bg``, ``qr_shape``, ``finder_shape``, ``frame_template``, ...
        """
        query: Dict[str, Any] = {"url": url, "format": format, "size": size}
        for name, value in options.items():
            # The QR endpoint reads booleans as "true"/"false", not "1"/"0".
            query[_camel(name)] = ("true" if value else "false") if isinstance(value, bool) else value
        accept = "image/svg+xml" if format == "svg" else "image/*"
        return self._client.request("GET", "/qr", query=query, auth=False, accept=accept, raw=True)

    def plans(self) -> PlanCatalog:
        """``GET /plans``: the plan catalog under ``plans``, keyed by plan ID (capitalized fields)."""
        return self._client.request("GET", "/plans", auth=False)


__all__ = [
    "AnalyticsResource",
    "ConversionsResource",
    "DestinationsResource",
    "DomainsResource",
    "LinksResource",
    "PublicResource",
    "ReportsResource",
    "TagsResource",
    "TeamsResource",
    "UTMTemplatesResource",
    "WorkspacesResource",
]
