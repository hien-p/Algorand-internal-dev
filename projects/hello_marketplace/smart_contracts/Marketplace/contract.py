from algopy import *
from algopy import itxn 
import algopy as ap

class Marketplace(ARC4Contract):

    assetID: UInt64  # global state  
    unitaryprice: UInt64 # global state

    # create application abi method, we set noop stand for no operations, 
    @arc4.abimethod(allow_actions=["NoOp"], create="require")
    def createAppliaction(self, assetID: Asset, unitaryprice: UInt64) -> None:
        self.assetID = assetID.id
        self.unitaryprice = unitaryprice

    @arc4.abimethod
    def setPrice(self, unitaryprice: UInt64) -> None:
        assert Txn.sender == Global.creator_address
        self.unitaryprice = unitaryprice
    
    # choose the asset will be sold 
    @arc4.abimethod
    def chooseAsset(self, mbrPay: gtxn.PaymentTransaction) -> None:
        assert Txn.sender == Global.creator_address

        assert not Global.current_application_address.is_opted_in(Asset(self.assetID))
        assert mbrPay.receiver == Global.current_application_address
        
        # the amount of the mbrpay is equal to the minimum balance from 
        assert mbrPay.amount ==  Global.min_balance + Global.asset_opt_in_min_balance 


        itxn.AssetTransfer(xfer_asset=self.assetID,
        asset_receiver=Global.current_application_address, 
        asset_amount=0).submit()


    # buy the asset
    @arc4.abimethod
    def Buy(self, buyerTxb: gtxn.PaymentTransaction, quantity: UInt64) -> None: 
        assert self.unitaryprice != UInt64(0) 
        assert Txn.sender == buyerTxb.sender 
        assert buyerTxb.receiver == Global.current_application_address
        assert buyerTxb.amount == self.unitaryprice * quantity # the amount of the buyerTxb is equal to the price of the asset

        itxn.AssetTransfer(
            xfer_asset=self.assetID,
            asset_receiver= Txn.sender,
            asset_amount=quantity
        ).submit()


    # we want to withdraw all the profits, when people buy assets they sent algos to the smart contract account. The creator need withdraw the moneys before delete smart contract 
    @arc4.abimethod(allow_actions=["DeleteApplication"])
    def deleteApplication(self) -> None:
        assert Txn.sender == Global.creator_address

        itxn.AssetTransfer(
            xfer_asset=self.assetID,
            asset_receiver=Global.creator_address,
            asset_amount=0,
            asset_close_to=Global.creator_address
        ).submit()

        itxn.Payment(
            receiver=Global.creator_address, 
            amount=0,
            close_remainder_to=Global.creator_address
        ).submit()

        self.deleteApplication()
        
