"""Issue commands for Jira."""

from agentix.core.exceptions import AgentixError
from agentix.jira.models import normalize_issue, normalize_issue_brief, normalize_transition
from ._common import _get_client, click, error_exit, output, success


@click.group("issue")
def issue_group():
    """Manage Jira issues."""
    pass


@issue_group.command("get")
@click.argument("issue_key")
@click.pass_context
def issue_get(ctx, issue_key):
    """Get issue details."""
    client = _get_client(ctx)
    issue = client.get_issue(issue_key)
    output(ctx, normalize_issue(issue))


@issue_group.command("list")
@click.option("--project", "-p", help="Project key.")
@click.option("--jql", help="JQL query (overrides other filters).")
@click.option("--assignee", help="Filter by assignee.")
@click.option("--status", help="Filter by status.")
@click.option("--type", "issue_type", help="Filter by issue type.")
@click.option("--max-results", default=50, type=int, help="Max results (default: 50).")
@click.pass_context
def issue_list(ctx, project, jql, assignee, status, issue_type, max_results):
    """List issues."""
    if not jql:
        parts = []
        if project:
            parts.append(f'project = "{project}"')
        if assignee:
            if assignee.lower() == "me":
                parts.append("assignee = currentUser()")
            else:
                parts.append(f'assignee = "{assignee}"')
        if status:
            parts.append(f'status = "{status}"')
        if issue_type:
            parts.append(f'issuetype = "{issue_type}"')
        jql = " AND ".join(parts) if parts else "ORDER BY updated DESC"

    client = _get_client(ctx)
    result = client.search_issues(jql, max_results=max_results)
    issues = [normalize_issue_brief(i) for i in result.get("issues", [])]
    output(ctx, issues)


@issue_group.command("create")
@click.option("--project", "-p", required=True, help="Project key.")
@click.option("--summary", "-s", required=True, help="Issue summary.")
@click.option("--type", "issue_type", default="Task", help="Issue type (default: Task).")
@click.option("--description", "-d", help="Issue description.")
@click.option("--assignee", help="Assignee account ID.")
@click.option("--priority", help="Priority name.")
@click.option("--labels", help="Comma-separated labels.")
@click.pass_context
def issue_create(ctx, project, summary, issue_type, description, assignee, priority, labels):
    """Create an issue."""
    client = _get_client(ctx)
    label_list = [lbl.strip() for lbl in labels.split(",")] if labels else None
    result = client.create_issue(
        project=project,
        summary=summary,
        issue_type=issue_type,
        description=description,
        assignee=assignee,
        priority=priority,
        labels=label_list,
    )
    success(ctx, 
        f"Created issue {result.get('key', '')}",
        data={"key": result.get("key"), "id": result.get("id"), "self": result.get("self")},
    )


@issue_group.command("update")
@click.argument("issue_key")
@click.option("--summary", help="New summary.")
@click.option("--description", help="New description.")
@click.option("--assignee", help="New assignee account ID.")
@click.option("--priority", help="New priority.")
@click.option("--labels", help="Comma-separated labels (replaces existing).")
@click.pass_context
def issue_update(ctx, issue_key, summary, description, assignee, priority, labels):
    """Update an issue."""
    fields = {}
    if summary:
        fields["summary"] = summary
    if description:
        fields["description"] = {
            "type": "doc",
            "version": 1,
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": description}]}
            ],
        }
    if assignee:
        fields["assignee"] = {"accountId": assignee}
    if priority:
        fields["priority"] = {"name": priority}
    if labels:
        fields["labels"] = [lbl.strip() for lbl in labels.split(",")]

    if not fields:
        error_exit(ctx, AgentixError("No fields to update."))
        return

    client = _get_client(ctx)
    client.update_issue(issue_key, fields)
    success(ctx, f"Updated issue {issue_key}")


@issue_group.command("assign")
@click.argument("issue_key")
@click.argument("assignee")
@click.pass_context
def issue_assign(ctx, issue_key, assignee):
    """Assign an issue."""
    client = _get_client(ctx)
    client.assign_issue(issue_key, assignee)
    success(ctx, f"Assigned {issue_key} to {assignee}")


@issue_group.command("transition")
@click.argument("issue_key")
@click.argument("status", required=False)
@click.option("--list", "list_transitions", is_flag=True, help="List available transitions.")
@click.option("--comment", help="Add a comment with the transition.")
@click.pass_context
def issue_transition(ctx, issue_key, status, list_transitions, comment):
    """Transition an issue to a new status."""
    client = _get_client(ctx)
    transitions = client.get_transitions(issue_key)

    if list_transitions or not status:
        normalized = [normalize_transition(t) for t in transitions]
        output(ctx, normalized)
        return

    # Find transition by name (case-insensitive)
    match = None
    for t in transitions:
        if t["name"].lower() == status.lower():
            match = t
            break
        if t.get("to", {}).get("name", "").lower() == status.lower():
            match = t
            break

    if not match:
        available = ", ".join(t["name"] for t in transitions)
        error_exit(
            ctx,
            AgentixError(f"No transition matching '{status}'. Available: {available}"),
        )
        return

    client.transition_issue(issue_key, match["id"], comment=comment)
    success(ctx, 
        f"Transitioned {issue_key} via '{match['name']}'"
    )


@issue_group.command("delete")
@click.argument("issue_key")
@click.option("--yes", is_flag=True, help="Skip confirmation.")
@click.pass_context
def issue_delete(ctx, issue_key, yes):
    """Delete an issue."""
    if not yes:
        click.confirm(f"Delete issue {issue_key}?", abort=True)
    client = _get_client(ctx)
    client.delete_issue(issue_key)
    success(ctx, f"Deleted issue {issue_key}")
