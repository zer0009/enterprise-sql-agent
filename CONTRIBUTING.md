# Contributing to Enterprise SQL Agent

Thank you for your interest in contributing to the Enterprise SQL Agent! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Development Workflow](#development-workflow)
- [Testing Guidelines](#testing-guidelines)
- [Code Style](#code-style)
- [Documentation](#documentation)
- [Release Process](#release-process)

## 🤝 Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct.html). By participating, you agree to uphold this code.

### Our Pledge

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different viewpoints and experiences
- Show empathy towards other community members

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- PostgreSQL database (for testing)
- AI model API key (Google Gemini or OpenAI)

### Fork and Clone

1. **Fork the repository**
   ```bash
   # Click the "Fork" button on GitHub
   # Then clone your fork
   git clone https://github.com/zer0009/enterprise-sql-agent.git
   cd enterprise-sql-agent
   ```

2. **Add upstream remote**
   ```bash
   git remote add upstream https://github.com/zer0009/enterprise-sql-agent.git
   ```

3. **Create a development branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 🛠️ Development Setup

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp env.template .env

# Edit .env with your settings
# At minimum, configure:
# - DATABASE_TYPE=postgresql
# - POSTGRES_* settings
# - GOOGLE_API_KEY or OPENAI_API_KEY
```

### 3. Database Setup

```bash
# Create test database
createdb enterprise_sql_agent_test

# Run basic tests
python -m pytest tests/ -v
```

## 📝 Contributing Guidelines

### Types of Contributions

We welcome various types of contributions:

#### 🐛 **Bug Fixes**
- Fix existing issues
- Improve error handling
- Resolve security vulnerabilities

#### ✨ **New Features**
- Add support for new database types
- Implement new AI model integrations
- Add new security features
- Enhance performance monitoring

#### 📚 **Documentation**
- Improve README and documentation
- Add code comments and docstrings
- Create tutorials and examples
- Update API documentation

#### 🧪 **Testing**
- Add unit tests
- Improve test coverage
- Add integration tests
- Performance testing

#### 🔧 **Infrastructure**
- CI/CD improvements
- Docker support
- Deployment scripts
- Monitoring and logging

### Contribution Areas

#### **High Priority**
- **Database Support**: MySQL, SQLite, SQL Server, Oracle, MongoDB
- **Security Enhancements**: Additional SQL injection patterns
- **Performance**: Query optimization and caching
- **Testing**: Comprehensive test coverage

#### **Medium Priority**
- **UI/UX**: Web interface or GUI
- **API**: RESTful API endpoints
- **Monitoring**: Advanced performance metrics
- **Documentation**: Tutorials and examples

#### **Low Priority**
- **Integrations**: Third-party tool integrations
- **Advanced Features**: Custom prompt templates
- **Deployment**: Docker and cloud deployment

## 🔄 Pull Request Process

### Before Submitting

1. **Check existing issues** - Ensure your contribution addresses an open issue
2. **Create an issue** - For major changes, discuss the approach first
3. **Update documentation** - Include relevant documentation updates
4. **Add tests** - Include tests for new functionality
5. **Update CHANGELOG** - Document your changes

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Database Support
- [ ] PostgreSQL (required)
- [ ] MySQL
- [ ] SQLite
- [ ] SQL Server
- [ ] Oracle
- [ ] MongoDB

## Security
- [ ] No security vulnerabilities introduced
- [ ] SQL injection prevention maintained
- [ ] Security tests pass

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] CHANGELOG updated
```

### Review Process

1. **Automated Checks** - CI/CD pipeline runs tests
2. **Code Review** - Maintainers review code quality
3. **Security Review** - Security-focused review for sensitive changes
4. **Testing** - Manual testing on PostgreSQL
5. **Approval** - At least one maintainer approval required

## 🐛 Issue Reporting

### Bug Reports

Use the bug report template:

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen.

**Environment**
- OS: [e.g., Windows 10, macOS 12, Ubuntu 20.04]
- Python version: [e.g., 3.8.10]
- Database: [e.g., PostgreSQL 13]
- AI Model: [e.g., Gemini 2.0 Flash]

**Additional context**
Add any other context about the problem here.
```

### Feature Requests

Use the feature request template:

```markdown
**Is your feature request related to a problem?**
A clear description of what the problem is.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
A clear description of any alternative solutions.

**Additional context**
Add any other context or screenshots about the feature request.
```

## 🔄 Development Workflow

### Branch Naming

Use descriptive branch names:

```bash
# Features
feature/add-mysql-support
feature/improve-error-handling
feature/add-web-interface

# Bug fixes
bugfix/fix-postgresql-connection
bugfix/resolve-memory-leak
bugfix/fix-security-vulnerability

# Documentation
docs/update-readme
docs/add-api-documentation
docs/improve-contributing-guide

# Refactoring
refactor/improve-code-structure
refactor/optimize-performance
refactor/update-dependencies
```

### Commit Messages

Follow conventional commit format:

```bash
# Format: type(scope): description

# Examples:
feat(database): add MySQL support
fix(security): prevent SQL injection in query validation
docs(readme): update installation instructions
test(agent): add unit tests for error recovery
refactor(utils): improve performance monitoring
```

### Commit Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `security`: Security-related changes

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── test_sql_agent.py
│   ├── test_security.py
│   └── test_performance.py
├── integration/             # Integration tests
│   ├── test_database.py
│   └── test_ai_integration.py
├── security/               # Security tests
│   ├── test_sql_injection.py
│   └── test_validation.py
└── fixtures/               # Test data
    ├── sample_queries.json
    └── test_database.sql
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test categories
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest tests/security/

# Run with coverage
python -m pytest --cov=src --cov-report=html

# Run specific test
python -m pytest tests/unit/test_sql_agent.py::test_process_question
```

### Test Requirements

- **Unit Tests**: Test individual functions and methods
- **Integration Tests**: Test component interactions
- **Security Tests**: Test SQL injection prevention
- **Performance Tests**: Test query performance and optimization
- **Database Tests**: Test with real PostgreSQL database

## 📏 Code Style

### Python Style Guide

Follow PEP 8 with these additions:

```python
# Line length: 100 characters (instead of 79)
# Use type hints for all functions
# Use docstrings for all public functions

def process_question(
    self, 
    question: str, 
    lightweight: bool = False
) -> Dict[str, Any]:
    """
    Process a natural language question and return structured response.
    
    Args:
        question: The natural language question to process
        lightweight: Whether to use lightweight processing mode
        
    Returns:
        Dictionary containing the structured response
        
    Raises:
        ValueError: If question is empty or invalid
        SecurityError: If query violates security policies
    """
    # Implementation here
```

### Code Organization

```python
# File structure
import os
import sys
from typing import Dict, Any, Optional

# Third-party imports
from langchain import SomeClass
from sqlalchemy import create_engine

# Local imports
from .config import DatabaseConfig
from .utils import PerformanceMonitor
```

### Documentation Standards

```python
class UniversalSQLAgent:
    """
    Enhanced Universal SQL Agent with improved structure and organization.
    
    This class provides a clean interface for SQL query processing with
    better separation of concerns and improved maintainability.
    
    Attributes:
        db: SQLDatabase instance for database operations
        llm: Language model instance for AI processing
        agent: AgentExecutor instance for query processing
        conversation_history: List of previous conversations
        
    Example:
        >>> agent = UniversalSQLAgent()
        >>> await agent.setup_database()
        >>> result = await agent.process_question("Show me all users")
    """
```

## 📚 Documentation

### Documentation Types

1. **Code Documentation**: Docstrings and inline comments
2. **API Documentation**: Function and class documentation
3. **User Documentation**: README, tutorials, examples
4. **Developer Documentation**: Contributing guide, architecture docs

### Documentation Standards

- Use clear, concise language
- Include examples for complex functions
- Update documentation with code changes
- Use consistent formatting and style

## 🚀 Release Process

### Version Numbering

We use [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] Version number updated
- [ ] Security review completed
- [ ] Performance testing completed

## 🆘 Getting Help

### Community Support

- **GitHub Discussions**: For questions and general discussion
- **GitHub Issues**: For bug reports and feature requests
- **Code Review**: For pull request feedback

### Contact Maintainers

- **GitHub**: @zer0009
- **Issues**: Use GitHub Issues for technical questions
- **Discussions**: Use GitHub Discussions for general questions

## 🙏 Recognition

Contributors will be recognized in:

- **CONTRIBUTORS.md**: List of all contributors
- **Release Notes**: Recognition in release announcements
- **GitHub**: Contributor badges and recognition

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to the Enterprise SQL Agent! Your contributions help make this project better for everyone. 🚀
