import pytest
from pathlib import Path
from core.models import PlatformTag
from implementations.knowledge_base.file_kb import FileKnowledgeBase

@pytest.fixture
def runbook_dir():
    return "tests/fixtures/knowledge_base"

@pytest.fixture
def kb(runbook_dir):
    return FileKnowledgeBase(runbook_dir)

class TestFileKnowledgeBaseInit:
    def test_loads_fixture_files(self, kb):
        """Verify that fixture runbook files are loaded on initialisation."""
        # Updated to 5 to account for the 3 new Sprint 4 runbooks
        assert len(kb._files) == 5

class TestFileKnowledgeBaseQueries:
    def test_get_service_hints(self, kb):
        hints = kb.get_service_hints("cdp-master-01", "HDFS Namenode is down")
        assert any("hdfs" in h for h in hints)

    def test_uc1_terraform_log_hints(self, kb):
        """Verify explicit acceptance criteria for issue #60."""
        
        # 1. Assert Master Node returns HDFS log paths and target OOM keyword strings
        master_hints = kb.get_log_hints("cdp-master-01", PlatformTag.CDP)
        assert any("/var/log/hadoop/hdfs" in p for p in master_hints.log_paths)
        assert "OutOfMemory" in master_hints.keywords

        # 2. Check Bus Data Node mapping
        bus_hints = kb.get_log_hints("cdp-bus-01", PlatformTag.CDP)
        assert any("/var/log/kafka" in p for p in bus_hints.log_paths)
        assert "timeout" in bus_hints.keywords

        # 3. Check Utility Node mapping
        utility_hints = kb.get_log_hints("cdp-utility-01", PlatformTag.CDP)
        assert any("/var/log/hive" in p for p in utility_hints.log_paths)
        assert "Hive" in utility_hints.keywords