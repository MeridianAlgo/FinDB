# Contributing to Financial News Scraper

Thank you for your interest in contributing to the Financial News Scraper project. This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, gender, gender identity and expression, sexual orientation, disability, personal appearance, body size, race, ethnicity, age, religion, or nationality.

### Expected Behavior

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- GitHub account
- Basic understanding of web scraping and databases

### Development Setup

1. Fork the repository on GitHub

2. Clone your fork locally:
```bash
git clone https://github.com/YOUR_USERNAME/FinDB.git
cd FinDB
```

3. Add upstream remote:
```bash
git remote add upstream https://github.com/MeridianAlgo/FinDB.git
```

4. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

5. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

6. Install pre-commit hooks:
```bash
pre-commit install
```

## Development Process

### Branching Strategy

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: New features
- `bugfix/*`: Bug fixes
- `hotfix/*`: Urgent production fixes

### Workflow

1. Create a new branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes

3. Run tests:
```bash
pytest tests/
```

4. Commit your changes:
```bash
git commit -m "Add feature: description"
```

5. Push to your fork:
```bash
git push origin feature/your-feature-name
```

6. Create a Pull Request on GitHub

## Coding Standards

### Python Style Guide

Follow PEP 8 guidelines with these specifications:

- Line length: 100 characters maximum
- Indentation: 4 spaces (no tabs)
- Quotes: Single quotes for strings, double quotes for docstrings
- Imports: Grouped and sorted (stdlib, third-party, local)

### Code Formatting

Use Black for code formatting:
```bash
black scraper.py models.py database.py
```

### Type Hints

Use type hints for function signatures:
```python
def fetch_article(url: str, timeout: int = 30) -> Optional[str]:
    pass
```

### Docstrings

Use Google-style docstrings:
```python
def process_article(article: Dict[str, Any]) -> FinancialNews:
    """Process raw article data into database model.
    
    Args:
        article: Dictionary containing article data
        
    Returns:
        FinancialNews model instance
        
    Raises:
        ValueError: If required fields are missing
    """
    pass
```

### Naming Conventions

- Classes: PascalCase (`NewsScraper`)
- Functions: snake_case (`fetch_article`)
- Constants: UPPER_SNAKE_CASE (`MAX_RETRIES`)
- Private methods: Leading underscore (`_internal_method`)

## Testing Guidelines

### Test Structure

```
tests/
├── unit/
│   ├── test_scraper.py
│   ├── test_database.py
│   └── test_export.py
├── integration/
│   ├── test_workflow.py
│   └── test_api.py
└── fixtures/
    └── sample_data.py
```

### Writing Tests

Use pytest for testing:

```python
import pytest
from scraper import NewsScraper

def test_fetch_rss_feed():
    """Test RSS feed fetching."""
    scraper = NewsScraper()
    feed = scraper.fetch_rss_feed('https://example.com/rss')
    assert feed is not None
    assert len(feed.entries) > 0

@pytest.mark.asyncio
async def test_async_scraping():
    """Test async scraping functionality."""
    async with NewsScraper() as scraper:
        articles, errors = await scraper.scrape_source('test_source', {})
        assert isinstance(articles, list)
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_scraper.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test
pytest tests/unit/test_scraper.py::test_fetch_rss_feed
```

### Test Coverage

Maintain minimum 80% code coverage for new code.

## Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat(scraper): add support for Reuters news source

- Implement RSS feed parser for Reuters
- Add content extraction logic
- Update configuration with Reuters settings

Closes #123
```

```
fix(database): resolve duplicate article insertion

Fixed issue where articles with same URL were being inserted
multiple times due to race condition in async processing.

Fixes #456
```

## Pull Request Process

### Before Submitting

1. Update documentation if needed
2. Add tests for new functionality
3. Ensure all tests pass
4. Update CHANGELOG.md
5. Rebase on latest main branch

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests passing
- [ ] No new warnings
```

### Review Process

1. Automated checks must pass
2. At least one maintainer approval required
3. Address all review comments
4. Squash commits if requested
5. Maintainer will merge when approved

## Issue Reporting

### Bug Reports

Use the bug report template:

```markdown
**Describe the bug**
Clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Step 1
2. Step 2
3. See error

**Expected behavior**
What should happen

**Actual behavior**
What actually happens

**Environment**
- OS: [e.g., Windows 10]
- Python version: [e.g., 3.11.0]
- Package versions: [from requirements.txt]

**Additional context**
Any other relevant information
```

### Feature Requests

Use the feature request template:

```markdown
**Is your feature request related to a problem?**
Description of the problem

**Describe the solution you'd like**
Clear description of desired functionality

**Describe alternatives you've considered**
Alternative solutions or features

**Additional context**
Any other relevant information
```

## Development Guidelines

### Adding New News Sources

1. Add source configuration to `config.py`:
```python
NEWS_SOURCES = {
    "new_source": {
        "rss_url": "https://newsource.com/rss",
        "base_url": "https://newsource.com",
        "content_selector": "div.article-body p",
        "title_selector": "h1.title",
        "date_selector": "time.published"
    }
}
```

2. Test the source:
```python
async def test_new_source():
    async with NewsScraper() as scraper:
        articles, errors = await scraper.scrape_source(
            'new_source',
            Config.NEWS_SOURCES['new_source']
        )
        assert len(articles) > 0
```

3. Update documentation

### Database Schema Changes

1. Create Alembic migration:
```bash
alembic revision -m "Add new column"
```

2. Edit migration file in `alembic/versions/`

3. Test migration:
```bash
alembic upgrade head
alembic downgrade -1
```

4. Update models.py

### API Endpoint Changes

1. Add endpoint to `api.py`
2. Add Pydantic models for request/response
3. Add tests in `tests/integration/test_api.py`
4. Update API documentation in `docs/API.md`

## Questions?

If you have questions:
- Check existing documentation
- Search existing issues
- Open a new issue with the "question" label
- Contact maintainers

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing to Financial News Scraper!
