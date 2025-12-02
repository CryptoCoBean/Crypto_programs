from web3 import Web3

# Connect to Ethereum node (or Arbitrum, or whichever chain Variational uses)
w3 = Web3(Web3.HTTPProvider("https://your.node.url"))

# Your wallet
private_key = "0xyourprivatekey"
wallet = w3.eth.account.from_key(private_key)
address = wallet.address

# Load contract ABI + address
with open("SettlementPoolABI.json") as f:
    abi = f.read()

contract_address = "0xSettlementPoolContractAddress"
settlement_contract = w3.eth.contract(address=contract_address, abi=abi)

# Example: call a function to open a trade / deposit margin
tx = settlement_contract.functions.openPosition(
    # function parameters according to contract
    ... 
).build_transaction({
    "from": address,
    "gas": 300_000,
    "nonce": w3.eth.get_transaction_count(address),
})

# Sign and send
signed = w3.eth.account.sign_transaction(tx, private_key)
tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
print("TX hash:", w3.toHex(tx_hash))

# Wait for receipt
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print("Receipt:", receipt)
