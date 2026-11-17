# Extending Smart Data Inspector

The project uses plain functions and explicit registration. There is no plugin discovery, base class, or hidden global state. A profiler/check receives data and configuration, returns a shared dataclass or simple structured result, and never writes files or mutates the input. A quality check returns `list[Finding]`; a chart writes exactly one PNG and returns `Path | None`.

## Naming and layout

Use a **module** for one cohesive analysis, for example `smart_data_inspector/profiling/text.py` with `tests/unit/profiling/test_text.py`. Use a **folder** only when a broad category has independent implementations: `visualizations/` holds one module per chart type; existing `quality/<check>/checks.py` folders are retained for backward-compatible earlier checks. New broad quality families should use `quality/<category>/` and `tests/unit/quality/<category>/`.

Keep names lowercase with underscores. Unit tests use deterministic, small DataFrames and stay beside their functional category. Integration/CLI tests belong in `tests/integration/`.

An existing small module such as `profiling/text.py` (with `tests/unit/profiling/test_text.py`) is a good starting point to copy. Run one test file with:

```sh
make test ARGS=tests/unit/profiling/test_my_measure.py
```

## Add one profiling module

1. Create `smart_data_inspector/profiling/example.py`.
2. Use a pure function accepting a `pd.DataFrame` or `pd.Series` and optional `InspectionConfig`.
3. Return a dataclass in `models.py` if the result crosses module boundaries.
4. Register it explicitly in `inspect_dataset` in `inspector.py` and attach the result to `Inspection` or `ColumnSummary`.
5. Consume the stored result in the renderer; do not recalculate it there.
6. Create `tests/unit/profiling/test_example.py` and run `pytest tests/unit/profiling/test_example.py -q`.

```python
# profiling/example.py
from dataclasses import dataclass
import pandas as pd
from ..config import InspectionConfig

@dataclass(frozen=True)
class ExampleProfile:
    count: int

def profile_example(frame: pd.DataFrame, config: InspectionConfig | None = None) -> ExampleProfile:
    del config
    return ExampleProfile(count=len(frame))
```

```python
def test_example_is_pure():
    frame = pd.DataFrame({"x": [1, 2]})
    assert profile_example(frame).count == 2
    assert frame["x"].tolist() == [1, 2]
```

## Add one quality check

1. Put a narrow check in `smart_data_inspector/quality/<name>.py`, or create `quality/<category>/<name>.py` for a real family.
2. Accept computed profiles when possible; do not duplicate profiling work.
3. Return `Finding(check_name, column, severity, evidence, rule, explanation)`.
4. Register it in `inspect_dataset`, then add a focused test in the mirrored test location.
5. The report will automatically include registered findings in priority order; add narrative treatment only when it improves interpretation.

```python
from ..models import Finding

def check_example(column: str, count: int, threshold: int) -> list[Finding]:
    if count < threshold:
        return []
    return [Finding("Example check", column, "info", f"{count} affected records.",
                    f"count >= {threshold}.", "Review this observation in context.")]
```

Test both sides of the threshold and assert all six fields that the report needs.

## Add a new category folder

For a substantial family such as `quality/schema/`:

1. Create `smart_data_inspector/quality/schema/__init__.py` and focused files such as `mixed_types.py` and `duplicate_columns.py`.
2. Create `tests/unit/quality/schema/` with one matching test per source module.
3. Add helpers only after two checks genuinely share logic; keep each check independently callable.
4. Import and register each check explicitly from `inspector.py`.
5. Run `pytest tests/unit/quality/schema/ -q`, then `pytest -q`.

The matching directory is itself the category test command, so no central test registry needs editing:

```sh
make test ARGS=tests/unit/quality/schema
```

## Add a chart

1. Create `smart_data_inspector/visualizations/example.py`.
2. Set Matplotlib’s `Agg` backend before importing `pyplot`.
3. Accept the data/result and `output_dir`, return `Path | None`, skip unsuitable inputs, save one PNG and always close the figure.
4. Add it to `visualizations/pipeline.py` with a stable asset key and caption. The pipeline catches a chart failure so profiling still succeeds.
5. Reference it from `render_report` with `_asset(lines, inspection.assets, "example")`.
6. Test that an appropriate DataFrame creates a nonempty PNG and unsuitable data returns `None`.

```python
def plot_example(frame: pd.DataFrame, output_dir: Path) -> Path | None:
    if frame.empty:
        return None
    path = output_dir / "example.png"
    figure, axis = plt.subplots()
    axis.plot(range(len(frame)))
    figure.savefig(path, dpi=160)
    plt.close(figure)
    return path
```

## Configuration and tests

Add a threshold to frozen `InspectionConfig`, validate it in `__post_init__`, document its meaning, and test invalid boundaries. Do not read environment variables in analysis modules. Handle empty, all-null, missing, nonfinite and unsuitable inputs by returning an empty/`None` structured result rather than printing or throwing unrelated exceptions.

Useful commands:

```sh
make test ARGS=tests/unit/profiling/test_missingness_profiler.py
make test ARGS=tests/unit/quality
pytest tests/unit/profiling/ -q
pytest -q
```
