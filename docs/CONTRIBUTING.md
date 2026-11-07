# Contributing to DSA_DAILY

Thank you for your interest in contributing to DSA_DAILY. We welcome contributions, bug fixes, enhancements, and documentation improvements from developers of all skill levels.

---

## 1. Code of Conduct

We are committed to providing a welcoming, inclusive, and harassment-free environment for everyone. Please be respectful, constructive, and collaborative in all discussions, pull requests, and issue reports.

---

## 2. How to Contribute

### 2.1. Reporting Bugs
- Search existing GitHub issues before submitting a new bug report.
- Include a descriptive title, clear steps to reproduce the issue, expected versus actual behavior, and error logs or screenshots.
- Specify your Python version and environment details (operating system, SQLite version).

### 2.2. Suggesting Features
- Open an issue describing the proposed feature, the problem it solves, and potential implementation approaches.
- Wait for feedback or discussion before opening a pull request for large feature implementations.

### 2.3. Submitting Pull Requests
1. Fork the repository and clone your fork locally.
2. Create a topic branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes adhering to project standards and conventions.
4. Run syntax checks and write tests where applicable.
5. Commit your changes with concise, informative commit messages following conventional commit guidelines:
   - `feat: add automated streak recovery handler`
   - `fix: resolve challenge date offset bug in daily scheduler`
   - `docs: update command reference for /scope commands`
6. Push your branch to GitHub and open a Pull Request targeting the `main` branch.

---

## 3. Development Workflow

### 3.1. Local Python Environment Setup
1. Ensure Python 3.12 or newer is installed.
2. Navigate to the bot directory and activate a virtual environment:
   ```bash
   cd bot
   python3 -m venv .venv
   source .venv/bin/activate   # On Windows: .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
3. Configure `bot/.env` with `DEV_MODE=true` and your test Discord server ID (`DEV_GUILD_ID`):
   ```env
   DISCORD_TOKEN=your_test_bot_token
   OWNER_DISCORD_ID=your_discord_id
   DEV_MODE=true
   DEV_GUILD_ID=your_test_guild_id
   DATABASE_URL=sqlite+aiosqlite:///./data/dsa_daily_dev.db
   ```
4. Run the bot:
   ```bash
   python -m bot.main
   ```

### 3.2. Testing and Validation
- Verify Python syntax across all modified modules:
  ```bash
  python3 -m py_compile bot/**/*.py
  ```
- Use `/test problem now` and `/test solve` in Discord during development to test without waiting for UTC midnight schedules.

---

## 4. Coding Standards

- **Python Style**: Adhere to PEP 8. Use explicit type hints for function signatures and data structures.
- **Asynchronous Operations**: All database access and HTTP calls must be non-blocking using `async`/`await` (SQLAlchemy async sessions and `aiohttp`/`httpx`).
- **Error Handling**: Use explicit try/except blocks and log exceptions with `logger.exception()`. Avoid bare `except:`.
- **Database Migrations & Models**: Keep SQLAlchemy models declared in `bot/db/models.py`. Ensure table constraints and index definitions are explicit.
- **Documentation**: Update markdown documents in `docs/` whenever commands, configurations, or interfaces are modified.
