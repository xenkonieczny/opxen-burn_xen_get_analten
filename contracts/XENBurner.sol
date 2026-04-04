// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

import "./IBurnRedeemable.sol";
import "./IBurnableToken.sol";

/// @title XENBurner — proxy do spalania XEN z obsługą IBurnRedeemable
contract XENBurner is IBurnRedeemable {
    /// @notice Adres głównego kontraktu XEN na Optimism
    address public immutable xen;

    constructor(address _xen) {
        xen = _xen;
    }

    /// @notice Entry-point dla front-endu: spala `amount` tokenów z msg.sender
    function burn(uint256 amount) external {
        IBurnableToken(xen).burn(msg.sender, amount);
    }

    /// @notice callback wywołany przez XEN po spaleniu
    /// @dev Nie musimy w nim nic robić, ale musi istnieć
    function onTokenBurned(address /*user*/, uint256 /*amount*/) external pure override {
        // noop
    }

    /// @notice Umożliwia `supportsInterface` zwrócić prawdziwe IBurnRedeemable interfaceId
    function supportsInterface(bytes4 interfaceId) external pure returns (bool) {
    return interfaceId == type(IBurnRedeemable).interfaceId
        || interfaceId == 0x01ffc9a7; // ERC165 interfaceId
}
}
