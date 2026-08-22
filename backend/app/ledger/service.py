from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database.models import LedgerBlock, LedgerTransaction
from app.security.crypto import canonical_json, merkle_root, sha256_hex


GENESIS_PREV_HASH = "0" * 64
# Shared by every local node so Git-synced blocks link to the same genesis.
CANONICAL_GENESIS_TIME = datetime(2026, 8, 16, 0, 0, 0, tzinfo=timezone.utc)


def _tx_id() -> str:
    return f"PTN-TX-{secrets.token_hex(8).upper()}"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(ts: datetime) -> str:
    """Normalize datetimes so SQLite round-trips do not break hashes."""
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc).isoformat()


def compute_block_hash(
    index: int,
    timestamp: datetime,
    previous_hash: str,
    merkle: str,
    validator: str,
    tx_ids: list[str],
) -> str:
    payload = {
        "index": index,
        "timestamp": _iso(timestamp),
        "previous_hash": previous_hash,
        "merkle_root": merkle,
        "validator": validator,
        "transactions": tx_ids,
    }
    return sha256_hex(canonical_json(payload))


class LedgerService:
    """Permissioned, cryptographically linked append-only ledger."""

    def __init__(self, db: Session):
        self.db = db

    def ensure_genesis(self) -> LedgerBlock:
        existing = self.db.scalar(select(LedgerBlock).where(LedgerBlock.index == 0))
        if existing:
            return existing

        ts = CANONICAL_GENESIS_TIME
        merkle = merkle_root([])
        block_hash = compute_block_hash(
            0, ts, GENESIS_PREV_HASH, merkle, settings.ledger_validator_id, []
        )
        block = LedgerBlock(
            index=0,
            timestamp=ts,
            previous_hash=GENESIS_PREV_HASH,
            merkle_root=merkle,
            validator=settings.ledger_validator_id,
            block_hash=block_hash,
            transaction_count=0,
        )
        self.db.add(block)
        self.db.flush()
        return block

    def get_latest_block(self) -> LedgerBlock | None:
        return self.db.scalar(select(LedgerBlock).order_by(LedgerBlock.index.desc()).limit(1))

    def append_transaction(
        self,
        *,
        transaction_type: str,
        issuer_id: str | None,
        credential_id: str | None,
        credential_hash: str | None,
        digital_signature: str | None,
        metadata_hash: str | None,
        payload: dict[str, Any] | None = None,
        auto_mine: bool = True,
    ) -> LedgerTransaction:
        self.ensure_genesis()
        tx = LedgerTransaction(
            transaction_id=_tx_id(),
            transaction_type=transaction_type,
            issuer_id=issuer_id,
            credential_id=credential_id,
            credential_hash=credential_hash,
            timestamp=_utcnow(),
            digital_signature=digital_signature,
            metadata_hash=metadata_hash,
            payload=payload or {},
        )
        self.db.add(tx)
        self.db.flush()

        if auto_mine:
            self.mine_pending_block([tx])
        return tx

    def mine_pending_block(self, transactions: list[LedgerTransaction]) -> LedgerBlock:
        latest = self.get_latest_block()
        if latest is None:
            latest = self.ensure_genesis()

        index = latest.index + 1
        ts = _utcnow()
        leaf_hashes = [
            sha256_hex(
                canonical_json(
                    {
                        "transaction_id": t.transaction_id,
                        "transaction_type": t.transaction_type,
                        "issuer_id": t.issuer_id,
                        "credential_id": t.credential_id,
                        "credential_hash": t.credential_hash,
                        "timestamp": _iso(t.timestamp),
                        "digital_signature": t.digital_signature,
                        "metadata_hash": t.metadata_hash,
                    }
                )
            )
            for t in transactions
        ]
        merkle = merkle_root(leaf_hashes)
        tx_ids = [t.transaction_id for t in transactions]
        block_hash = compute_block_hash(
            index, ts, latest.block_hash, merkle, settings.ledger_validator_id, tx_ids
        )
        block = LedgerBlock(
            index=index,
            timestamp=ts,
            previous_hash=latest.block_hash,
            merkle_root=merkle,
            validator=settings.ledger_validator_id,
            block_hash=block_hash,
            transaction_count=len(transactions),
        )
        self.db.add(block)
        self.db.flush()

        for t in transactions:
            t.block_id = block.id
            t.block_index = block.index

        self.db.flush()
        return block

    def verify_chain(self) -> dict[str, Any]:
        blocks = list(self.db.scalars(select(LedgerBlock).order_by(LedgerBlock.index.asc())).all())
        if not blocks:
            return {"valid": True, "height": 0, "message": "Empty ledger"}

        errors: list[str] = []
        for i, block in enumerate(blocks):
            if block.index != i:
                errors.append(f"Block index mismatch at position {i}: found {block.index}")

            if i == 0:
                if block.previous_hash != GENESIS_PREV_HASH:
                    errors.append("Genesis previous_hash invalid")
            else:
                prev = blocks[i - 1]
                if block.previous_hash != prev.block_hash:
                    errors.append(f"Broken link at block {block.index}")

            txs = list(
                self.db.scalars(
                    select(LedgerTransaction).where(LedgerTransaction.block_id == block.id)
                ).all()
            )
            leaf_hashes = [
                sha256_hex(
                    canonical_json(
                        {
                            "transaction_id": t.transaction_id,
                            "transaction_type": t.transaction_type,
                            "issuer_id": t.issuer_id,
                            "credential_id": t.credential_id,
                            "credential_hash": t.credential_hash,
                            "timestamp": _iso(t.timestamp),
                            "digital_signature": t.digital_signature,
                            "metadata_hash": t.metadata_hash,
                        }
                    )
                )
                for t in txs
            ]
            if block.index == 0 and not txs:
                expected_merkle = block.merkle_root
            else:
                expected_merkle = merkle_root(leaf_hashes)
            if expected_merkle != block.merkle_root:
                errors.append(f"Merkle root mismatch at block {block.index}")

            expected_hash = compute_block_hash(
                block.index,
                block.timestamp,
                block.previous_hash,
                block.merkle_root,
                block.validator,
                [t.transaction_id for t in txs],
            )
            if expected_hash != block.block_hash:
                errors.append(f"Block hash mismatch at block {block.index}")

        return {
            "valid": len(errors) == 0,
            "height": blocks[-1].index if blocks else 0,
            "block_count": len(blocks),
            "errors": errors,
            "message": "Chain integrity verified" if not errors else "Tampering detected",
        }

    def get_unattached_transactions(self) -> list[LedgerTransaction]:
        return list(
            self.db.scalars(
                select(LedgerTransaction).where(LedgerTransaction.block_id.is_(None))
            ).all()
        )

    def delete_blocks_from(self, index: int) -> list[str]:
        """Drop local blocks at and after index. Transactions are detached, not deleted."""
        blocks = list(
            self.db.scalars(select(LedgerBlock).where(LedgerBlock.index >= index)).all()
        )
        dropped = [b.block_hash for b in blocks]
        for block in blocks:
            txs = list(
                self.db.scalars(
                    select(LedgerTransaction).where(LedgerTransaction.block_id == block.id)
                ).all()
            )
            for tx in txs:
                tx.block_id = None
                tx.block_index = None
            self.db.delete(block)
        self.db.flush()
        return dropped

    def import_block(self, payload: dict[str, Any]) -> LedgerBlock:
        existing = self.get_block(int(payload["index"]))
        if existing:
            return existing
        ts = datetime.fromisoformat(payload["timestamp"])
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        block = LedgerBlock(
            index=int(payload["index"]),
            timestamp=ts,
            previous_hash=payload["previous_hash"],
            merkle_root=payload["merkle_root"],
            validator=payload["validator"],
            block_hash=payload["block_hash"],
            transaction_count=int(payload.get("transaction_count") or len(payload.get("transactions") or [])),
        )
        self.db.add(block)
        self.db.flush()
        for txp in payload.get("transactions") or []:
            self.import_transaction(txp, block)
        self.db.flush()
        return block

    def import_transaction(self, payload: dict[str, Any], block: LedgerBlock | None) -> LedgerTransaction:
        existing = self.get_transaction(payload["transaction_id"])
        if existing:
            if block and existing.block_id is None:
                existing.block_id = block.id
                existing.block_index = block.index
            return existing
        ts = datetime.fromisoformat(payload["timestamp"])
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        tx = LedgerTransaction(
            transaction_id=payload["transaction_id"],
            transaction_type=payload["transaction_type"],
            issuer_id=payload.get("issuer_id"),
            credential_id=payload.get("credential_id"),
            credential_hash=payload.get("credential_hash"),
            timestamp=ts,
            digital_signature=payload.get("digital_signature"),
            metadata_hash=payload.get("metadata_hash"),
            payload=payload.get("payload") or {},
            block_id=block.id if block else None,
            block_index=block.index if block else None,
        )
        self.db.add(tx)
        self.db.flush()
        return tx

    def export_block(self, block: LedgerBlock) -> dict[str, Any]:
        txs = list(
            self.db.scalars(
                select(LedgerTransaction).where(LedgerTransaction.block_id == block.id)
            ).all()
        )
        return {
            "index": block.index,
            "timestamp": _iso(block.timestamp),
            "previous_hash": block.previous_hash,
            "merkle_root": block.merkle_root,
            "validator": block.validator,
            "block_hash": block.block_hash,
            "transaction_count": block.transaction_count,
            "transactions": [
                {
                    "transaction_id": t.transaction_id,
                    "transaction_type": t.transaction_type,
                    "issuer_id": t.issuer_id,
                    "credential_id": t.credential_id,
                    "credential_hash": t.credential_hash,
                    "timestamp": _iso(t.timestamp),
                    "digital_signature": t.digital_signature,
                    "metadata_hash": t.metadata_hash,
                    "payload": t.payload or {},
                }
                for t in txs
            ],
        }

    def get_block(self, height: int) -> LedgerBlock | None:
        return self.db.scalar(select(LedgerBlock).where(LedgerBlock.index == height))

    def get_transaction(self, transaction_id: str) -> LedgerTransaction | None:
        return self.db.scalar(
            select(LedgerTransaction).where(LedgerTransaction.transaction_id == transaction_id)
        )

    def search(self, query: str, limit: int = 50) -> dict[str, Any]:
        q = query.strip()
        blocks: list[LedgerBlock] = []
        txs: list[LedgerTransaction] = []

        if q.isdigit():
            b = self.get_block(int(q))
            if b:
                blocks.append(b)

        b_hash = self.db.scalar(select(LedgerBlock).where(LedgerBlock.block_hash == q.lower()))
        if b_hash:
            blocks.append(b_hash)

        tx = self.get_transaction(q.upper() if q.upper().startswith("PTN-TX-") else q)
        if not tx:
            tx = self.db.scalar(
                select(LedgerTransaction).where(LedgerTransaction.credential_id == q)
            )
        if tx:
            txs.append(tx)

        # Partial search
        if not blocks and not txs:
            txs = list(
                self.db.scalars(
                    select(LedgerTransaction)
                    .where(
                        (LedgerTransaction.transaction_id.ilike(f"%{q}%"))
                        | (LedgerTransaction.credential_id.ilike(f"%{q}%"))
                    )
                    .limit(limit)
                ).all()
            )
            blocks = list(
                self.db.scalars(
                    select(LedgerBlock).where(LedgerBlock.block_hash.ilike(f"%{q}%")).limit(limit)
                ).all()
            )

        return {"blocks": blocks, "transactions": txs}
