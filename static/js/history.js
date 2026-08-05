async function loadTransactionHistory() {
    const response = await fetch('/transactions/history/data')
    const data = await response.json()

    transaction_history = data.transaction_history

    if (transaction_history == null) {
        return
    }

    const tbody = document.getElementById("transactions-tbody")

    transaction_history.forEach(t => {
        const isSell = t.type === "SELL"

        const row = document.createElement("tr")
        row.innerHTML = `
        <td>${t.symbol}</td>
        <td class="num">${Number(t.shares)}</td>
        <td class="num">${t.price.toLocaleString('en-US',{style:'currency', currency:'USD'})}</td>
        <td class="num">${t.total.toLocaleString('en-US',{style:'currency', currency:'USD'})}</td>
        <td><span class="display-table__badge ${isSell ? "sell" : "buy"}">${t.type}</span></td>
        <td class="num">${t.time}</td>`
        tbody.appendChild(row)
    })
}

document.addEventListener("DOMContentLoaded", loadTransactionHistory)