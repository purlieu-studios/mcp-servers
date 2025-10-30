# Pull Request

## 📋 Description
<!-- Provide a clear and concise description of your changes -->



## 🔗 Related Issue
<!-- Link to the issue this PR addresses -->
Closes #

## 🎯 Type of Change
<!-- Mark the relevant option with an 'x' -->

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🧪 Test additions or updates
- [ ] ♻️ Code refactoring (no functional changes)
- [ ] 🔧 Configuration change
- [ ] ⚡ Performance improvement

## 📏 Code Size Check
<!-- Verify your PR follows our size guidelines -->

- [ ] **Total changes are ≤500 lines of code** (excluding tests, docs, config)
  - If over 500 LOC, explain why or consider splitting into multiple PRs
  - Use `git diff --stat origin/main...HEAD` to check

**Reason if over 500 LOC:**
<!-- Explain why this PR exceeds the limit -->


## ✅ Testing
<!-- Describe the tests you ran and how to reproduce them -->

- [ ] All existing tests pass locally (`pytest`)
- [ ] Added new tests for new functionality
- [ ] Manual testing completed

**Test Coverage:**
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Test coverage remains ≥80% for changed files

**Testing Steps:**
1.
2.
3.

## 📸 Screenshots (if applicable)
<!-- Add screenshots for UI changes -->



## 🧪 Test Results
<!-- Paste test output showing all tests passing -->

```bash
# Paste pytest output here
```

## 📋 Checklist
<!-- Verify all items before requesting review -->

### Code Quality
- [ ] Code follows the project's style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] No unnecessary console.log/print statements
- [ ] No hardcoded values (use config/environment variables)

### Documentation
- [ ] Documentation updated (README, docstrings, comments)
- [ ] CLAUDE.md guide updated if tool/API changes
- [ ] Breaking changes documented in commit message

### Testing & CI
- [ ] All tests pass locally
- [ ] No new warnings or errors
- [ ] CI pipeline passes (GitHub Actions)
- [ ] Code coverage maintained or improved

### Git Hygiene
- [ ] Commit messages are clear and descriptive
- [ ] No merge commits (rebased on latest main)
- [ ] No unrelated changes included
- [ ] Branch is up to date with main

## 🔍 Review Focus Areas
<!-- Guide reviewers on what to focus on -->

Please pay special attention to:
-
-

## 📝 Additional Notes
<!-- Any additional context, concerns, or questions for reviewers -->



## 🤖 AI-Assisted Development
<!-- If this PR was developed with AI assistance (e.g., Claude Code) -->

- [ ] This PR includes AI-assisted code
- [ ] All AI-generated code has been reviewed and tested
- [ ] AI suggestions were validated against project standards

---

**For Reviewers:**
- Verify LOC limit is respected (or justified)
- Ensure all tests pass in CI
- Check code coverage hasn't decreased
- Validate documentation is complete
