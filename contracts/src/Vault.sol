// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract Vault {
    address public owner;
    
    event Deposit(address indexed user, uint256 amount);
    event EmergencyExitTriggered(address indexed user, string reason);

    constructor() {
        // The wallet that deploys this contract becomes the "owner" (Your Python AI)
        owner = msg.sender;
    }

    // Security check: Only the AI can trigger a rescue
    modifier onlyOwner() {
        require(msg.sender == owner, "Not authorized: Watchtower AI only");
        _;
    }

    // Users deposit their vulnerable tokens here
    function deposit() external payable {
        emit Deposit(msg.sender, msg.value);
    }

    // The function the Python AI calls when Risk Score hits 90%
    function emergencyExit(address user) external onlyOwner {
        // In a production environment, this function would interact with a Mantle DEX 
        // to instantly swap the user's tokens for stable USDC before the rug-pull happens.
        
        // For this portfolio prototype, we emit the rescue event to prove the AI trigger works!
        emit EmergencyExitTriggered(user, "High Risk: Malicious Developer Activity Detected");
    }
}