from setuptools import setup, find_packages
import re
from pathlib import Path

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


def read_version() -> str:
    """Extract __version__ from the package __init__.py without importing it."""
    init_path = Path(__file__).parent / "notion_markdown_converter" / "__init__.py"
    content = init_path.read_text(encoding="utf-8")
    match = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", content)
    if not match:
        raise RuntimeError("Unable to find __version__ in notion_markdown_converter/__init__.py")
    return match.group(1)

setup(
    name="notion-markdown-converter",
    version=read_version(),
    author="Your Name",
    author_email="your.email@example.com",
    description="A bidirectional converter between Notion API JSON format and Markdown",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/notion_md_converter",
    packages=find_packages(exclude=("tests", "examples", "references")),
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup",
    ],
    python_requires=">=3.7",
    install_requires=[
        "notion-client>=2.0.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "notion-fetch=notion_markdown_converter.cli:fetch_page_main",
            "notion-upload=notion_markdown_converter.cli:upload_page_main",
        ]
    },
)