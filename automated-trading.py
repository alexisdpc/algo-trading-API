''' ================================================  Trading on the Vertex Protocol ============================================
Author: Alexis Plascencia 

On Vertex, all spot assets trade against USDC and settle in balances. Buying an asset on the spot market requires you to exchange USDC. 
Selling an asset means you'll receive USDC.

For DepositCollateral and WithdrawCollateral, the amount specifies the physical token amount that you want to receive. 
i.e. if USDC has 6 decimals, and you want to deposit or withdraw 1 USDC, you specify amount = 1e6.

For all other transactions, amount is normalized to 18 decimals, so 1e18 == one unit of the underlying asset. 
For example, if you want to buy 1 wETH, regardless of the amount of decimals the wETH contract has on chain, 
you specify 1e18 in the amount field of the order.
============================================================================================================================='''

import time
import json
import pandas as pd

from configparser import ConfigParser
from vertex_protocol.client import create_vertex_client
from vertex_protocol.engine_client.types.execute import (
    OrderParams,
    PlaceOrderParams
)
from vertex_protocol.contracts.types import DepositCollateralParams
from vertex_protocol.utils.bytes32 import subaccount_to_bytes32, subaccount_to_hex
from vertex_protocol.utils.expiration import OrderType, get_expiration_timestamp
from vertex_protocol.utils.math import to_pow_10, to_x18
from vertex_protocol.utils.nonce import gen_order_nonce
from vertex_protocol.utils.subaccount import SubaccountParams

from eth_account import Account
from eth_account.signers.local import LocalAccount

def read_credentials():
  """Read the account and private key from the config.ini file

  Returns:
      list with two elements: the account number and the private key.
  """

  config = ConfigParser()
  config.read('config.ini')

  # Account details
  account = config.get('Account_Details', 'account')
  private_key = config.get('Account_Details', 'private_key')

  return [account, private_key]

def vertex_client(private_key):
  """Set up Vertex client

  Arguments:
      private_key: The private key to make for the account making the transactions

  Returns:
      client: The client variable that connects to either the Testnet or Mainnet
  """
    
  print("setting up vertex client...")

  #client = create_vertex_client(ClientMode.MAINNET, private_key)
  #client = create_vertex_client(ClientMode.TESTNET, private_key)
  #client = create_vertex_client("mainnet", private_key)

  client = create_vertex_client("sepolia-testnet", private_key)
  #signer: LocalAccount = Account.from_key(private_key)
  #client_from_signer = create_vertex_client("sepolia-testnet", signer)
  return client


def deposit_collateral(client):
  """Deposit the collateral

  Arguments:
      client: The client variable that connects to either the Testnet or Mainnet
  """
    
  # First approve allowance for the amount you want to deposit
  print("approving allowance...")

  #approve_allowance_tx_hash = client.spot.approve_allowance(31, to_pow_10(1, 10))
  approve_allowance_tx_hash = client.spot.approve_allowance(3, to_pow_10(3, 18))

  print("approve allowance tx hash:", approve_allowance_tx_hash)

  # Now, you can make the actual deposit.
  print("depositing collateral...")
  deposit_tx_hash = client.spot.deposit(
        DepositCollateralParams(
            #subaccount_name="default", product_id=31, amount=to_pow_10(1, 10)
            subaccount_name="default", product_id=3, amount=to_pow_10(3, 18)
        )
    )
  print("deposit collateral tx hash:", deposit_tx_hash) 


def buy_and_sell(time_pause):
  """Deposit the collateral

  Arguments:
      client: The client variable that connects to either the Testnet or Mainnet
  """
  token_id = 3
  num_transactions = 10
  for i in range(num_transactions):

    # Retrieves liquidity per price tick from the engine:
    liquid = client.market.get_market_liquidity(product_id=3, depth=1)
    liquid_res = liquid.json()

    bids_start = liquid_res.find("bids")
    bids_end = liquid_res.find(",", bids_start+10)
    bid_price = int(liquid_res[bids_start+10:bids_end-1])

    ask_start = liquid_res.find("asks")
    ask_end = liquid_res.find(",", ask_start+10)
    ask_price = int(liquid_res[ask_start+10:ask_end-1])
    #print(bid_price, ask_price)

    # For example, to submit an IOC order with an expiration of 1000 seconds, we would set expiration as follows:
    unix_epoch = int(time.time())
    ioc_expiration = str((unix_epoch + 1000) | (1 << 62))
    #get_expiration_timestamp(OrderType.POST_ONLY, int(time.time()) + 40),

    owner = client.context.engine_client.signer.address
    print("placing order...")
    order = OrderParams(
        sender=SubaccountParams(
            subaccount_owner=owner,
            subaccount_name="default",
        ),
        priceX18=ask_price+10000000000000000000,
        amount=1e18,
        expiration=ioc_expiration,
        nonce=gen_order_nonce(),
      )
    res = client.market.place_order(PlaceOrderParams(product_id=token_id, order=order))
    #print("order result:", res.json(indent=2))


    res_json = res.json(indent=2)
    output = json.loads(res_json)
    status.append(output['status'])
    time_exec.append(output['req']['place_order']['order']['expiration'])

    amount = int(output['req']['place_order']['order']['amount'])
    amount_trade.append(amount)

    if amount<0:
      transaction.append('Sell')

    elif amount>0:
      transaction.append('Buy')  

    producto_id.append(output['req']['place_order']['product_id'])
    request_type.append(output['request_type'])

    time.sleep(time_pause)  # Makes a 'time_pause' seconds pause

    # Retrieves liquidity per price tick from the engine:
    liquid = client.market.get_market_liquidity(product_id=3, depth=1)
    liquid_res = liquid.json()

    bids_start = liquid_res.find("bids")
    bids_end = liquid_res.find(",", bids_start+10)
    bid_price = int(liquid_res[bids_start+10:bids_end-1])

    ask_start = liquid_res.find("asks")
    ask_end = liquid_res.find(",", ask_start+10)
    ask_price = int(liquid_res[ask_start+10:ask_end-1])
    #print(bid_price, ask_price)

    unix_epoch = int(time.time())
    ioc_expiration = str((unix_epoch + 1000) | (1 << 62))
    #get_expiration_timestamp(OrderType.POST_ONLY, int(time.time()) + 40),

    owner = client.context.engine_client.signer.address
    print("placing order...")
    order = OrderParams(
        sender=SubaccountParams(
            subaccount_owner=owner,
            subaccount_name="default",
        ),
        priceX18=bid_price-1000000000000000000,
        amount=-1e18,
        expiration=ioc_expiration,
        nonce=gen_order_nonce(),
      )
    res = client.market.place_order(PlaceOrderParams(product_id=token_id, order=order))
    #print("order result:", res.json(indent=2))

    res_json = res.json(indent=2)
    output = json.loads(res_json)
    status.append(output['status'])
    time_exec.append(output['req']['place_order']['order']['expiration'])

    amount = int(output['req']['place_order']['order']['amount'])
    amount_trade.append(amount)

    if amount<0:
      transaction.append('Sell')

    elif amount>0:
      transaction.append('Buy')  

    producto_id.append(output['req']['place_order']['product_id'])
    request_type.append(output['request_type'])

    time.sleep(time_pause)  # Makes a 'time_pause' seconds pause  


status = []
time_exec = []
amount_trade = []
producto_id = []
request_type = []
transaction = []
time_pause = 5        # Time pause between each buy and sell in seconds


if __name__ == "__main__":
  
  account, private_key = read_credentials()
  client = vertex_client(private_key)
  #deposit_collateral(client)
  buy_and_sell(time_pause)

  # ===================== Generate CSV file with the details of all the transactions: =====================

  product_symbol = []
  amount_normal = []
  time_normal = []

  for i in range(len(time_exec)):
    time_normal.append(int(time_exec[i])-int(time_exec[0]))
    amount_normal.append(amount_trade[i]/1e18)  
    if producto_id[i] == 3:
      product_symbol.append('ETH')
  
  df = pd.DataFrame({"Status": status})
  df["Execution Time"] = time_normal
  df['Symbol'] = product_symbol
  df['Transaction'] = transaction 
  df['Amount'] = amount_normal
  df['Request type'] = request_type

  df.to_csv('transactions.csv')

