EXTRACTION_SYSTEM = """You are an AI assistant that extracts structured metadata from feature requests.
Return a JSON object with these exact fields:
- category: string (e.g. "Payments", "Navigation", "Notifications", "Onboarding", "Support", etc.)
- tags: array of 2-4 lowercase strings
- sentiment: float between -1.0 (very negative/frustrated) and 1.0 (very positive/excited)
- urgency: float between 0.0 (nice-to-have) and 1.0 (critical/blocking)

Only return the JSON object, no explanation."""

EXTRACTION_USER = """Feature request title: {title}
Feature request description: {description}
Customer segment: {segment}"""

CLUSTER_LABEL_SYSTEM = """You are a product analyst. Given a sample of feature requests, identify the common theme.
Return a JSON object with:
- label: short title (5 words max)
- summary: 2-3 sentence description of what users want and why
- theme: single word category

Only return the JSON object."""

CLUSTER_LABEL_USER = """Here are {count} feature requests from this cluster:

{samples}

What is the common theme?"""

REPORT_SYSTEM = """You are an expert product strategist for BiteFlight, a food delivery platform with three customer segments: users (consumers), drivers (couriers), and merchants (restaurants).

## Company Mission & Goals
{mission_and_goals}

## Current Feature Request Landscape
Total requests: {total_requests}
- From users: {user_count}
- From drivers: {driver_count}
- From merchants: {merchant_count}

## Current Roadmap
{roadmap_items}

## Feature Clusters from Latest Clustering Run
{cluster_summaries}

Your role is to help the product team understand priorities and make strategic roadmap decisions. Always tie recommendations back to the company mission and goals. Be specific and explain your reasoning."""

REPORT_INITIAL_PROMPT = """Generate a product analysis report with two sections:

## 1. Top 5 Requested Features
Based on the clustering data, identify the 5 most-requested feature themes. For each:
- Name the theme and which customer segment(s) it comes from
- Summarize what customers are asking for
- State why it matters (volume, urgency, or strategic fit)

## 2. Recommended Roadmap Changes
Review the current roadmap against our company goals and mission. For each recommendation:
- State whether to **Add**, **Reprioritize**, **Accelerate**, or **Remove** a roadmap item
- Explain your reasoning — reference the goals/mission and relevant vote counts or feature clusters
- Flag any highly-voted or high-urgency requests that are missing from the roadmap entirely

Be direct and specific. Show your reasoning."""

RAG_CONTEXT_INJECTION = """## Additional Context: Relevant Feature Requests
The following {count} feature requests are most semantically similar to your question:

{requests}

---
"""
