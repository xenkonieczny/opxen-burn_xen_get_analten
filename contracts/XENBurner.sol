// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "./IBurnRedeemable.sol";
import "./IBurnableToken.sol";

/// @title XENBurner — wrapper do spalania XEN z obsługą IBurnRedeemable
contract XENBurner is IBurnRedeemable {
    /// @notice Adres głównego kontraktu XEN na Optimism
    address public immutable xen;

    /// @notice Zsumowane spalenia per użytkownik per epoka (1 dzień UTC)
    mapping(address => mapping(uint256 => uint256)) public burnedInEpoch;

    /// @notice Zsumowane spalenia per użytkownik (all-time)
    mapping(address => uint256) public totalBurned;

    /// @notice Globalna suma spaleń
    uint256 public globalBurned;

    /// @dev Reentrancy guard
    uint256 private _locked = 1;

    event Burned(address indexed user, uint256 amount, uint256 indexed epoch);

    modifier nonReentrant() {
        require(_locked == 1, "reentrant");
        _locked = 2;
        _;
        _locked = 1;
    }

    constructor(address _xen) {
        require(_xen != address(0), "xen=0");
        xen = _xen;
    }

    /// @notice Entry-point dla front-endu: spala `amount` tokenów z msg.sender
    function burn(uint256 amount) external nonReentrant {
        require(amount > 0, "amount=0");
        IBurnableToken(xen).burn(msg.sender, amount);
    }

    /// @notice callback wywołany przez XEN po spaleniu
    function onTokenBurned(address user, uint256 amount) external override {
        require(msg.sender == xen, "only XEN");
        uint256 epoch = block.timestamp / 1 days;
        burnedInEpoch[user][epoch] += amount;
        totalBurned[user] += amount;
        globalBurned += amount;
        emit Burned(user, amount, epoch);
    }

    /// @notice ERC-165 — ogłasza wsparcie IBurnRedeemable
    function supportsInterface(bytes4 interfaceId) external pure returns (bool) {
        return interfaceId == type(IBurnRedeemable).interfaceId
            || interfaceId == 0x01ffc9a7; // ERC-165
    }
}
