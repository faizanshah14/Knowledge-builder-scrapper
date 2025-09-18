from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="knowledge-builder",
    version="1.0.0",
    author="Faizan Shah",
    author_email="faizanshah1496@gmail.com",
    description="A powerful web scraper and knowledge base system with AI-powered Q&A",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/faizanshah14/Knowledge-builder-scrapper",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Markup :: HTML",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "knowledge-builder=scrapper.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
