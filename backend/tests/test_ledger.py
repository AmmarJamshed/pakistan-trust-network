"""Ledger unit tests — genesis, chaining, tamper detection."""

from datetime import datetime, timezone

from app.ledger.service import GENESIS_PREV_HASH, LedgerService, compute_block_hash
from app.security.crypto import merkle_root, sha256_hex


def test_compute_block_hash_deterministic():
    ts = datetime(2026, 8, 16, tzinfo=timezone.utc)
    h1 = compute_block_hash(0, ts, GENESIS_PREV_HASH, merkle_root([]), "v1", [])
    h2 = compute_block_hash(0, ts, GENESIS_PREV_HASH, merkle_root([]), "v1", [])
    assert h1 == h2
    assert len(h1) == 64


def test_merkle_root_empty():
    assert merkle_root([]) == sha256_hex("empty")


def test_genesis_and_chain(db_session):
    svc = LedgerService(db_session)
    genesis = svc.ensure_genesis()
    assert genesis.index == 0
    assert genesis.previous_hash == GENESIS_PREV_HASH

    tx = svc.append_transaction(
        transaction_type="CREDENTIAL_ISSUED",
        issuer_id="ptn:org:test",
        credential_id="ptn:cred:test",
        credential_hash="a" * 64,
        digital_signature="sig",
        metadata_hash="b" * 64,
        payload={},
    )
    assert tx.block_index == 1

    result = svc.verify_chain()
    assert result["valid"] is True
    assert result["height"] >= 1


def test_tampering_detected(db_session):
    svc = LedgerService(db_session)
    svc.ensure_genesis()
    svc.append_transaction(
        transaction_type="CREDENTIAL_ISSUED",
        issuer_id="ptn:org:test",
        credential_id="ptn:cred:x",
        credential_hash="c" * 64,
        digital_signature="sig",
        metadata_hash="d" * 64,
    )
    block = svc.get_block(1)
    assert block is not None
    block.block_hash = "0" * 64
    db_session.flush()

    result = svc.verify_chain()
    assert result["valid"] is False
    assert len(result["errors"]) > 0
