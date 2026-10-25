"""All local managers are cleaned up even if a sibling fails; no DB or network."""

from types import SimpleNamespace

import pytest

from app import main


@pytest.mark.parametrize("failure", [None, "start", "shutdown"])
async def test_lifespan_always_releases_local_managers(monkeypatch, failure):
    calls = []

    async def recover():
        calls.append("paper.recover")
        return 0

    def operation(label):
        async def invoke():
            calls.append(label)
            if label == f"market.{failure}":
                raise RuntimeError("fixture failure")

        return invoke

    monkeypatch.setattr(
        main,
        "paper_manager",
        SimpleNamespace(recover_interrupted=recover, shutdown=operation("paper.shutdown")),
    )
    for name, prefix in (("experiment_manager", "experiment"), ("market_update_manager", "market")):
        monkeypatch.setattr(
            main,
            name,
            SimpleNamespace(
                start=operation(f"{prefix}.start"), shutdown=operation(f"{prefix}.shutdown")
            ),
        )

    async def run():
        async with main.lifespan(main.app):
            calls.append("serving")

    if failure:
        with pytest.raises(RuntimeError, match="fixture failure"):
            await run()
    else:
        await run()
    expected = ["experiment.start", "market.start"]
    if failure != "start":
        expected.extend(["paper.recover", "serving"])
    assert calls == [*expected, "paper.shutdown", "market.shutdown", "experiment.shutdown"]


async def test_rejected_second_startup_does_not_interrupt_paper(monkeypatch):
    calls = []

    async def reject_owner():
        calls.append("experiment.start")
        raise RuntimeError("another process owns the exploratory job queue")

    async def operation(label):
        calls.append(label)
        return 0

    monkeypatch.setattr(
        main,
        "paper_manager",
        SimpleNamespace(
            recover_interrupted=lambda: operation("paper.recover"),
            shutdown=lambda: operation("paper.shutdown"),
        ),
    )
    monkeypatch.setattr(
        main,
        "experiment_manager",
        SimpleNamespace(
            start=reject_owner,
            shutdown=lambda: operation("experiment.shutdown"),
        ),
    )
    monkeypatch.setattr(
        main,
        "market_update_manager",
        SimpleNamespace(
            start=lambda: operation("market.start"),
            shutdown=lambda: operation("market.shutdown"),
        ),
    )

    with pytest.raises(RuntimeError, match="another process owns"):
        async with main.lifespan(main.app):
            pass
    assert calls == [
        "experiment.start",
        "paper.shutdown",
        "market.shutdown",
        "experiment.shutdown",
    ]
