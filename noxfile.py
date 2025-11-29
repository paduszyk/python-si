from __future__ import annotations

import functools
import re
import sys
from pathlib import Path

import nox

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[import-not-found]

nox.options.default_venv_backend = "uv"


@functools.cache
def get_python_versions() -> list[str]:
    pyproject_path = Path(__file__).resolve().parent / "pyproject.toml"

    with pyproject_path.open(mode="rb") as pyproject_file:
        pyproject_data = tomllib.load(pyproject_file)

    classifiers = pyproject_data.get("project", {}).get("classifiers", [])

    if not classifiers:
        msg = (
            f"missing 'project.classifiers' in {pyproject_path.name}; "
            f"cannot determine supported Python versions"
        )
        raise RuntimeError(msg)

    python_versions = [
        match.group(1)
        for classifier in classifiers
        if (
            match := re.match(
                r"Programming Language :: Python :: (\d+\.\d+)",
                classifier,
            )
        )
        is not None
    ]

    if not python_versions:
        msg = (
            f"no Python version classifiers found in {pyproject_path.name}; "
            f"expected entries like 'Programming Language :: Python :: 3.x'"
        )
        raise RuntimeError(msg)

    python_versions.sort(key=lambda v: tuple(map(int, v.split("."))))

    return python_versions


@nox.session(python=False)
def uv(session: nox.Session) -> None:
    session.run("uv", "lock", "--check", external=True)


@nox.session(requires=["uv"])
@nox.parametrize(
    "args",
    [
        nox.param(["check"], id="check"),
        nox.param(["format", "--diff"], id="format"),
    ],
)
def ruff(session: nox.Session, args: list[str]) -> None:
    session.run_install(
        "uv",
        "sync",
        "--only-group=ruff",
        "--frozen",
        env={
            "UV_PROJECT_ENVIRONMENT": session.virtualenv.location,
        },
        silent=True,
    )
    session.run("ruff", *args, *session.posargs, ".")


@nox.session(requires=["uv"])
def mypy(session: nox.Session) -> None:
    session.run_install(
        "uv",
        "sync",
        "--group=mypy",
        "--frozen",
        env={
            "UV_PROJECT_ENVIRONMENT": session.virtualenv.location,
        },
        silent=True,
    )
    session.run("mypy", *session.posargs, ".")


@nox.session(requires=["uv"])
@nox.parametrize("python", get_python_versions())
def pytest(session: nox.Session) -> None:
    session.run_install(
        "uv",
        "sync",
        "--group=pytest",
        "--frozen",
        env={
            "UV_PROJECT_ENVIRONMENT": session.virtualenv.location,
        },
        silent=True,
    )
    session.run("pytest", *session.posargs)
