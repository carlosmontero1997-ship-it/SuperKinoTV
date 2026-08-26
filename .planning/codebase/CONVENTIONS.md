# Conventions

## Naming Conventions
- Functions and variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- File names: `lowercase_with_underscores`

## Code Style
- Follows `black` formatting (Python 3.11+)
- Type hints used where beneficial, not obsessively
- Docstrings follow NumPy format for core modules
- Streamlit pages follow consistent layout structure

## Import Order
1. Standard library imports (`os`, `sys`, `json`, etc.)
2. Related third-party imports (`pandas`, `numpy`, `streamlit`, etc.)
3. Local application/library imports (`from superkino.core import ...`)

## Commenting
- All public functions have docstrings
- Complex mathematical formulas documented with references
- Inline comments for non-obvious logic, especially in analysis functions

## Error Handling
- Core module errors raise specific exception types
- UI layer catches and displays user-friendly messages
- Validation errors caught during data ingestion