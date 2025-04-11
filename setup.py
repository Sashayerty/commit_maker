from setuptools import find_packages, setup

setup(
    name="commit_maker",
    version="0.1.2",
    author="Alex Bulgakov",
    author_email="sashayerty@ya.ru",
    description="CLI-утилита для генерации git-коммитов с помощью ИИ",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    license="MIT",
    python_requires=">=3.8",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "commit_maker=commit_maker.main:main",
        ],
    },
    install_requires=[],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
