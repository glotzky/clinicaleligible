# TrialIntel: Clinical Trial Intelligence

**TrialIntel** is an AI-powered pipeline that transforms unstructured clinical trial eligibility criteria into structured, machine-readable data. 

### 💡 The Problem
Clinical trial eligibility (inclusion/exclusion criteria) is currently stored as free-text medical jargon. This makes it nearly impossible to programmatically match patients to trials or conduct large-scale recruitment analytics without manual review.

### 🛠️ The Solution
This project uses the **ClinicalTrials.gov API v2.0** to fetch trial data and leverages **Large Language Models (LLMs)** to parse complex medical sentences into a structured schema (JSON/SQL).

### 🚀 Key Features
- **Modern API Integration:** Fully compatible with ClinicalTrials.gov REST API v2.0.
- **Structured Extraction:** Converts text like *"Adults 18-65 with BMI > 30"* into validated JSON objects.
- **Database Interoperability:** Built with SQLAlchemy; supports SQLite (local) and PostgreSQL (cloud) via environment variables.
- **Pydantic Validation:** Ensures the AI output follows a strict schema for downstream medical applications.

### 🏗️ Tech Stack
- **Language:** Python 3.10+
- **AI/LLM:** OpenAI GPT-4o (or Llama-3 via Groq/Ollama)
- **Data:** SQLAlchemy, Pydantic, Requests
- **Database:** SQLite (Default) / PostgreSQL
