# Contributing to ScholarAI Platform

First off, thank you for considering contributing to the ScholarAI Platform! It is people like you who make this project better for everyone.

The following is a set of guidelines for contributing to the ScholarAI Platform, which is hosted in the [HaiderNaqvi-5/scholarai-platform](https://github.com/HaiderNaqvi-5/scholarai-platform) repository on GitHub. These are mostly guidelines rather than strict rules. Use your best judgment, and feel free to propose changes to this document in a pull request.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. We expect all contributors to maintain a welcoming, respectful, and inclusive environment for everyone.

## How Can I Contribute?

### Reporting Bugs

Bugs are tracked as GitHub issues. When you are creating a bug report, please include as many details as possible:

* **Use a clear and descriptive title** for the issue to identify the problem.
* **Describe the exact steps** which reproduce the problem in as much detail as possible.
* **Provide specific examples** to demonstrate the steps. Include copy/pasteable snippets or screenshots if applicable.
* **Describe the behavior you observed** after following the steps and point out what exactly is the problem with that behavior.
* **Explain which behavior you expected to see instead** and why.

### Suggesting Enhancements

Enhancement suggestions are also tracked as GitHub issues. Before creating enhancement suggestions, please check the issue tracker to see if your idea has already been proposed. When you are creating an enhancement suggestion, please include:

* **A clear and descriptive title** for the issue.
* **A detailed description** of the suggested enhancement.
* **Specific examples** to demonstrate how the feature would work.
* **An explanation of why this enhancement would be useful** to most ScholarAI Platform users.

### Pull Requests

The process described here has several goals: maintain code quality, fix problems safely, and keep the commit history clean.

1. Fork the repo and create your branch from `main`.
2. If you have added code that should be tested, please add tests.
3. If you have changed APIs or features, update the corresponding documentation.
4. Ensure the test suite passes locally before submitting.
5. Make sure your code conforms to the existing style guidelines of the project.
6. Submit your pull request with a clear description of the changes.

### SLC Governance Requirements

All feature work must follow the ScholarAI stage contract.

1. Every feature issue and PR must include one stage label: `v0.1`, `v0.2`, `v0.3`, or `v1.x`.
2. No stage label means no sprint entry.
3. PRs must explicitly describe SLC impact and deferred-stage impact.
4. UI-affecting changes must include evidence links for desktop and mobile (or a justified `N/A`).
5. PRs must map to acceptance checklist IDs from `docs/scholarai/v0_1_slc_acceptance_checklist.md`.
6. Canonical product/governance docs live under `docs/scholarai/` and must remain terminology-consistent with the SLC model.

## Development Setup

To set up your local development environment, please follow these general steps:

1. Fork the [HaiderNaqvi-5/scholarai-platform](https://github.com/HaiderNaqvi-5/scholarai-platform) repository.
2. Clone your fork locally.
3. Install the project dependencies (refer to the `README.md` for specific installation commands).
4. Create a new branch for your feature or bugfix.
5. Make your changes and commit them.

## Commit Messages

To keep the project history clean and readable, please format your commit messages accordingly:

* Limit the subject line to 50 characters.
* Capitalize the subject line.
* Do not end the subject line with a period.
* Use the imperative mood in the subject line (e.g., "Add user authentication" instead of "Added user authentication").
* Wrap the body at 72 characters.
* Use the body to explain what and why rather than how.

## Getting Help

If you have any questions or need guidance on how to implement a specific feature, feel free to open a discussion issue or reach out to the maintainers on GitHub.

Thank you for your contributions!
