// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title CredentialPassport
 * @notice Stores document hashes for verifiable credential management
 * @dev Deployed on Polygon zkEVM for low-cost transactions
 */
contract CredentialPassport {
    struct Credential {
        bytes32 documentHash;
        address issuedBy;
        uint256 issuedAt;
        bool isVerified;
    }

    // studentId => documentType => Credential
    mapping(bytes32 => mapping(string => Credential)) public credentials;

    // Authorized institutions
    mapping(address => bool) public authorizedInstitutions;

    address public owner;

    event CredentialStored(bytes32 indexed studentId, string documentType, bytes32 documentHash);
    event CredentialVerified(bytes32 indexed studentId, string documentType, address verifiedBy);
    event InstitutionAuthorized(address indexed institution);
    event InstitutionRevoked(address indexed institution);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier onlyAuthorized() {
        require(authorizedInstitutions[msg.sender], "Not authorized institution");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function authorizeInstitution(address _institution) external onlyOwner {
        authorizedInstitutions[_institution] = true;
        emit InstitutionAuthorized(_institution);
    }

    function revokeInstitution(address _institution) external onlyOwner {
        authorizedInstitutions[_institution] = false;
        emit InstitutionRevoked(_institution);
    }

    function storeCredential(
        bytes32 _studentId,
        string calldata _documentType,
        bytes32 _documentHash
    ) external onlyAuthorized {
        credentials[_studentId][_documentType] = Credential({
            documentHash: _documentHash,
            issuedBy: msg.sender,
            issuedAt: block.timestamp,
            isVerified: true
        });

        emit CredentialStored(_studentId, _documentType, _documentHash);
    }

    function verifyCredential(
        bytes32 _studentId,
        string calldata _documentType,
        bytes32 _documentHash
    ) external view returns (bool) {
        Credential memory cred = credentials[_studentId][_documentType];
        return cred.isVerified && cred.documentHash == _documentHash;
    }
}
