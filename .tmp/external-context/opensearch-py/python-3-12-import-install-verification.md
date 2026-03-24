---
source: Context7 API + PyPI JSON
library: OpenSearch Python Client
package: opensearch-py
topic: python-3-12-import-install-verification
fetched: 2026-03-23T00:00:00Z
official_docs: https://opensearch.org/docs/latest/clients/python/
---

## Package/import mapping (Python)

- **pip package**: `opensearch-py`
- **import name**: `opensearchpy`
- **basic import**: `from opensearchpy import OpenSearch`

## Python 3.12 compatibility (current, version-relevant)

- Current PyPI release observed: `opensearch-py==3.1.0`
- `3.1.0` metadata: `Requires-Python >=3.10,<4` (Python 3.12 supported)
- Safe minimum for Python 3.12 from package metadata history:
  - `opensearch-py>=2.6.0` (`Requires-Python >=3.8,<4`, includes Python 3.12 classifier)
  - Recommended practical floor for new projects: `>=3.0.0` (latest major line)

## Install commands (Python 3.12)

```bash
python -m pip install "opensearch-py>=3.0.0"
```

If you need async client support:

```bash
python -m pip install "opensearch-py[async]>=3.0.0"
```

## Quick import verification snippet

```python
import sys
import opensearchpy
from opensearchpy import OpenSearch

print("python:", sys.version.split()[0])
print("opensearch-py:", opensearchpy.__version__)
print("OpenSearch symbol import: OK", OpenSearch is not None)
```

## Official alternatives status

- **`opensearch-dsl`** exists on PyPI but is officially marked for deprecation after `2.1.0`.
- OpenSearch upstream guidance indicates DSL functionality was merged into `opensearch-py` (>=2.2.0) via `opensearchpy.helpers`.
- For new Python 3.12 setups, prefer **`opensearch-py`** as the primary/official client package.

## Test-environment caveats (known)

- Test snippets in official guides often use:
  - `verify_certs=False`
  - `ssl_show_warn=False`
  - and sometimes `urllib3.disable_warnings()`
- These settings suppress TLS verification warnings and are convenient for local/integration tests, but should not be copied to production defaults.
- Async tests require installing the async extra (`opensearch-py[async]`) so `aiohttp` is present.
- Avoid local module shadowing in tests (e.g., a file named `opensearchpy.py`), which breaks `import opensearchpy`.

## Source pointers used

- Context7: `/opensearch-project/opensearch-py` (USER_GUIDE, UPGRADING, COMPATIBILITY, SSL/testing snippets)
- PyPI metadata:
  - `https://pypi.org/pypi/opensearch-py/json`
  - `https://pypi.org/pypi/opensearch-py/2.6.0/json`
  - `https://pypi.org/pypi/opensearch-py/3.1.0/json`
  - `https://pypi.org/pypi/opensearch-dsl/json`
