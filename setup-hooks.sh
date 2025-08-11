#!/bin/bash
# Setup script for Git hooks
# Run this script to install pre-commit hooks for code quality checks

set -e

echo "🔧 Setting up Git hooks for code quality checks..."

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a Git repository. Please run this script from the project root."
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Copy pre-commit hook
if [ -f ".githooks/pre-commit" ]; then
    cp .githooks/pre-commit .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
    echo "✅ Pre-commit hook installed"
else
    echo "❌ Error: .githooks/pre-commit not found"
    exit 1
fi

# Test the hook
echo ""
echo "🧪 Testing pre-commit hook..."
if .git/hooks/pre-commit; then
    echo ""
    echo "🎉 Git hooks setup completed successfully!"
    echo ""
    echo "📋 The following checks will run before each commit:"
    echo "   • Python linting (ruff)"
    echo "   • Code formatting (ruff)"
    echo "   • YAML validation"
    echo "   • Type checking (if mypy available)"
    echo "   • Unit tests only (integration tests excluded to reduce server load)"
    echo "   • Database creation test"
    echo ""
    echo "💡 To bypass hooks temporarily, use: git commit --no-verify"
    echo "⚠️  Only use --no-verify in emergencies!"
else
    echo ""
    echo "❌ Pre-commit hook test failed. Please check the output above."
    exit 1
fi