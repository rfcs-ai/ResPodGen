from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="research-podcast",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Convert research papers to podcast-style audio content",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/research-paper-podcast",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "typer>=0.9.0",
        "PyMuPDF>=1.21.0",
        "pydub>=0.25.1",
        "requests>=2.28.0",
        "soundfile>=0.12.1",
        "dataclasses-json>=0.5.7",
    ],
    extras_require={
        "dev": [
            "black>=23.0.0",
            "isort>=5.12.0",
            "pytest>=7.3.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "research-podcast=research_podcast.cli:app",
        ],
    },
)