# #Exponential
import matplotlib.pyplot as plt
import numpy as np

# # Portfolio size
# P = 76000

# # Exponential risk parameters
# floor = 0.001   # 0.1%
# cap = 0.5      # 5%
# M0 = 1e9        # scaling reference
# k = 6           # steepness factor
# m_shift = 3e6   # start accelerating around 3M

# def risk_pct(mcap):
#     """Return portfolio risk % given market cap (exponential growth starting at 3M)."""
#     adjusted = max(0, mcap - m_shift)  # no negative exponent
#     risk = floor + (cap - floor) * (1 - np.exp(-k * adjusted / M0))
#     return min(risk, cap)

# def allocation(mcap):
#     """Return $ allocation for given market cap."""
#     return P * risk_pct(mcap)

# while True:
#     # Example: test 700k mcap
#     mcap_test = int(input("Enter a mcap of the asset you want to test? "))
#     # mcap_test = 148_000_000
#     risk_test = risk_pct(mcap_test)
#     alloc_test = allocation(mcap_test)

#     print(f"Market Cap: ${mcap_test:,.0f}")
#     print(f"Risk % of Portfolio: {risk_test*100:.2f}%")
#     print(f"Position Size: ${alloc_test:,.2f}")

#     # --- Plot risk curve ---
#     mcap_vals = np.logspace(5, 11, 1000)  # 100k to 100B
#     risk_vals = [risk_pct(m) for m in mcap_vals]

#     plt.figure(figsize=(10,6))
#     plt.plot(mcap_vals, [r*100 for r in risk_vals], label='Risk %', color='green')

#     # --- Add lines to show example point ---
#     plt.axvline(mcap_test, color='red', linestyle='--', label=f'Market Cap: ${mcap_test:,}')
#     plt.axhline(risk_test*100, color='blue', linestyle='--', label=f'Risk: {risk_test*100:.2f}%')
#     plt.scatter(mcap_test, risk_test*100, color='orange', zorder=5, s=80, label='Point')

#     plt.xscale('log')
#     plt.xlabel('Market Cap (USD, log scale)')
#     plt.ylabel('Risk % of Portfolio')
#     plt.title('Exponential Portfolio Risk vs Market Cap')
#     plt.grid(True, which="both", ls="--", lw=0.5)
#     plt.legend()
#     plt.show()

############################################################################################################################
# Asset risk by mcap full port size (Good above 1B)

# Portfolio size
P = 76000

# Exponential risk parameters
floor = 0.001   # 0.1%
cap = 0.2      # 20%
M0 = 100e9        # scaling reference (Max market cap)
k = 6           # steepness factor
m_shift = 1e5   # start accelerating around 100k mcap

def risk_pct(mcap):
    """Return portfolio risk % given market cap (exponential growth starting at 3M)."""
    adjusted = max(0, mcap - m_shift)  # no negative exponent
    risk = floor + (cap - floor) * (1 - np.exp(-k * adjusted / M0))
    return min(risk, cap)

def allocation(mcap):
    """Return $ allocation for given market cap."""
    return P * risk_pct(mcap)

while True:
    # Example: test 700k mcap
    mcap_test = int(input("Enter a mcap of the asset you want to test? "))
    # mcap_test = 148_000_000
    risk_test = risk_pct(mcap_test)
    alloc_test = allocation(mcap_test)

    print(f"Market Cap: ${mcap_test:,.0f}")
    print(f"Risk % of Portfolio: {risk_test*100:.2f}%")
    print(f"Position Size: ${alloc_test:,.2f}")

    # --- Plot risk curve ---
    mcap_vals = np.logspace(5, 11, 1000)  # 100k to 100B
    risk_vals = [risk_pct(m) for m in mcap_vals]

    plt.figure(figsize=(10,6))
    plt.plot(mcap_vals, [r*100 for r in risk_vals], label='Risk %', color='green')

    # --- Add lines to show example point ---
    plt.axvline(mcap_test, color='red', linestyle='--', label=f'Market Cap: ${mcap_test:,}')
    plt.axhline(risk_test*100, color='blue', linestyle='--', label=f'Risk: {risk_test*100:.2f}%')
    plt.scatter(mcap_test, risk_test*100, color='orange', zorder=5, s=80, label='Point')

    plt.xscale('log')
    plt.xlabel('Market Cap (USD, log scale)')
    plt.ylabel('Risk % of Portfolio')
    plt.title('Exponential Portfolio Risk vs Market Cap')
    plt.grid(True, which="both", ls="--", lw=0.5)
    plt.legend()
    plt.show()


