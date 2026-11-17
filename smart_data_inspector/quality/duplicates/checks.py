"""Duplicate review prompts, not automatic deduplication."""

from ...models import Finding


def check_duplicates(count: int) -> list[Finding]:
    if not count:
        return []
    return [Finding(
        "Duplicate rows", None, "warning", f"{count:,} repeated row(s) beyond the first occurrence.",
        "Full-row equality after missing-value normalization; count additional occurrences only.",
        "Check whether repeated records are intended replicates before removing anything.",
    )]
