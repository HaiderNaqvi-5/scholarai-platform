# ScholarAI — Blockchain Design

> **Network:** Polygon zkEVM (Ethereum Layer-2)  
> **Language:** Solidity 0.8+  
> **Toolchain:** Hardhat

---

## 1. Design Rationale

| Decision | Justification |
|---|---|
| **Polygon zkEVM** over Ethereum mainnet | Gas costs $0.01–0.05/tx vs $5–50 on L1 |
| **Polygon zkEVM** over other L2s | EVM-compatible, ZK proof security, production-ready |
| **On-chain hashes only** (not documents) | Privacy preservation; documents stay off-chain |
| **No wallet required for students** | Platform manages signing via backend custodial key |

---

## 2. Smart Contract: `CredentialPassport.sol`

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";

contract CredentialPassport is AccessControl {
    bytes32 public constant INSTITUTION_ROLE = keccak256("INSTITUTION");

    struct Credential {
        bytes32 documentHash;
        address institution;
        uint256 timestamp;
        bool isVerified;
    }

    // studentId => documentHash => Credential
    mapping(bytes32 => mapping(bytes32 => Credential)) public credentials;

    event CredentialStored(bytes32 indexed studentId, bytes32 indexed docHash, address institution);

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }

    function storeCredentialHash(
        bytes32 studentId,
        bytes32 docHash
    ) external onlyRole(INSTITUTION_ROLE) {
        credentials[studentId][docHash] = Credential({
            documentHash: docHash,
            institution: msg.sender,
            timestamp: block.timestamp,
            isVerified: true
        });
        emit CredentialStored(studentId, docHash, msg.sender);
    }

    function verifyCredential(
        bytes32 studentId,
        bytes32 docHash
    ) external view returns (bool verified, address institution, uint256 timestamp) {
        Credential memory cred = credentials[studentId][docHash];
        return (cred.isVerified, cred.institution, cred.timestamp);
    }

    function addInstitution(address inst) external onlyRole(DEFAULT_ADMIN_ROLE) {
        _grantRole(INSTITUTION_ROLE, inst);
    }
}
```

---

## 3. Verification Flow

1. Student uploads document (PDF) via platform UI
2. Backend generates SHA-256 hash of the file  
3. Platform sends verification request to institution
4. Institution confirms document authenticity via platform interface
5. Backend calls `storeCredentialHash(studentId, docHash)` on smart contract
6. Transaction receipt + `txHash` stored in PostgreSQL `credentials` table
7. Student sees "✓ Verified" badge on their credential

**Later, during scholarship application:**

8. Scholarship committee clicks "Verify Credential"
9. Backend calls `verifyCredential(studentId, docHash)` — read-only, no gas cost
10. Returns `{verified: true, institution: "...", timestamp: "..."}`

---

## 4. Gas Cost Estimates (Polygon zkEVM)

| Operation | Estimated Gas | Estimated Cost (USD) |
|---|---|---|
| `storeCredentialHash()` | ~50,000 gas | $0.01–0.03 |
| `verifyCredential()` | 0 (view function) | Free |
| `addInstitution()` | ~45,000 gas | $0.01–0.02 |
| Contract deployment | ~500,000 gas | $0.10–0.30 |

---

## 5. Integration Architecture

```
Student UI → FastAPI → ethers.js → Polygon zkEVM
                ↓
         PostgreSQL (store txHash)
```

- **Backend custodial wallet:** Platform holds a signing key for gas-paying operations
- **Students never need a wallet** — the platform abstracts blockchain complexity
- **Institutions** can optionally self-custody (for stronger verification guarantees)
