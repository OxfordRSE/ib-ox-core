# EBS snapshot lifecycle for glow-deploy

## Problem

`update()` (core.py:1083) reruns the runner bootstrap script in place on a
live instance (`git checkout --force` + `docker compose up --build`) — a real
mutation of a running deployment's data (`glow-postgres`, `odk-postgres` live
on the instance's single root EBS volume). There is no backup taken first.

Separately, `destroy()` (core.py:1144) already leaves the root volume behind
forever (`delete_on_termination = false` in `runner.tf`) as an accidental
safety net — paying full gp3 price indefinitely for a volume nobody can see
or manage from the GUI.

This spec wires EBS snapshots into both paths, and makes them visible and
manageable (list, delete, restore-into-a-new-deployment) from the GUI.

## Non-goals

- Whole-volume "swap the root disk" restore. Restore is data-only: copy
  `glow-postgres`/`odk-postgres` out of a snapshot into a fresh, up-to-date
  instance. (See "Restore semantics" below for why.)
- Automatic retention/expiry (DLM, keep-last-N). Snapshots are cheap
  (used-block pricing) and stay until a human deletes them via the GUI.
- An on-demand "snapshot now" button. Only the two automatic triggers
  (pre-update, pre-destroy) exist in v1.
- Cross-region/cross-account snapshot copy, encryption knobs beyond whatever
  the source volume already uses.

## Tagging & discovery

Deployments in this tool have no database — `list_deployments()` (core.py:935)
discovers them live by querying EC2 for instances tagged `Component=glow-runner`,
keyed by a `Domain` tag. Snapshots follow the same model:

- Every snapshot is tagged `Domain=<domain>`, `Component=glow-runner-snapshot`,
  `Reason=pre-update|pre-destroy`.
- `list_snapshots(region, session, domain=None)` filters
  `describe_snapshots` by these tags. Omitting `domain` returns the global
  list — this is what makes orphaned snapshots (from a since-destroyed
  deployment) still visible: the snapshot carries its own `Domain` tag
  independent of whether that domain has a live instance.
- `runner.tf` gains a `volume_tags` block on the root device so the *volume*
  itself carries `Domain`/`Component` (today only the instance is tagged).
  This lets pre-update snapshot code find "this deployment's volume" by tag
  lookup instead of threading a volume-id through `Config`.

## Restore semantics

Two ways to interpret "restore a snapshot into a new deployment":

1. Swap the whole root volume onto a freshly-provisioned instance.
2. Provision normally (current AMI, current code), then copy just the
   Postgres data directories out of the snapshot.

Chosen: **(2), data-only restore.** Swapping the root volume means the new
deployment also reverts to snapshot-time OS/AMI/code, which fights the point
of provisioning against current `main`/a release tag, and requires detaching
the volume Terraform just attached (fighting Terraform's model of that
resource). Data-only keeps app code current and only restores the state that
actually needed backing up.

Mechanism: create a volume from the snapshot in the new instance's AZ, attach
it as a secondary device via SSM, run a script that stops the compose stack,
rsyncs `glow-postgres`/`odk-postgres` from the mounted volume over the fresh
instance's data dirs, restarts, then detaches and deletes the temporary
volume.

## core.py additions

Following the existing `_client(session, "ec2", region)` convention:

- `find_root_volume_id(instance_id, region, session) -> str` — via
  `describe_instances`, used while the instance is still running/attached
  (both hook points below need this before the volume becomes hard to find).
- `create_snapshot(volume_id, domain, reason, region, session) -> str` —
  tags per above, `write_line`-logs progress into the calling job's output
  stream.
- `list_snapshots(region, session, domain=None) -> list[dict]` — id, domain,
  reason, created-at, size, state.
- `delete_snapshot(snapshot_id, region, session)`.
- `restore_snapshot_data(instance_id, snapshot_id, region, session)` — the
  restore mechanism described above.

## Hook points

**`update()`** (core.py:1083): after `wait_for_ssm_online`, before
`rerun_runner_userdata`, call `find_root_volume_id` +
`create_snapshot(reason="pre-update")`. Logged via `write_line` into the same
progress stream the update job already tails (the CloudWatch-log-tailing
`on_tick` mechanism added to `rerun_runner_userdata`).

**`destroy()`** (core.py:1144): capture `instance_id` (and from it,
`volume_id` via `find_root_volume_id`) *before* running `terraform destroy` —
Terraform state disappears once destroy completes. Run `terraform destroy` as
today (instance terminates; volume persists — `delete_on_termination=false`
is unchanged). Then snapshot the now-detached, no-longer-written-to volume
(`reason="pre-destroy"`) and `delete_volume` it. Net effect versus today: the
same safety net, but at snapshot pricing instead of paying full volume price
forever, and the result is now visible/manageable in the GUI instead of an
invisible orphaned resource.

## Provisioning integration (restore path)

`/deployments/new` already collects `domain_name`/`git_ref`/etc. and runs
`provision()` as a background job. Add an optional `restore_from_snapshot_id`
form field — a `<select>` populated from the global snapshot list (labelled
by domain + reason + timestamp). `provision()` runs unchanged; if a snapshot
was selected, it calls `restore_snapshot_data()` as a final step, logged into
the same job progress stream. No new job kind — it's a conditional extra step
in the existing `provision()` job.

## GUI

- `deployment_detail.html`: new `<details><summary>Snapshots</summary>` card
  (matches the existing "Update" card pattern) listing this domain's
  snapshots (created, reason, size), each with a `button-danger-ghost`
  delete form (`confirm()`, matching the destroy button's pattern).
  New route: `POST /deployments/{domain}/snapshots/{id}/delete`. The existing
  `GET /deployments/{domain}` route's context gains a `snapshots` key.
- New global page `/snapshots` (linked from `base.html` nav): flat table
  across all domains, including orphans from destroyed deployments, same
  delete action.
- No separate "restore" button on `/snapshots` — the new-deployment form's
  snapshot dropdown is the single restore entry point.
- No on-demand snapshot button in v1.

## Testing

Follow `test_core.py`'s existing pattern (boto3 client mocked via the
`_client` injection point):

- Unit tests for `create_snapshot`/`list_snapshots`/`delete_snapshot`:
  correct tags set, correct filter applied, domain-scoped vs. global listing.
- A test asserting `update()` calls the snapshot hook before
  `rerun_runner_userdata`, and `destroy()` captures the volume id before
  `terraform destroy` and snapshots/deletes after.
- GUI route tests following whichever pattern the existing route tests use
  (to be confirmed during implementation planning).
