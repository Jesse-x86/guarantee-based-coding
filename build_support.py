"""Copy the canonical offline manual into built packages, never the source tree."""
from pathlib import Path

from setuptools.command.build_py import build_py


MANUAL_LANGUAGES = ("en", "zh")
MANUAL_TOPICS = ("quick-start", "concepts", "workflow", "reference", "onboarding-agent")


class BuildPy(build_py):
    """Include the fixed manual topics when building directly or from an sdist."""

    def _manual_files(self):
        root = Path(__file__).resolve().parent
        for language in MANUAL_LANGUAGES:
            for topic in MANUAL_TOPICS:
                relative = Path(language) / f"{topic}.md"
                yield root / "docs" / relative, Path(self.build_lib) / "gbc/assets/docs" / relative

    def run(self):
        super().run()
        for source, destination in self._manual_files():
            self.mkpath(str(destination.parent))
            self.copy_file(str(source), str(destination))

    def get_outputs(self, include_bytecode=True):
        outputs = super().get_outputs(include_bytecode=include_bytecode)
        return outputs + [str(destination) for _, destination in self._manual_files()]
