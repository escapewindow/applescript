from setuptools import setup

setup(
    name="signingscript",
    version="0.1.0",
    description="TaskCluster Signing Script",
    author="Mozilla Release Engineering",
    author_email="release+python@mozilla.com",
    url="https://github.com/escapewindow/signingscript",
    packages=["signingscript"],
    package_data={"signingscript": ["data/*.json"]},
    include_package_data=True,
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "signingscript = signingscript.script:main",
        ],
    },
    license="MPL2",
    install_requires=[
        "arrow",
        "jsonschema",
        "python-jose",
        "taskcluster",
    ],
)
