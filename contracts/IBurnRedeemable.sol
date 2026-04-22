// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @dev Interfejs, który musi zaimplementować każdy „redeemer”
interface IBurnRedeemable {
    /// @notice Wywoływane przez XEN token po spaleniu
    /// @param user adres użytkownika, który spalił tokeny
    /// @param amount liczba spalonych tokenów
    function onTokenBurned(address user, uint256 amount) external;
}
