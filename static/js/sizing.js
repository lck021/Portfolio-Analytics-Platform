// To dynamically show the current stock price
const symbol_input = document.getElementById("symbol")
const current_price = document.getElementById("current-price")

async function updatePrice () {
    const symbol = symbol_input.value

    if (symbol.length == 0) {
        return
    }

    const response = await fetch(`/api/quote?symbol=${symbol}`)
    const data = await response.json()

    current_price.textContent = `$${data.current_price}`
}

symbol_input.addEventListener("change", updatePrice)

if (symbol_input.value.length != 0) {
    updatePrice()
}

// To display positive/negative labels
const calculatorData = document.getElementById("calculator-data")

if (calculatorData) {
    const cash = Number(calculatorData.dataset.cash)
    const capitalRequired = Number(calculatorData.dataset.capitalRequired)
    const portfolioAllocation = Number(calculatorData.dataset.portfolioAllocation)

    document.getElementById("capital-negative").hidden =
        cash > capitalRequired

    document.getElementById("capital-positive").hidden =
        cash <= capitalRequired

    document.getElementById("portfolio-negative").hidden =
        portfolioAllocation < 15

    document.getElementById("portfolio-positive").hidden =
        portfolioAllocation >= 15
}