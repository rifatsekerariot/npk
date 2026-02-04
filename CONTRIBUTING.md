# Contributing to NPK Sensor Monitor

Thank you for your interest in contributing!

## How to Contribute

1. **Fork** the repository
2. **Clone** your fork locally
3. Create a **feature branch**: `git checkout -b feature/your-feature-name`
4. Make your changes
5. **Test** your changes thoroughly
6. **Commit** with clear messages: `git commit -m "Add: feature description"`
7. **Push** to your fork: `git push origin feature/your-feature-name`
8. Open a **Pull Request**

## Development Setup

```bash
# Clone the repository
git clone https://github.com/rifatsekerariot/npk.git
cd npk

# Install dependencies
pip3 install -r requirements.txt

# Test the components
python3 src/npk_reader.py --test
```

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and small

## Testing

Before submitting a PR:

- Test sensor reading functionality
- Test MQTT publishing
- Verify configuration handling
- Check error handling

## Reporting Issues

When reporting issues, please include:

- Raspberry Pi model and OS version
- Python version
- Full error messages and logs
- Steps to reproduce

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
