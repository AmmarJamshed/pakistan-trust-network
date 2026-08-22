"""Adapter interfaces for future interoperability. Do not implement fake integrations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class CredentialIssuer(ABC):
    @abstractmethod
    def issue(self, holder: str, credential_type: str, data: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class ExternalIdentityProvider(ABC):
    @abstractmethod
    def verify(self, identity_reference: str) -> dict[str, Any]:
        raise NotImplementedError


class ExternalLedger(ABC):
    @abstractmethod
    def anchor(self, credential_hash: str, metadata: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
