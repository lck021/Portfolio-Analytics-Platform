function clearBalanceSummary() {
    document.getElementById("cash-new-balance").textContent = "—"
}

const cashAmount = document.getElementById("cash-amount")

async function updateBalanceSummary() {
    const amount = cashAmount.value
    const infoLabel = document.getElementById("cash-info-label")

    const response = await fetch(`/cash/data?cash=${amount}`)
    const data = await response.json()

    document.getElementById("cash-current-balance").textContent =
        data.current_balance.toLocaleString('en-US', { style: 'currency', currency: 'USD' })

    if (amount.length == 0) {
        clearBalanceSummary()
        infoLabel.textContent = ""
        return
    }

    if (data.valid_amount == false) {
        clearBalanceSummary()
        infoLabel.textContent = "Enter a valid amount!"
        infoLabel.classList.remove("positive-label")
        infoLabel.classList.add("negative-label")
        return
    }

    document.getElementById("cash-new-balance").textContent =
        data.new_balance.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
    infoLabel.textContent = "Ready to deposit"
    infoLabel.classList.remove("negative-label")
    infoLabel.classList.add("positive-label")
}

cashAmount.addEventListener("input", updateBalanceSummary)

// populate current balance on page load
updateBalanceSummary()