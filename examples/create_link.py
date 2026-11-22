"""Create a tagged link in a workspace, read it back and print its clicks.

    SHORTN_API_KEY=sk_live_... SHORTN_WORKSPACE=<workspace public id> python examples/create_link.py
"""

import os

from shortn_sdk import Shortn


def main() -> None:
    shortn = Shortn(os.environ["SHORTN_API_KEY"])
    workspace_id = os.environ["SHORTN_WORKSPACE"]

    tags = shortn.tags.list(workspace_id)["tags"] or []
    spring = next((tag for tag in tags if tag["name"] == "Spring"), None)
    if spring is None:
        spring = shortn.tags.create(workspace_id, name="Spring", color="#14b8a6")

    link = shortn.links.create(
        url="https://example.com/pricing",
        title="Pricing",
        workspace_public_id=workspace_id,
        tag_public_ids=[spring["public_id"]],
        utm_source="newsletter",
        utm_medium="email",
        utm_campaign="spring_launch",
    )
    print(link["short_url"], link["link_status"])

    details = shortn.links.get(link["public_id"])["data"]
    totals = shortn.analytics.link(link["public_id"])
    print(details["title"], totals["total_clicks"], "clicks")


if __name__ == "__main__":
    main()
