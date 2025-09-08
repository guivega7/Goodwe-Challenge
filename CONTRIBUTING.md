# Contributing to SolarMind

We welcome contributions to the SolarMind solar energy management system! This document outlines the process for contributing to this project.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project follows a professional code of conduct. Please be respectful and constructive in all interactions.

## Getting Started

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/solarmind.git
   cd solarmind
   ```

2. **Set up development environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Initialize database**
   ```bash
   python init_db.py
   ```

## Development Process

### Branch Naming
- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `hotfix/description` - Critical fixes
- `docs/description` - Documentation updates

### Testing
- Write tests for new features
- Ensure all existing tests pass
- Test with different Python versions when possible

### Environment Setup
- Use virtual environments
- Keep dependencies updated
- Test with both development and production configs

## Coding Standards

### Python Style
- Follow PEP 8 style guidelines
- Use type hints for function parameters and returns
- Maximum line length: 100 characters
- Use meaningful variable and function names

### Documentation
- All functions must have docstrings
- Use Google-style docstrings
- Include parameter types and return types
- Document complex algorithms and business logic

### Example Function Documentation
```python
def calculate_energy_savings(
    consumption: float, 
    generation: float, 
    rate: float = 0.95
) -> Dict[str, float]:
    """
    Calculate energy savings based on consumption and generation.
    
    Args:
        consumption: Energy consumption in kWh
        generation: Energy generation in kWh
        rate: Energy rate per kWh (default: R$ 0.95)
        
    Returns:
        dict: Savings information including total savings and excess energy
        
    Raises:
        ValueError: If consumption or generation values are negative
    """
```

### Error Handling
- Use try-catch blocks for external API calls
- Log errors with appropriate levels
- Provide meaningful error messages
- Handle edge cases gracefully

### Database
- Use SQLAlchemy ORM patterns
- Include proper relationships between models
- Add validation at the model level
- Use database transactions for multi-step operations

## Commit Guidelines

### Commit Message Format
```
type(scope): brief description

Detailed explanation of the change, if necessary.

- List any breaking changes
- Reference any issues fixed: Fixes #123
```

### Commit Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples
```
feat(api): add energy prediction endpoint

Add new endpoint for AI-based energy generation prediction
based on weather data and historical patterns.

- Supports multiple prediction models
- Includes confidence intervals
- Cached results for performance

Fixes #45
```

## Pull Request Process

### Before Submitting
1. Ensure code follows style guidelines
2. Add or update tests as needed
3. Update documentation if required
4. Test thoroughly in development environment
5. Rebase on latest main branch

### Pull Request Template
- **Description**: Clear description of changes
- **Type of Change**: Feature, bugfix, documentation, etc.
- **Testing**: How the changes were tested
- **Screenshots**: If UI changes are involved
- **Breaking Changes**: List any breaking changes

### Review Process
1. Automated checks must pass
2. At least one code review required
3. All conversations must be resolved
4. Maintainer approval required for merge

## Architecture Guidelines

### Directory Structure
- `models/` - Database models and business logic
- `routes/` - Flask blueprints and web routes
- `services/` - External integrations and business services
- `utils/` - Utility functions and helpers
- `templates/` - HTML templates
- `static/` - CSS, JavaScript, and images

### API Design
- Use RESTful conventions
- Include proper HTTP status codes
- Provide consistent error responses
- Support both JSON and HTML responses where appropriate

### Security Considerations
- Validate all user inputs
- Use parameterized queries
- Implement proper authentication
- Follow OWASP security guidelines

## Getting Help

- Open an issue for bugs or feature requests
- Use discussions for questions
- Check existing issues before creating new ones
- Provide detailed information when reporting bugs

## Recognition

Contributors will be recognized in the project README and release notes.

Thank you for contributing to SolarMind!
