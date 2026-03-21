"""CLI commands for Jira integration."""


import click

from agentix.core.auth import resolve_auth
from agentix.core.exceptions import AgentixError
from agentix.jira.client import JiraClient
from agentix.jira.models import (
    normalize_attachment,
    normalize_board,
    normalize_comment,
    normalize_issue,
    normalize_issue_brief,
    normalize_project,
    normalize_sprint,
    normalize_transition,
)


def _get_client(ctx: click.Context) -> JiraClient:
    auth = resolve_auth(
        "jira",
        ctx.obj["config_manager"],
        profile_name=ctx.obj["profile"],
    )
    return JiraClient(auth.base_url, auth.user, auth.token, auth.auth_type)


@click.group("jira")
def jira_group():
    """Jira issue tracking."""
    pass


# -- Issue commands --


@jira_group.group("issue")
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
    ctx.obj["formatter"].output(normalize_issue(issue))


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
    ctx.obj["formatter"].output(issues)


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
    ctx.obj["formatter"].success(
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
        ctx.obj["formatter"].error(AgentixError("No fields to update."))
        ctx.exit(3)
        return

    client = _get_client(ctx)
    client.update_issue(issue_key, fields)
    ctx.obj["formatter"].success(f"Updated issue {issue_key}")


@issue_group.command("assign")
@click.argument("issue_key")
@click.argument("assignee")
@click.pass_context
def issue_assign(ctx, issue_key, assignee):
    """Assign an issue."""
    client = _get_client(ctx)
    client.assign_issue(issue_key, assignee)
    ctx.obj["formatter"].success(f"Assigned {issue_key} to {assignee}")


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
        ctx.obj["formatter"].output(normalized)
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
        ctx.obj["formatter"].error(
            AgentixError(f"No transition matching '{status}'. Available: {available}")
        )
        ctx.exit(3)
        return

    client.transition_issue(issue_key, match["id"], comment=comment)
    ctx.obj["formatter"].success(
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
    ctx.obj["formatter"].success(f"Deleted issue {issue_key}")


# -- Comment commands --


@jira_group.group("comment")
def comment_group():
    """Manage issue comments."""
    pass


@comment_group.command("list")
@click.argument("issue_key")
@click.pass_context
def comment_list(ctx, issue_key):
    """List comments on an issue."""
    client = _get_client(ctx)
    comments = client.get_comments(issue_key)
    ctx.obj["formatter"].output([normalize_comment(c) for c in comments])


@comment_group.command("add")
@click.argument("issue_key")
@click.option("--body", "-b", required=True, help="Comment text.")
@click.pass_context
def comment_add(ctx, issue_key, body):
    """Add a comment to an issue."""
    client = _get_client(ctx)
    result = client.add_comment(issue_key, body)
    ctx.obj["formatter"].success(
        f"Added comment to {issue_key}",
        data={"id": result.get("id")},
    )


@comment_group.command("get")
@click.argument("issue_key")
@click.argument("comment_id")
@click.pass_context
def comment_get(ctx, issue_key, comment_id):
    """Get a specific comment."""
    client = _get_client(ctx)
    comment = client.get_comment(issue_key, comment_id)
    ctx.obj["formatter"].output(normalize_comment(comment))


# -- Attachment commands --


@jira_group.group("attachment")
def attachment_group():
    """Manage issue attachments."""
    pass


@attachment_group.command("list")
@click.argument("issue_key")
@click.pass_context
def attachment_list(ctx, issue_key):
    """List attachments on an issue."""
    client = _get_client(ctx)
    attachments = client.get_attachments(issue_key)
    ctx.obj["formatter"].output([normalize_attachment(a) for a in attachments])


@attachment_group.command("add")
@click.argument("issue_key")
@click.argument("file_path", type=click.Path(exists=True))
@click.pass_context
def attachment_add(ctx, issue_key, file_path):
    """Add an attachment to an issue."""
    client = _get_client(ctx)
    result = client.add_attachment(issue_key, file_path)
    ctx.obj["formatter"].success(
        f"Added attachment to {issue_key}",
        data={"attachments": result},
    )


@attachment_group.command("get")
@click.argument("attachment_id")
@click.option("--output", "-o", "output_path", help="Output file path.")
@click.pass_context
def attachment_get(ctx, attachment_id, output_path):
    """Download an attachment."""
    client = _get_client(ctx)
    content = client.get_attachment_content(attachment_id)
    if output_path:
        with open(output_path, "wb") as f:
            f.write(content)
        ctx.obj["formatter"].success(f"Saved attachment to {output_path}")
    else:
        import sys
        sys.stdout.buffer.write(content)


# -- Sprint commands --


@jira_group.group("sprint")
def sprint_group():
    """Manage sprints."""
    pass


@sprint_group.command("list")
@click.option("--board", "-b", required=True, type=int, help="Board ID.")
@click.option("--state", type=click.Choice(["active", "closed", "future"]), help="Sprint state filter.")
@click.pass_context
def sprint_list(ctx, board, state):
    """List sprints for a board."""
    client = _get_client(ctx)
    sprints = client.get_sprints(board, state=state)
    ctx.obj["formatter"].output([normalize_sprint(s) for s in sprints])


@sprint_group.command("get")
@click.argument("sprint_id", type=int)
@click.pass_context
def sprint_get(ctx, sprint_id):
    """Get sprint details."""
    client = _get_client(ctx)
    sprint = client.get_sprint(sprint_id)
    ctx.obj["formatter"].output(normalize_sprint(sprint))


@sprint_group.command("issues")
@click.argument("sprint_id", type=int)
@click.option("--max-results", default=50, type=int, help="Max results.")
@click.pass_context
def sprint_issues(ctx, sprint_id, max_results):
    """List issues in a sprint."""
    client = _get_client(ctx)
    issues = client.get_sprint_issues(sprint_id, max_results=max_results)
    ctx.obj["formatter"].output([normalize_issue_brief(i) for i in issues])


@sprint_group.command("active")
@click.option("--board", "-b", required=True, type=int, help="Board ID.")
@click.pass_context
def sprint_active(ctx, board):
    """Get the active sprint for a board."""
    client = _get_client(ctx)
    sprint = client.get_active_sprint(board)
    if sprint:
        ctx.obj["formatter"].output(normalize_sprint(sprint))
    else:
        ctx.obj["formatter"].output({"message": "No active sprint found."})


# -- Epic commands --


@jira_group.group("epic")
def epic_group():
    """Manage epics."""
    pass


@epic_group.command("list")
@click.option("--project", "-p", help="Project key.")
@click.pass_context
def epic_list(ctx, project):
    """List epics."""
    client = _get_client(ctx)
    epics = client.get_epics(project)
    ctx.obj["formatter"].output([normalize_issue_brief(e) for e in epics])


@epic_group.command("get")
@click.argument("epic_key")
@click.pass_context
def epic_get(ctx, epic_key):
    """Get epic details."""
    client = _get_client(ctx)
    epic = client.get_issue(epic_key)
    ctx.obj["formatter"].output(normalize_issue(epic))


@epic_group.command("issues")
@click.argument("epic_key")
@click.option("--max-results", default=50, type=int, help="Max results.")
@click.pass_context
def epic_issues(ctx, epic_key, max_results):
    """List issues in an epic."""
    client = _get_client(ctx)
    issues = client.get_epic_issues(epic_key, max_results=max_results)
    ctx.obj["formatter"].output([normalize_issue_brief(i) for i in issues])


# -- Board commands --


@jira_group.group("board")
def board_group():
    """Manage boards."""
    pass


@board_group.command("list")
@click.option("--project", "-p", help="Project key.")
@click.pass_context
def board_list(ctx, project):
    """List boards."""
    client = _get_client(ctx)
    boards = client.get_boards(project)
    ctx.obj["formatter"].output([normalize_board(b) for b in boards])


@board_group.command("get")
@click.argument("board_id", type=int)
@click.pass_context
def board_get(ctx, board_id):
    """Get board details."""
    client = _get_client(ctx)
    board = client.get_board(board_id)
    ctx.obj["formatter"].output(normalize_board(board))


# -- Project commands --


@jira_group.group("project")
def project_group():
    """Manage projects."""
    pass


@project_group.command("list")
@click.pass_context
def project_list(ctx):
    """List projects."""
    client = _get_client(ctx)
    projects = client.get_projects()
    ctx.obj["formatter"].output([normalize_project(p) for p in projects])


@project_group.command("get")
@click.argument("project_key")
@click.pass_context
def project_get(ctx, project_key):
    """Get project details."""
    client = _get_client(ctx)
    project = client.get_project(project_key)
    ctx.obj["formatter"].output(normalize_project(project))


# -- Search --


@jira_group.command("search")
@click.argument("jql")
@click.option("--max-results", default=50, type=int, help="Max results (default: 50).")
@click.option("--fields", help="Comma-separated field names.")
@click.pass_context
def jira_search(ctx, jql, max_results, fields):
    """Search issues with JQL."""
    client = _get_client(ctx)
    field_list = [f.strip() for f in fields.split(",")] if fields else None
    result = client.search_issues(jql, fields=field_list, max_results=max_results)
    issues = [normalize_issue_brief(i) for i in result.get("issues", [])]
    ctx.obj["formatter"].output(issues)
