from benchmark.tasks import TASKS
from opspilot.agent import run_agent
from opspilot.config import MODEL
from opspilot.tools import WORKSPACE

BUDGET_SEED = "Server 1200. Staff 4500. Travel 300."


def reset_workspace() -> None:
    """Every task starts from the same empty workspace."""
    WORKSPACE.mkdir(exist_ok=True)
    for path in WORKSPACE.glob("*"):
        if path.is_file():
            path.unlink()
    (WORKSPACE / "budget.txt").write_text(BUDGET_SEED)


def run_task(task) -> tuple[bool, str, float, int]:
    """Returns (passed, why_not, cost, steps)."""
    reset_workspace()
    try:
        run = run_agent(task["question"], verbose=False, approve_all=True)
    except Exception as e:
        return False, f"agent crashed: {type(e).__name__}: {e}", 0.0, 0

    try:
        if task["check"]():
            return True, "", run.cost_usd, run.steps
        return False, f"check failed (stopped={run.stopped_because})", run.cost_usd, run.steps
    except Exception as e:
        return False, f"check raised {type(e).__name__}: {e}", run.cost_usd, run.steps


def main() -> None:
    passed = 0
    total_cost = 0.0

    for task in TASKS:
        ok, why, cost, steps = run_task(task)
        passed += ok
        total_cost += cost
        print(f"{'PASS' if ok else 'FAIL'}  {task['id']:<18} "
              f"steps={steps:<2} ${cost:.4f}  {why}")

    n = len(TASKS)
    print(f"\n{passed}/{n} passed ({passed / n:.0%})   total ${total_cost:.4f}")


if __name__ == "__main__":
    print(f"model: {MODEL}\n")
    main()
