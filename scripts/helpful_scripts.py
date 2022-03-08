from re import I
from brownie import (
    accounts,
    network,
    config,
    MockV3Aggregator,
    Contract,
    VRFCoordinatorMock,
    LinkToken,
    interface,
)

LOCAL_BLOCKCHAIN_ENVIROMENT = {"development", "ganache-local"}
FORKED_BLOCKCHAIN_ENVIRONMENT = {"mainnet-fork-dev"}


def get_account(index=None, id=None):
    if index:
        return accounts[index]
    if id:
        return accounts.load(id)
    if (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIROMENT
        or network.show_active() in FORKED_BLOCKCHAIN_ENVIRONMENT
    ):
        return accounts[0]
    return accounts.add(config["wallets"]["from_key"])


contract_to_mock = {
    "eth_usd_price_feed": MockV3Aggregator,
    "vrf_coordinator": VRFCoordinatorMock,
    "link_token": LinkToken,
}

DECIMAL = 8
INITIAL_VALUE = 200000000000


def deploy_mock(decimal=DECIMAL, initial_value=INITIAL_VALUE):
    account = get_account()
    mock_price_feed = MockV3Aggregator.deploy(decimal, initial_value, {"from": account})
    mock_link_token = LinkToken.deploy({"from": account})
    mock_vrf_coordinator = VRFCoordinatorMock.deploy(
        mock_link_token.address, {"from": account}
    )
    print("Deployed")


def get_contract(contract_name):
    """this fucn will grab the contract address from bownie config if defined
    otherwise it will deploy a mock version of that contract, and returns that mock contract.

    args:
        contract_name(string)
    returns :
    brownie.network.contract.projectContract, most recents deployed version of this contract
    """
    contract_type = contract_to_mock[contract_name]
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIROMENT:
        if len(contract_type) <= 0:
            deploy_mock()
        contract = contract_type[-1]  # MockV3Aggregator[-1]
    else:
        contract_address = config["networks"][network.show_active()][contract_name]
        # address
        # abi
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi
        )
        # MockV3Aggregator.abi
    return contract


def fund_with_link(
    contract_address, account=None, link_token=None, amount=100000000000000000
):  # 0.1Link
    account = account if account else get_account()
    link_token = link_token if link_token else get_contract("link_token")
    tx = link_token.transfer(contract_address, amount, {"from": account})
    # link_token_contract = interface.LinkTokenInterface(link_token.address)
    # tx = link_token_contract.transfer(contract_address, amount, {"from": account})
    tx.wait(1)
    print("Funded !")
    return tx
