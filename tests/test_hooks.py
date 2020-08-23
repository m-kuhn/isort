import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from isort import exceptions, hooks


def test_git_hook(src_dir):
    """Simple smoke level testing of git hooks"""

    # Ensure correct subprocess command is called
    with patch("subprocess.run", MagicMock()) as run_mock:
        hooks.git_hook()
        assert run_mock.called_once()
        assert run_mock.call_args[0][0] == [
            "git",
            "diff-index",
            "--cached",
            "--name-only",
            "--diff-filter=ACMRTUXB",
            "HEAD",
        ]

        hooks.git_hook(lazy=True)
        assert run_mock.called_once()
        assert run_mock.call_args[0][0] == [
            "git",
            "diff-index",
            "--name-only",
            "--diff-filter=ACMRTUXB",
            "HEAD",
        ]

    # Test with incorrectly sorted file returned from git
    with patch(
        "isort.hooks.get_lines", MagicMock(return_value=[os.path.join(src_dir, "main.py")])
    ) as run_mock:

        class FakeProcessResponse(object):
            stdout = b"import b\nimport a"

        with patch("subprocess.run", MagicMock(return_value=FakeProcessResponse())) as run_mock:
            with patch("isort.api", MagicMock(return_value=False)):
                hooks.git_hook(modify=True)

    # Test with skipped file returned from git
    with patch(
        "isort.hooks.get_lines", MagicMock(return_value=[os.path.join(src_dir, "main.py")])
    ) as run_mock:

        class FakeProcessResponse(object):
            stdout = b"# isort: skip-file\nimport b\nimport a\n"

        with patch("subprocess.run", MagicMock(return_value=FakeProcessResponse())) as run_mock:
            with patch("isort.api", MagicMock(side_effect=exceptions.FileSkipped("", ""))):
                hooks.git_hook(modify=True)


def test_git_hook_uses_the_configuration_file_specified_in_settings_path(tmp_path: Path) -> None:
    subdirectory_path = tmp_path / "subdirectory"
    configuration_file_path = subdirectory_path / ".isort.cfg"

    # Inserting the modified file in the parent directory of the configuration file ensures that it
    # will not be found by the normal search routine
    modified_file_path = configuration_file_path.parent.parent / "somefile.py"

    # This section will be used to check that the configuration file was indeed loaded
    section = "testsection"

    os.mkdir(subdirectory_path)
    with open(configuration_file_path, "w") as fd:
        fd.write("[isort]\n")
        fd.write(f"sections={section}")

    with open(modified_file_path, "w") as fd:
        pass

    files_modified = [str(modified_file_path.absolute())]
    with patch("isort.hooks.get_lines", MagicMock(return_value=files_modified)):
        with patch("isort.hooks.get_output", MagicMock(return_value="")):
            with patch("isort.api.check_code_string", MagicMock()) as run_mock:
                hooks.git_hook(settings_file=str(configuration_file_path))

                assert run_mock.call_args[1]["config"].sections == (section,)
