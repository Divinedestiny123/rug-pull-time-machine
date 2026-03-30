// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// We need an interface to interact with standard ERC20 tokens (like USDT or WETH)
interface IERC20 {
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
    function transfer(address recipient, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract PredictiveShieldVault {
    // 1. State Variables
    address public backendOperator; // The wallet address controlled by your Python AI
    
    // Tracks how much of which token each user has in the vault
    // User Address => Token Address => Amount
    mapping(address => mapping(address => uint256)) public balances;

    // 2. Events (The logs your Python script and Frontend will listen to)
    event Deposited(address indexed user, address indexed token, uint256 amount);
    event Withdrawn(address indexed user, address indexed token, uint256 amount);
    event EmergencyExitExecuted(address indexed user, address indexed token, uint256 amount);

    // 3. Modifiers (Security checks)
    modifier onlyOperator() {
        require(msg.sender == backendOperator, "Only the AI Backend can execute this");
        _;
    }

    // 4. Constructor (Runs once when deployed)
    constructor(address _operatorWallet) {
        backendOperator = _operatorWallet; // You will set this to your Python script's wallet
    }

    // 5. Core Functions

    // Users call this to lock their tokens in the shield
    function deposit(address _token, uint256 _amount) external {
        require(_amount > 0, "Amount must be greater than 0");
        
        // Transfer tokens from the user to this contract
        IERC20(_token).transferFrom(msg.sender, address(this), _amount);
        
        // Update their balance internally
        balances[msg.sender][_token] += _amount;
        
        emit Deposited(msg.sender, _token, _amount);
    }

    // Users can manually withdraw at any time if they feel safe
    function withdraw(address _token, uint256 _amount) external {
        require(balances[msg.sender][_token] >= _amount, "Insufficient balance");
        
        // Deduct from internal ledger first (security best practice)
        balances[msg.sender][_token] -= _amount;
        
        // Send tokens back to the user
        IERC20(_token).transfer(msg.sender, _amount);
        
        emit Withdrawn(msg.sender, _token, _amount);
    }

    // THE GOD-MODE FUNCTION: Only your Python backend can call this
    function emergencyExit(address _user, address _tokenToSell, uint256 _amount) external onlyOperator {
        require(balances[_user][_tokenToSell] >= _amount, "User does not have enough tokens");

        balances[_user][_tokenToSell] -= _amount;

        // In a V2, this function would interact with a DEX (like Uniswap/Mantle Swap)
        // to automatically sell the _tokenToSell for a stablecoin. 
        // For V1, we will simply transfer the endangered token back to the user's secure cold wallet, 
        // or trigger the sell logic. Let's send it back to them for now as a baseline rescue.
        IERC20(_tokenToSell).transfer(_user, _amount);

        emit EmergencyExitExecuted(_user, _tokenToSell, _amount);
    }
}