// SPDX-License-Identifier: MIT
pragma solidity ^0.6.0;

import "@chainlink/contracts/src/v0.6/interfaces/AggregatorV3Interface.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@chainlink/contracts/src/v0.6/VRFConsumerBase.sol";

contract Lottery is VRFConsumerBase, Ownable {
    address payable[] public players;
    uint256 usdEntryFee;
    uint256 public fee;
    bytes32 public keyHash;
    address payable public recentWinner;
    uint256 public randomness;
    event RequestedRandomness(bytes32 requestId);

    AggregatorV3Interface internal ethUsdPriceFeed;
    enum LOTTERY_STATE {
        OPEN,
        CLOSED,
        CALCULATING_WINNER
    }
    LOTTERY_STATE public lottery_state;

    //set when contract deployed
    constructor(
        address _priceFeedAddress,
        address _vrfcooardinator,
        address _link,
        uint256 _fee,
        bytes32 _keyHash
    ) public VRFConsumerBase(_vrfcooardinator, _link) {
        usdEntryFee = 50 * (10**18);
        ethUsdPriceFeed = AggregatorV3Interface(_priceFeedAddress);
        lottery_state = LOTTERY_STATE.CLOSED;
        fee = _fee;
        keyHash = _keyHash;
    }

    function enterPlayer() public payable {
        require(
            lottery_state == LOTTERY_STATE.OPEN,
            "Lottery is not yet started"
        );
        //$50 minimum
        require(msg.value >= getEntranceFee(), "Not enough ETH!");
        players.push(msg.sender);
    }

    function getEntranceFee() public view returns (uint256) {
        //?
        (, int256 price, , , ) = ethUsdPriceFeed.latestRoundData();
        //2000$ 1 eth
        //$50 eth ?
        //50/2000
        uint256 adjustedPrice = uint256(price) * (10**10);
        uint256 costToEnter = (usdEntryFee * 10**18) / adjustedPrice;
        return costToEnter;
    }

    function startLottery() public onlyOwner {
        require(
            lottery_state == LOTTERY_STATE.CLOSED,
            "cant start new lottery"
        );
        lottery_state = LOTTERY_STATE.OPEN;
    }

    function endLottery() public payable onlyOwner {
        lottery_state = LOTTERY_STATE.CALCULATING_WINNER;
        bytes32 requestId = requestRandomness(keyHash, fee);
        emit RequestedRandomness(requestId);
    }

    function fulfillRandomness(bytes32 _requestId, uint256 _randomness)
        internal
        override
    {
        require(
            lottery_state == LOTTERY_STATE.CALCULATING_WINNER,
            "you not there yet!"
        );
        require(_randomness > 0, "randomeness is not found");
        uint256 indexOfWinner = _randomness % players.length;
        recentWinner = players[indexOfWinner];
        recentWinner.transfer(address(this).balance);

        //reset lottery
        randomness = _randomness;
        players = new address payable[](0);
        lottery_state = LOTTERY_STATE.CLOSED;
    }
}
