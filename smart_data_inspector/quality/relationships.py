"""Quality prompts based on strong associations, without causal claims."""

from ..config import InspectionConfig
from ..models import Finding, RelationshipProfile


def check_relationships(profile: RelationshipProfile, config: InspectionConfig) -> list[Finding]:
    findings = []
    for relationship in profile.relationships:
        strength = max(abs(relationship.pearson or 0), abs(relationship.spearman or 0))
        if strength < config.correlation_threshold:
            continue
        findings.append(Finding("Strong numerical correlation", f"{relationship.left} ↔ {relationship.right}", "info",
                                f"Pearson={relationship.pearson:.3g}, Spearman={relationship.spearman:.3g}, based on {relationship.pair_count:,} complete pair(s).",
                                f"Absolute Pearson or Spearman correlation >= {config.correlation_threshold:.2f}.",
                                "The variables may be redundant or related; correlation does not establish causation."))
    return findings
