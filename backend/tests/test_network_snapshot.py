from app.ledger.service import LedgerService
from app.network.snapshot import export_snapshot, import_snapshot
from tests.test_credentials import _setup_issuer_holder


def test_snapshot_roundtrip_preserves_proof(db_session):
    org, holder = _setup_issuer_holder(db_session)
    from app.credentials.service import CredentialService

    svc = CredentialService(db_session)
    cred = svc.issue(
        organization=org,
        holder=holder,
        type_code="UniversityDegree",
        title="BS Computer Science",
        credential_subject={"degree": "BS Computer Science"},
    )
    snap = export_snapshot(db_session)
    assert snap["credentials"]
    assert snap["blocks"]
    assert all("encrypted_private_key" not in i for i in snap["identities"])
    assert all("password" not in str(c).lower() for c in snap["credentials"])

    imported = import_snapshot(db_session, snap)
    assert imported["credentials"] == 0  # already present
    result = svc.verify(cred.credential_id)
    assert result["overall"] == "VERIFIED"
    chain = LedgerService(db_session).verify_chain()
    assert chain["valid"] is True
