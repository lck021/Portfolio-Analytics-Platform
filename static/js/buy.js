function clearOrderSummary() {
    document.getElementById("buy-stock-price").textContent = "—"
    document.getElementById("buy-stock-total").textContent = "—"
    document.getElementById("buy-cash-available").textContent = "—"
    document.getElementById("buy-cash-remaining").textContent = "—"
}

//gets symbol field, 'quote' button and graph type selector
const lookupButton = document.getElementById("buy-lookup-btn")
const symbolInput = document.getElementById("buy-symbol")
const buyQuantity = document.getElementById("buy-quantity")

// fills in quote field 
lookupButton.addEventListener("click", async function () {
    const symbol = symbolInput.value
    currentSymbol = symbol

    if (symbol.length == 0) {
        return;
    }

    const response = await fetch(`/api/quote?symbol=${symbol}`);
    const data = await response.json()

    const sign = data.change > 0 ? "+" : data.change < 0 ? "-" : ""

    const card = document.querySelector('.quote-card')
    card.classList.toggle('is-up', sign == "+")
    card.classList.toggle('is-down', sign == "-")

    //displays immediate data about stock
    document.getElementById("symbol-show").textContent = symbol
    document.getElementById("current-price").textContent = `$${data.current_price}`
    document.getElementById("change").textContent = `${sign}$${Math.abs(data.change)}`
    document.getElementById("percent-change").textContent = `(${data.percent_change}%)`
    document.getElementById("high").textContent = `${data.high}`
    document.getElementById("low").textContent = `${data.low}`
    document.getElementById("open").textContent = `${data.open}`
    document.getElementById("previous-close").textContent = `${data.previous_close}`
})

// function to update order information
async function updateOrderSummary() {
    const symbol = symbolInput.value
    const quantity = Number(buyQuantity.value)
    const infoLabel = document.getElementById("buy-info-label")

    if (quantity == 0) {
        return
    }

    clearOrderSummary() // resets order information fields
    const response = await fetch(`/buy/data?symbol=${symbol}&shares=${quantity}`);
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
        infoLabel.textContent = "Invalid number of shares!"
        infoLabel.classList.remove("positive-label")
        infoLabel.classList.add("negative-label")
        return
    }

    const { individual_cost, estimated_cost, cash_available, remaining_cash } = data

    document.getElementById("buy-stock-price").textContent = estimated_cost.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
    document.getElementById("buy-stock-total").textContent = `${quantity.toLocaleString('en-US')} shares at ${individual_cost.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}`
    document.getElementById("buy-cash-available").textContent = cash_available.toLocaleString('en-US', { style: 'currency', currency: 'USD' })

    if (remaining_cash < 0) {
        document.getElementById("buy-cash-remaining").textContent = "$0.00"
        infoLabel.textContent = "Insufficient cash!"
        infoLabel.classList.remove("positive-label")
        infoLabel.classList.add("negative-label")
        return
    }

    document.getElementById("buy-cash-remaining").textContent = remaining_cash.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
    infoLabel.textContent = "Sufficient cash"
    infoLabel.classList.remove("negative-label")
    infoLabel.classList.add("positive-label")
}

symbolInput.addEventListener("change", updateOrderSummary)
buyQuantity.addEventListener("input", updateOrderSummary)