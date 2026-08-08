"""The CI must run on GitHub's runners and nowhere else.

This repository is public and its workflows are triggered by pull requests,
including from forks. A self-hosted runner would execute that code on the
owner's own machine, with whatever credentials the runner's user carries -- the
Puppet fleet's own agent runners are deliberately restricted for exactly this
reason. Nothing here needs that, and nothing here should acquire it quietly.
"""
import glob
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOWS = sorted(glob.glob(os.path.join(REPO, ".github", "workflows", "*.y*ml")))

# GitHub-hosted images. A label that is not one of these is either self-hosted
# or a group, and both mean "not GitHub's machines".
HOSTED = re.compile(r"^(ubuntu|windows|macos)-[a-z0-9.]+$")


def jobs_runs_on():
    for path in WORKFLOWS:
        for line_no, line in enumerate(open(path, encoding="utf-8"), 1):
            m = re.match(r"\s*runs-on:\s*(.+?)\s*$", line)
            if m:
                yield os.path.basename(path), line_no, m.group(1)


def test_there_is_at_least_one_workflow_to_check():
    """Otherwise every assertion below passes by having nothing to look at."""
    assert WORKFLOWS, "no workflow files found"
    assert list(jobs_runs_on()), "no runs-on found in any workflow"


def test_every_job_runs_on_a_github_hosted_runner():
    for name, line_no, value in jobs_runs_on():
        assert HOSTED.match(value), (
            f"{name}:{line_no} runs-on: {value!r} is not a GitHub-hosted image")


def test_no_workflow_mentions_a_self_hosted_label():
    """Catches the list form, which the line match above would not read."""
    for path in WORKFLOWS:
        text = open(path, encoding="utf-8").read()
        for label in ("self-hosted", "groniko-agent"):
            assert label not in text, f"{os.path.basename(path)} mentions {label}"


def test_the_guard_rejects_what_it_must():
    """A check nobody has shown a bad value is not a check."""
    for bad in ("self-hosted", "[self-hosted, linux]", "groniko-agent", "my-runner-group"):
        assert not HOSTED.match(bad), f"should be refused: {bad}"
    for good in ("ubuntu-latest", "ubuntu-24.04", "macos-14", "windows-latest"):
        assert HOSTED.match(good), f"should be accepted: {good}"
