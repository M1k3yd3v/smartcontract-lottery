from ast import excepthandler
from asyncio import exceptions
from brownie import Lottery, accounts, network, config, web3, exceptions
from web3 import Web3
import pytest
from scripts.deploy_lottery import deploy_lottery
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIROMENT,
    fund_with_link,
    get_account,
    get_contract,
)


def test_get_entrance_fee():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIROMENT:
        pytest.skip()
    tx = deploy_lottery()
    print(tx.getEntranceFee())
    assert tx.getEntranceFee() > Web3.toWei(0.022, "ether")


def test_cant_enter_unless_started():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIROMENT:
        pytest.skip()
    account = accounts[0]
    lottery = deploy_lottery()
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enterPlayer({"from": account, "value": lottery.getEntranceFee()})


def test_can_start_and_enter_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIROMENT:
        pytest.skip()
    account = get_account()
    lottery = deploy_lottery()
    lottery.startLottery({"from": account})
    lottery.enterPlayer({"from": account, "value": lottery.getEntranceFee()})
    # assert
    assert lottery.players(0) == account


def test_can_end_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIROMENT:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    fund_with_link(lottery)
    lottery.enterPlayer({"from": account, "value": lottery.getEntranceFee()})
    lottery.endLottery({"from": account})
    assert lottery.lottery_state() == 2


def test_can_pick_winner_correctly():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIROMENT:
        pytest.skip()
    account = get_account()
    lottery = deploy_lottery()
    lottery.startLottery({"from": account})
    lottery.enterPlayer({"from": account, "value": lottery.getEntranceFee()})
    lottery.enterPlayer(
        {"from": get_account(index=1), "value": lottery.getEntranceFee()}
    )
    lottery.enterPlayer(
        {"from": get_account(index=2), "value": lottery.getEntranceFee()}
    )
    fund_with_link(lottery)
    starting_balance_account = account.balance()
    balance_of_lottery = lottery.balance()
    transaction = lottery.endLottery()
    request_Id = transaction.events["RequestedRandomness"]["requestId"]
    STATIC_RNG = 777
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_Id, STATIC_RNG, lottery.address, {"from": account}
    )
    # 777%3 = 0
    assert lottery.recentWinner() == account.address
    assert lottery.balance() == 0
    assert account.balance() == starting_balance_account + balance_of_lottery
