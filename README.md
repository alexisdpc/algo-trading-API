# Algorithmic trading on the Vertex protocol

In this repository we implement automated trading in the Vertex protocol.\
Using the Vertex API we automate buy and sell orders in a python script. \
The orders can be checked in the online exchange as the image shows:

![image](https://github.com/alexisdpc/algo-trading-API/assets/124795834/dc4af327-c64d-4645-a608-e8ecf947b532)

## Futures data using Deribit API

The Jupyter notebook `eth_futures_yield.ipynb` analyses futures data using Deribit's API.

![image](https://github.com/alexisdpc/algo-trading-API/assets/124795834/109b86ec-2536-4a10-b9a3-caf0dc63e9a4)


## DUNE Analytics and ETH transaction fees

Here we provide an example query to obtain the total base and priority fees by block.

```sql
/*  Base and priority fees in ETH by block. (Dune Analytics SQL query)
Author: Alexis Plascencia   aplascenciac@gmail.com
First, we combine the 'transactions' and 'blocks' table and complete the 'priority_fee_per_gas' */
WITH table1 AS(
    SELECT
        block_number,
        t.gas_used,
        priority_fee_per_gas,
        CASE WHEN priority_fee_per_gas IS NOT NULL 
            THEN priority_fee_per_gas ELSE gas_price-b.base_fee_per_gas END AS all_priority_fee_per_gas,
        t.gas_used*(gas_price/1e18) AS fees_eth,
        t.gas_used*(b.base_fee_per_gas/1e18) AS base_fees
    FROM ethereum.transactions t
    LEFT JOIN ethereum.blocks b ON block_number = number
    WHERE block_time > date '2024-01-01' 
      AND success
)

/* We get the total base and priority fees by summing over each block
priority_fees_eth includes only those with 'DynamicFee'
all_priority_fees_eth includes all priority fees such that 
the equality  total_fees_eth = base_fees_eth + all_priority_fees_eth  is satisfied */
SELECT
    block_number,
    SUM(fees_eth) AS total_fees_eth,
    SUM(base_fees) AS base_fees_eth,
    SUM(gas_used*(priority_fee_per_gas/1e18)) AS priority_fees_eth,
    SUM(gas_used*(all_priority_fee_per_gas/1e18)) AS all_priority_fees_eth
FROM table1
GROUP BY 1
ORDER BY 1 DESC
```

## Bitcoin price forecasting 

