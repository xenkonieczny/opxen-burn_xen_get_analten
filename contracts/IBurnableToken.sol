// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

/// @dev Interfejs uproszczony kontraktu XEN
interface IBurnableToken {
    /// @notice Spala tokeny z konta user
    /// @param user adres, z którego spalane są tokeny
    /// @param amount ilość tokenów do spalenia
    function burn(address user, uint256 amount) external;
}
