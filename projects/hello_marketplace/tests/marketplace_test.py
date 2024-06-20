import pytest 
from algokit_utils.beta.algorand_client import AlgorandClient, PayParams, AssetCreateParams, AssetTransferParams, PayParams, AssetOptInParams
from algokit_utils.beta.account_manager import AddressAndSigner

# from algokit_utils.beta.dispenser import Dispenser
from smart_contracts.artifacts.Marketplace.client import MarketplaceClient


import algosdk
from algosdk.atomic_transaction_composer import TransactionWithSigner
import algokit_utils



@pytest.fixture(scope="session")
def algorand() -> AlgorandClient:
    """Get an Algorand client."""
    return AlgorandClient.default_local_net()


@pytest.fixture(scope="session")
def dispenser(algorand: AlgorandClient) -> AddressAndSigner:
    """Get an account from the dispenser."""
    return algorand.account.dispenser()

@pytest.fixture(scope="session")
def creator(algorand: AlgorandClient, dispenser: AddressAndSigner) -> AddressAndSigner:
    account = algorand.account.random()

    algorand.send.payment(
        PayParams(
            sender=dispenser.address,
            receiver=account.address,
            amount=10_000_000,
        )
    ) 
    return account

# 
@pytest.fixture(scope="session")
def test_asset_id(creator: AddressAndSigner, algorand: AlgorandClient) -> int:
    sent_txn = algorand.send.asset_create(AssetCreateParams(sender= creator.address, total=10))

    return sent_txn['confirmation']["asset-index"]


@pytest.fixture(scope="session")
def digital_marketplace_client(algorand: AlgorandClient, creator: AddressAndSigner, test_asset_id: int) -> MarketplaceClient:
    client = MarketplaceClient(
        algod_client=algorand.client.algod,
        sender= creator.address,
        signer= creator.signer,
    )
 
    client.create_create_appliaction(unitaryprice=0, assetID=test_asset_id)

    return client


def test_opt_in_to_asset(digital_marketplace_client: MarketplaceClient, 
                        creator: AddressAndSigner, 
                        test_asset_id: int, 
                        algorand: AlgorandClient):
    
    # ensue get_asset_information throws an erro because the app is ot yet opted in  
    pytest.raises(algosdk.error.AlgodHTTPError, 
    lambda:  algorand.account.get_asset_information(digital_marketplace_client.app_address, test_asset_id),
    )

    # we need to send 100_000 algo for account and 100_000 for ASA MBR 
    mbr_pay_txn = algorand.transactions.payment(PayParams(
        sender=creator.address, 
        receiver=digital_marketplace_client.app_address,
        amount=200_000,
        extra_fee=1000,
    ))

    result = digital_marketplace_client.choose_asset(
        mbrPay=TransactionWithSigner(txn=mbr_pay_txn, signer=creator.signer),
        transaction_parameters=algokit_utils.TransactionParameters(
            # we are using this asset in contract, AVM need asset id 
            # maybe it will be done automatically in the future
            foreign_assets=[test_asset_id]
        ),
    )
   
    assert result.confirmed_round

    assert(algorand.account.get_asset_information(digital_marketplace_client.app_address, test_asset_id)["asset-holding"]["amount"]
           == 0
           )




# deposit the asset in the account 
def test_deposit(digital_marketplace_client: MarketplaceClient, 
                        creator: AddressAndSigner, 
                        test_asset_id: int, 
                        algorand: AlgorandClient):
    result = algorand.send.asset_transfer(
        AssetTransferParams(
            sender=creator.address,
            receiver=digital_marketplace_client.app_address,
            asset_id=test_asset_id,
            amount=3,
        )
    )

    assert result["confirmation"]
    

    assert(algorand.account.get_asset_information(digital_marketplace_client.app_address, test_asset_id)["asset-holding"]["amount"]
           == 3
           )


def test_set_price(digital_marketplace_client: MarketplaceClient):
    result = digital_marketplace_client.set_price(
        unitaryprice=1_111_000,
    )

    assert result.confirmed_round

# def test_buy(digital_marketplace_client: MarketplaceClient, 
#             creator: AddressAndSigner, 
#             test_asset_id: int, 
#             algorand: AlgorandClient,
#             dispenser: AddressAndSigner):  
    
#     # creaate a new account to buy
#     buyer = algorand.account.random()

#     # use the dispenser to fund 
#     algorand.send.payment(
#         PayParams(
#             sender= dispenser.address,
#             receiver=buyer.address,
#             amount=10_000_000,
#         )
#     )    

#     algorand.send.asset_opt_in(
#        AssetOptInParams(
#        sender=buyer.address,
#          asset_id=test_asset_id,
#        )
#     )

#     # buy two assets  

#     buyer_payment_txn = algorand.transactions.payment(
#         PayParams(
#             sender=buyer.address,
#             receiver=digital_marketplace_client.app_address,
#             amount = 2 * 3_3000_000,
#             extra_fee=1_000,
#         )
#     )

#     result = digital_marketplace_client.buy(
#         buyerTxb=TransactionWithSigner(txn=buyer_payment_txn, signer=buyer.signer),
#         quantity=2,
#         transaction_parameters=algokit_utils.TransactionParameters(
#             sender=buyer.address,
#             signer=buyer.signer,
#             foreign_assets=[test_asset_id], 
#         ),
#     )

#     # make sure the buyer got an asset 
#     assert result.confirmed_round 

    # assert(algorand.account.get_asset_information(
    #     digital_marketplace_client.app_address, test_asset_id)["asset-holding"]["amount"] == 3
    # )


# def test_delete_application(digital_marketplace_client: MarketplaceClient, creator: AddressAndSigner, algorand: AlgorandClient, test_asset_id: int):
#     before_call_amount = algorand.account.get_information(creator.address)["amount"]

#     result = digital_marketplace_client.delete_delete_application(
#         transaction_parameters=algokit_utils.TransactionParameters(
#             foreign_assets=[test_asset_id],
#         )
#     )

   