# AI Job Hunter — Workflow

## Job Discovery
```mermaid
flowchart TD
    A["Indeed Job Alerts"] --> B["Gmail API"]
    B --> C["Job Extraction"]
    C --> D["Duplicate Removal"]
    D --> E["Job Matching and Filtering"]
    E --> F["Jobs for Review"]
```

## Interactive Dashboard
```mermaid
flowchart TD
    A["Job Discovery"] --> B["Streamlit Dashboard"]
    B --> C["AI Job Analysis"]
    C --> D["Resume Tailoring"]
    D --> E["Resume Draft"]
    E --> F["PDF Export"]
    F --> G["Manual Application"]
```

## Human Oversight
AI-generated recommendations and resume drafts require human review. Applications are submitted manually.
