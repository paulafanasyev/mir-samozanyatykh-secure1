from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
SV = (ROOT / "app/api/svetlana.py").read_text(encoding="utf-8")
CFG = (ROOT / "app/core/config.py").read_text(encoding="utf-8")
SCHEMA = (ROOT / "app/schemas/contracts.py").read_text(encoding="utf-8")
SERVER = (ROOT / "server.py").read_text(encoding="utf-8")


def test_all_changed_python_files_parse():
    for path in [ROOT / "app/api/svetlana.py", ROOT / "app/schemas/contracts.py", ROOT / "app/core/config.py"]:
        ast.parse(path.read_text(encoding="utf-8"))


def test_offline_model_defaults_to_loopback():
    assert "OFFLINE_AI_ALLOW_REMOTE: bool = False" in CFG
    assert "_offline_ai_url_is_local" in SV
    assert "offline AI URL is not local" in SV


def test_document_generation_has_separate_rate_limit():
    assert "SVETLANA_DOCUMENTS_PER_HOUR" in CFG
    assert '"svetlana_document_generated"' in SV
    assert "status_code=429" in SV


def test_contract_template_id_matches_string_workflow():
    assert "template_id: str" in SCHEMA
    assert 'if template_type not in CONTRACT_TYPES' in SV


def test_legacy_admin_tier_endpoint_validates_allowlist():
    block = SERVER[SERVER.index('async def update_user_tier'):SERVER.index('# ============ HTML ROUTES', SERVER.index('async def update_user_tier'))]
    assert "tier not in allowed_tiers" in block
