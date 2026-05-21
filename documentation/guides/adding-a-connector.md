# Adding a Connector

ARIA's plugin architecture means you can add a new log connector, ITSM connector, or secret store without touching any agent code. This guide walks through adding a log connector as an example.

## 1. Identify the interface

All log connectors implement `LogStoreInterface` from `core/interfaces/log_store.py`:

```python
class LogStoreInterface(ABC):
    @abstractmethod
    def query(
        self,
        service: str,
        start: datetime,
        end: datetime,
        keywords: list[str],
    ) -> list[LogLine]: ...
```

Your implementation must satisfy this contract. Nothing else.

## 2. Create the implementation file

Put your implementation in the right subtree:

- **On-premise (SSH-accessible)**: configure `SSHLogConnector` (`implementations/clusters/onprem/log_connector.py`) with your log directories and SSH key secret — no new file needed for most on-prem platforms.
- **Cloud-native**: create `implementations/clusters/cloud/<platform>/log_connector.py`. For example, a Splunk Cloud connector would live at `implementations/clusters/cloud/splunk/log_connector.py`.

```python
from core.interfaces.log_store import LogStoreInterface
from core.models import LogLine

class SplunkLogStore(LogStoreInterface):
    def __init__(self, endpoint: str, token: str) -> None:
        self._endpoint = endpoint
        self._token = token

    def query(self, service, start, end, keywords):
        # call Splunk search API
        ...
        return [LogLine(...) for result in results]
```

Keep the constructor narrow — accept only what the connector needs. Retrieve credentials via `VaultInterface`, not by accepting raw secret strings.

## 3. Raise the right exceptions

Use the domain exceptions from `core/exceptions.py`:

| Situation | Exception |
|---|---|
| Backend unreachable | `LogStoreUnavailableError` |
| Query timed out | `LogQueryTimeoutError` |

Do not raise generic `Exception` or let HTTP library exceptions propagate — callers depend on these specific types.

## 4. Write unit tests

Test your connector in `tests/unit/` using a mocked HTTP client — no real network calls. Cover at minimum:

- Successful query returning results
- Empty results (not an error — return `[]`)
- Backend unavailable → `LogStoreUnavailableError`
- Query timeout → `LogQueryTimeoutError`

## 5. Register the connector

Agent 2 routes to connectors based on `PlatformTag`. Add your connector to the registry in `core/agents/log_finder.py` (or wherever the registry lives when Agent 2 is implemented).

## Checklist

- [ ] Implements the correct ABC from `core/interfaces/`
- [ ] Credentials retrieved via `VaultInterface`, not hardcoded
- [ ] Raises only domain exceptions from `core/exceptions.py`
- [ ] Unit tests with mocked network — no real services required
- [ ] Registered in the connector registry for the relevant `PlatformTag`
