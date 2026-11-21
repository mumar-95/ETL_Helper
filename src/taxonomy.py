"""Canonical taxonomy for the scenario bank."""

from __future__ import annotations

TECHNOLOGIES = ("PowerCenter", "IICS", "SQL")

DIFFICULTIES = ("beginner", "intermediate", "advanced", "senior", "expert")

LABELS = ("verified", "publicly_reported", "community", "ai_generated")

STATUSES = ("draft", "validated", "published")

CATEGORIES = (
    "Mapping design scenarios",
    "Transformation scenarios",
    "Lookup scenarios",
    "Incremental loading scenarios",
    "SCD implementation scenarios",
    "Performance tuning scenarios",
    "Data quality scenarios",
    "Duplicate handling scenarios",
    "Error handling scenarios",
    "Workflow and taskflow scenarios",
    "Production support scenarios",
    "Recovery and restart scenarios",
    "Data reconciliation scenarios",
    "Complex business logic scenarios",
    "Architecture and framework scenarios",
    "Real-time project challenges",
)

IICS_SERVICE_SCOPES = (
    "CDI",
    "CDI + Taskflows",
    "CAI",
    "CDI + API/App Integration",
    "CDI + Mass Ingestion",
    "CDI + Data Quality",
    "Requires non-CDI IICS service",
)

TECH_QUOTAS = {
    "PowerCenter": 400,
    "IICS": 350,
    "SQL": 250,
}

EXPERIENCE_BANDS = {
    "0-2 years": {"years_min": 0, "years_max": 2, "difficulties": ("beginner", "intermediate")},
    "3-5 years": {"years_min": 3, "years_max": 5, "difficulties": ("intermediate", "advanced")},
    "6-9 years": {"years_min": 6, "years_max": 9, "difficulties": ("advanced", "senior")},
    "10-15+ years": {"years_min": 10, "years_max": 20, "difficulties": ("senior", "expert")},
}

DIFFICULTY_YEAR_RANGES = {
    "beginner": (0, 2),
    "intermediate": (2, 5),
    "advanced": (5, 9),
    "senior": (8, 12),
    "expert": (12, 20),
}

POWERCENTER_TOPICS = {
    "Lookup scenarios": [
        "large lookup table performance",
        "dynamic lookup cache",
        "lookup cache synchronization",
        "multiple lookup transformations",
        "connected versus unconnected lookup",
        "lookup SQL override",
        "lookup returning multiple matching records",
        "lookup with effective dates",
        "lookup with composite keys",
        "persistent cache",
        "lookup cache rebuilding",
        "lookup cache out-of-sync",
    ],
    "Incremental loading scenarios": [
        "last successful load date",
        "mapping variable implementation",
        "multiple source tables with different load dates",
        "incremental loading with timestamp columns",
        "incremental loading without update timestamps",
        "late-arriving records",
        "deleted source records",
        "restarting failed incremental loads",
        "watermark management",
        "duplicate prevention",
    ],
    "SCD implementation scenarios": [
        "SCD Type 1",
        "SCD Type 2",
        "SCD Type 3",
        "multiple changes to one customer",
        "historical record preservation",
        "expired record handling",
        "late-arriving dimensions",
        "early-arriving facts",
        "multiple source systems feeding one dimension",
        "surrogate key management",
    ],
    "Performance tuning scenarios": [
        "session suddenly running slowly",
        "source bottleneck",
        "target bottleneck",
        "transformation bottleneck",
        "lookup cache overflow",
        "aggregator performance",
        "sorter performance",
        "joiner optimization",
        "partitioning",
        "pushdown optimization",
        "large-volume data processing",
    ],
    "Workflow and taskflow scenarios": [
        "session failure",
        "workflow recovery",
        "dependency handling",
        "missing source file",
        "multiple file arrivals",
        "restart from failed session",
        "duplicate records after recovery",
        "commit interval issues",
        "workflow scheduling",
        "parameter file errors",
    ],
    "Architecture and framework scenarios": [
        "multiple source systems",
        "multiple target tables",
        "parent-child data loading",
        "fact and dimension loading",
        "CDC implementation",
        "dynamic file processing",
        "metadata-driven ETL",
        "error tables",
        "audit tables",
        "restartable ETL frameworks",
    ],
}

IICS_TOPICS = {
    "Workflow and taskflow scenarios": [
        "Secure Agent failures",
        "agent group configuration",
        "runtime environment issues",
        "mapping task failures",
        "taskflow failures",
        "parallel task execution",
        "conditional task execution",
        "taskflow recovery",
    ],
    "Mapping design scenarios": [
        "parameterization",
        "reusable mappings",
        "cloud source and target connections",
        "dynamic file processing",
        "high-volume processing",
    ],
    "Lookup scenarios": [
        "lookup optimization",
        "unconnected lookup in CDI",
        "lookup cache in Secure Agent",
    ],
    "Incremental loading scenarios": [
        "incremental loading",
        "CDC",
        "watermark parameters",
    ],
    "Architecture and framework scenarios": [
        "API-based integration",
        "REST API automation",
        "deployment failures",
        "environment-specific configuration",
        "PowerCenter to IICS migration",
        "complex enterprise integration frameworks",
    ],
    "Production support scenarios": [
        "production monitoring",
        "data reconciliation",
        "error handling",
    ],
}

SQL_TOPICS = {
    "Duplicate handling scenarios": [
        "duplicate removal",
        "latest record selection",
        "source-to-target comparison",
    ],
    "Data reconciliation scenarios": [
        "historical data comparison",
        "insert missing records",
        "update changed records",
        "delete obsolete records",
        "data reconciliation",
    ],
    "Complex business logic scenarios": [
        "ROW_NUMBER",
        "RANK",
        "DENSE_RANK",
        "LEAD",
        "LAG",
        "FIRST_VALUE",
        "LAST_VALUE",
        "running totals",
        "moving averages",
        "consecutive date calculations",
    ],
    "SCD implementation scenarios": [
        "SCD Type 1 with MERGE",
        "SCD Type 2 with MERGE",
        "MERGE implementation",
    ],
    "Incremental loading scenarios": [
        "incremental loading SQL",
        "watermark based extract",
    ],
    "Performance tuning scenarios": [
        "large-table joins",
        "query optimization",
        "index optimization",
        "CTE-based transformations",
        "complex subqueries",
        "hierarchical queries",
    ],
}

BUSINESS_DOMAINS = [
    "Retail banking customer master",
    "E-commerce order fulfillment",
    "Healthcare claims adjudication",
    "Telecom subscriber billing",
    "Insurance policy administration",
    "Manufacturing inventory",
    "HR employee dimension",
    "Logistics shipment tracking",
    "Capital markets trade settlement",
    "Utilities meter reading",
    "Airline passenger booking",
    "Hospital patient encounters",
]

DATA_VOLUMES = [
    "50K rows/day",
    "500K rows/day",
    "2M rows/day",
    "10M rows/batch",
    "50M historical backfill",
    "near-real-time micro-batches",
]

SECTION_TITLES = {
    "A": "What does the business need?",
    "B": "Understand the scenario",
    "C": "Sample input data",
    "D": "Expected output",
    "E": "Step-by-step build",
    "F": "Each transformation explained",
    "G": "SQL logic",
    "H": "Flow diagram",
    "I": "Make it faster",
    "J": "Errors, restart, and production",
    "K": "Other ways to build it",
    "L": "Short interview answer",
    "M": "Follow-up questions",
}
