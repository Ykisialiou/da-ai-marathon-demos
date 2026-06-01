# AI Marathon Demos

This repository contains demonstration projects designed for presentations, live coding sessions, and workshops.

## Project Structure

*   **`k8s-1/`**: A lightweight Flask web application that displays NASA's Astronomy Picture of the Day (APOD). It features built-in logging, structured error handling, and a `/healthz` endpoint designed for Kubernetes liveness and readiness probes.
*   **`.github/workflows/pr-agent.yml`**: Automates Pull Request (PR) code reviews using the AI-powered PR-Agent.
*   **`.pr_agent.toml`**: Custom rules and LLM configuration for the PR-Agent.

---

## 1. NASA APOD Application (`k8s-1/`)

A simple Flask application integrating with the public NASA API.

### Prerequisites

Ensure you have Python 3.9+ installed.

### Local Setup

1. Navigate to the application directory:
   ```bash
   cd k8s-1
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Set your NASA API key. If not provided, it falls back to `"DEMO_KEY"`:
   ```bash
   export NASA_API_KEY="your_api_key"
   ```

4. Run the development server:
   ```bash
   python app.py
   ```

5. Access the application at [http://localhost:5000](http://localhost:5000) and verify the health check endpoint at [http://localhost:5000/healthz](http://localhost:5000/healthz).

---

## 2. AI Code Reviewer (PR-Agent)

This repository is integrated with the community-maintained PR-Agent to automatically analyze pull requests.

### LLM Engine
*   **Model**: Qwen 2.5 Coder 32B Instruct (via OpenRouter)
*   **Workflow**: Runs automatically via GitHub Actions whenever a new Pull Request is opened or a trigger comment (e.g., `/review`, `/improve`) is posted.

### Triggering AI Review

Simply open a Pull Request against the `main` branch or comment on an active PR with one of the following commands:
*   `/review` - Generates a complete PR review and summary.
*   `/improve` - Suggests structural or performance enhancements.
*   `/describe` - Automatically generates and updates the PR description.
