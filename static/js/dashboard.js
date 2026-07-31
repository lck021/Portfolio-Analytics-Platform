function setText(id, text) {
    document.getElementById(id).textContent = text
}

async function loadDashboard() {
    const response = await fetch("/api/dashboard")
    const data = await response.json()

    setText(
        "portfolio-value",
        data.portfolio_value.toLocaleString('en-US',{style:'currency', currency:'USD'})
    )

    setText(
        "largest-winner-symbol",
        data.largest_winner.symbol
    )

    setText(
        "largest-winner-percent",
        `${data.largest_winner.percent_return.toFixed(2)}%`
    )

    setText(
        "largest-winner-value",
        data.largest_winner.profit_loss.toLocaleString('en-US',{style:'currency', currency:'USD'})
    )

    setText(
        "largest-winner-subtext",
        `Cost basis ${data.largest_winner.cost_basis.toLocaleString('en-US',{style:'currency', currency:'USD'})} · unrealized`
    )

    setText(
        "largest-loser-symbol",
        data.largest_loser.symbol
    )

    setText(
        "largest-loser-percent",
        `${data.largest_loser.percent_return.toFixed(2)}%`
    )

    setText(
        "largest-loser-value",
        data.largest_loser.profit_loss.toLocaleString('en-US',{style:'currency', currency:'USD'})
    )

    setText(
        "largest-loser-subtext",
        `Cost basis ${data.largest_loser.cost_basis.toLocaleString('en-US',{style:'currency', currency:'USD'})} · unrealized`
    )

    setText(
        "best-position-symbol",
        data.best_position.symbol
    )

    setText(
        "best-position-return",
        `${data.best_position.percent_return.toFixed(2)}%`
    )

    setText(
        "worst-position-symbol",
        data.worst_position.symbol
    )

    setText(
        "worst-position-return",
        `${data.worst_position.percent_return.toFixed(2)}%`
    )
}

document.addEventListener("DOMContentLoaded", loadDashboard)