# Contributing to TokenLens

First off, thank you for considering contributing to TokenLens! It's people like you that make TokenLens such a great tool for the community.

## Development Setup

To set up your local development environment, follow these steps:

### Prerequisites

- Python 3.11+
- Node.js 20+
- Google Gemini API Key

### Backend Setup

1. **Navigate to the backend directory (or root)**:
   You can run the backend directly from the project root.

2. **Create a virtual environment** (optional but recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables**:
   Create a `.env` file or export them directly in your terminal:
   ```bash
   export GEMINI_API_KEY="your-gemini-api-key"
   export TOKEN_LENS_API_KEY="your-secure-auth-key"  # Used for API authentication
   ```

5. **Run the FastAPI server**:
   ```bash
   uvicorn backend.main:app --reload --port 8080
   ```
   The API will be available at `http://localhost:8080` and the interactive Swagger UI at `http://localhost:8080/docs`.

### Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment variables**:
   Create a `.env.local` file in the `frontend` directory:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8080
   NEXT_PUBLIC_API_KEY=your-secure-auth-key
   ```

4. **Run the Next.js development server**:
   ```bash
   npm run dev
   ```
   The dashboard will be available at `http://localhost:3000`.

## Submitting Pull Requests

1. Fork the repository and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. Ensure the test suite passes (`pytest backend/tests/`).
4. Format your code (e.g., using `black` or `ruff` for Python, `prettier` for TypeScript).
5. Issue that pull request!

## Code of Conduct

Please note that this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms.
