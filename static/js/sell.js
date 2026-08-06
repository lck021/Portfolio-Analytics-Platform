function clearOrderSummary() {
    document.getElementById("sell-stock-price").textContent = "—"
    document.getElementById("sell-stock-total").textContent = ""
    document.getElementById("sell-shares-owned").textContent = "—"
    document.getElementById("sell-cash-remaining").textContent = "—"
}

// gets symbol dropdown and shares field
const symbolInput = document.getElementById("sell-symbol")
const sellShares = document.getElementById("sell-shares")

// function to update order information
async function updateOrderSummary() {
    const symbol = symbolInput.value
    const quantity = Number(sellShares.value)
    const infoLabel = document.getElementById("sell-info-label")

    if (quantity == 0) {
        return
    }

    clearOrderSummary() // resets order information fields
    const response = await fetch(`/sell/data?symbol=${symbol}&shares=${quantity}`);
    const data = await response.json()

    if (data.valid_ticker == false) {
        clearOrderSummary()
        infoLabel.textContent = "Invalid ticker!"
        infoLabel.classList.remove("positive-label")
        infoLabel.classList.add("negative-label")
        return
    }

    if (data.valid_shares == false) {
        clearOrderSummary()
        if (data.shares_owned !== undefined) {
            infoLabel.textContent = `You only own ${data.shares_owned} share${data.shares_owned == 1 ? '' : 's'}!`
        } else {
            infoLabel.textContent = "Invalid number of shares!"
        }
        infoLabel.classList.remove("positive-label")
        infoLabel.classList.add("negative-label")
        return
    }

    const { individual_cost, estimated_proceeds, shares_owned, cash_available, cash_after_sale } = data

    document.getElementById("sell-stock-price").textContent = estimated_proceeds.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
    document.getElementById("sell-stock-total").textContent = `${quantity.toLocaleString('en-US')} shares at ${individual_cost.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}`
    document.getElementById("sell-shares-owned").textContent = shares_owned.toLocaleString('en-US')
    document.getElementById("sell-cash-remaining").textContent = cash_after_sale.toLocaleString('en-US', { style: 'currency', currency: 'USD' })

    infoLabel.textContent = "Order valid"
    infoLabel.classList.remove("negative-label")
    infoLabel.classList.add("positive-label")
}

symbolInput.addEventListener("change", updateOrderSummary)
sellShares.addEventListener("input", updateOrderSummary)