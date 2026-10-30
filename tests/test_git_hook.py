"""
Unit tests for Git Hook & GitHub Action installers.
"""

import os
import subprocess
import tempfile
import unittest
from codereview.hooks.git_hook import install_git_hook, uninstall_git_hook
from codereview.hooks.github_action import install_github_action_workflow


class TestGitHooks(unittest.TestCase):

    def test_git_hook_lifecycle_in_repo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize clean git repository in temp directory
            subprocess.run(["git", "init", tmpdir], capture_output=True, check=True)

            ok, msg = install_git_hook(tmpdir)
            self.assertTrue(ok, f"Failed to install git hook: {msg}")
            hook_path = os.path.join(tmpdir, ".git", "hooks", "pre-commit")
            self.assertTrue(os.path.exists(hook_path))

            with open(hook_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("Automated Code Reviewer", content)
            self.assertIn("review", content)

            ok_un, msg_un = uninstall_git_hook(tmpdir)
            self.assertTrue(ok_un, f"Failed to uninstall: {msg_un}")
            self.assertFalse(os.path.exists(hook_path))

    def test_github_action_installer(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ok, msg = install_github_action_workflow(tmpdir)
            self.assertTrue(ok)
            wf_path = os.path.join(tmpdir, ".github", "workflows", "code_review.yml")
            self.assertTrue(os.path.exists(wf_path))
            with open(wf_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("code-review", content)
            self.assertIn("GITHUB_STEP_SUMMARY", content)


if __name__ == "__main__":
    unittest.main()
