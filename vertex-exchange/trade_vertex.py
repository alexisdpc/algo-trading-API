'''
 ==========================================  Trading on the Vertex Protocol =======================================
 Author: Alexis Plascencia 

First need to get some credit on the testnet from an Arbitrum Sepolia Faucet, e.g:
https://arbitrum-faucet.com/

On Vertex, all spot assets trade against USDC and settle in balances. Buying an asset on the spot market requires you to exchange USDC. 
Selling an asset means you'll receive USDC.

For DepositCollateral and WithdrawCollateral, the amount specifies the physical token amount that you want to receive. 
i.e. if USDC has 6 decimals, and you want to deposit or withdraw 1 USDC, you specify amount = 1e6.

For all other transactions, amount is normalized to 18 decimals, so 1e18 == one unit of the underlying asset. For example, if you want to buy 1 wETH, 
regardless of the amount of decimals the wETH contract has on chain, you specify 1e18 in the amount field of the order.
'''

import requests
import time
import json

from configparser import ConfigParser
from vertex_protocol.client import create_vertex_client
from vertex_protocol.engine_client.types.execute import (
    OrderParams,
    PlaceOrderParams,
    WithdrawCollateralParams,
    PlaceMarketOrderParams,
    CancelOrdersParams
)
from vertex_protocol.contracts.types import DepositCollateralParams
from vertex_protocol.utils.bytes32 import subaccount_to_bytes32, subaccount_to_hex
from vertex_protocol.utils.expiration import OrderType, get_expiration_timestamp
from vertex_protocol.utils.math import to_pow_10, to_x18
from vertex_protocol.utils.nonce import gen_order_nonce
from vertex_protocol.utils.subaccount import SubaccountParams

from eth_account import Account
from eth_account.signers.local import LocalAccount

# ================== Read config.ini file =============================
config = ConfigParser()
config.read('config.ini')

# Account details
account = config.get('Account_Details', 'account')
private_key = config.get('Account_Details', 'private_key')

# ==============Set up Vertex client ================================
print("setting up vertex client...")

#client = create_vertex_client(ClientMode.MAINNET, private_key)
#client = create_vertex_client(ClientMode.TESTNET, private_key)
#client = create_vertex_client("mainnet", private_key)

client = create_vertex_client("sepolia-testnet", private_key)
signer: LocalAccount = Account.from_key(private_key)
client_from_signer = create_vertex_client("sepolia-testnet", signer)

# ====================== Mint test tokens =======================
print("minting test tokens...")
mint_tx_hash = client.spot._mint_mock_erc20(31, to_pow_10(1, 18))  #Product Ids: BTC: 0, ETH: 3, USDC: 31
mint_tx_hash = client.spot._mint_mock_erc20(3, to_pow_10(1, 18))  #Product Ids: BTC: 0, ETH: 3, USDC: 31
print("mint tx hash:", mint_tx_hash)

# ====================== Deposit collateral =======================

# First approve allowance for the amount you want to deposit
print("approving allowance...")
approve_allowance_tx_hash = client.spot.approve_allowance(31, to_pow_10(1, 18))
print("approve allowance tx hash:", approve_allowance_tx_hash)

# Now, you can make the actual deposit.
##print("depositing collateral...")
deposit_tx_hash = client.spot.deposit(
        DepositCollateralParams(
            subaccount_name="default", product_id=31, amount=to_pow_10(1, 18)
        )
    )
print("deposit collateral tx hash:", deposit_tx_hash) 

# Retrieves liquidity per price tick from the engine:
client.market.get_market_liquidity(product_id=3, depth=1)

# ========================= Placing an order: =================================
status = []
time_exec = []
amount_trade = []
producto_id = []
request_type = []

for i in range(10):
  # For example, to submit an IOC order with an expiration of 1000 seconds, we would set expiration as follows:
  unix_epoch = int(time.time())
  ioc_expiration = str((unix_epoch + 1000) | (1 << 62))
  #get_expiration_timestamp(OrderType.POST_ONLY, int(time.time()) + 40),

  owner = client.context.engine_client.signer.address
  print("placing order...")
  product_id = 3
  order = OrderParams(
        sender=SubaccountParams(
            subaccount_owner=owner,
            subaccount_name="default",
        ),
        priceX18=to_x18(2516),
        amount=to_pow_10(1, 17),
        expiration=ioc_expiration,
        nonce=gen_order_nonce(),
    )
  res = client.market.place_order(PlaceOrderParams(product_id=3, order=order))
  print("order result:", res.json(indent=2))


  res_json = res.json(indent=2)
  output = json.loads(res_json)
  status.append(output['status'])
  time_exec.append(output['req']['place_order']['order']['expiration'])
  amount_trade.append(output['req']['place_order']['order']['amount'])
  producto_id.append(output['req']['place_order']['product_id'])
  request_type.append(output['request_type'])
  time.sleep(10)  # Trades every 10 seconds