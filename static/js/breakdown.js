function sgd(value) {
    return value.toLocaleString('en-US', {
        style: 'currency',
        currency: 'USD'})
}

function setText(id, text) {
    document.getElementById(id).textContent = text
}

function setVisible(id, visible) {
    document.getElementById(id).style.display = visible ? "" : "none"
}

async function loadBreakdown() {
    const response = await fetch("/breakdown/data")
    const data = await response.json()

    if (data.insufficient_data) {
        setVisible("breakdown--empty", true)
        setText("breakdown--empty-cash", 
            `Current cash: ${data.current_cash.toLocaleString('en-US',{style:'currency', currency:'USD'})}`
        )
        return
    }

    setVisible("breakdown--empty", false)
    const { portfolio, current_cash, total, stock_data, sector_data } = data

    // write portfolio breakdown table
    const thead = document.getElementById('portfolio-breakdown-thead');

    const headerRow = document.createElement('tr');
    headerRow.innerHTML = `
        <th class="text-start"><strong>Symbol</strong></th>
        <th class="text-end"><strong>Shares</strong></th>
        <th class="text-end"><strong>Price</strong></th>
        <th class="text-end"><strong>Total</strong></th>`
    thead.appendChild(headerRow)

    const tbody = document.getElementById('portfolio-breakdown-tbody')
    portfolio.forEach(stock => {
                const row = document.createElement('tr')
                row.innerHTML = `
                    <td class="text-start">${stock.symbol}</td>
                    <td class="text-end">${stock.total_shares}</td>
                    <td class="text-end">${sgd(stock.price)}</td>
                    <td class="text-end">${sgd(stock.total)}</td>
                `;
                tbody.appendChild(row)
            });

    const cashRow = document.createElement('tr')
    cashRow.innerHTML = `
        <td colspan="3" class="text-end"><strong>Cash</strong></td>
        <td class="text-end">${sgd(current_cash)}</td>`
    tbody.appendChild(cashRow)

    const totalRow = document.createElement('tr')
    totalRow.innerHTML = `
        <td colspan="3" class="text-end"><strong>TOTAL</strong></td>
        <td class="text-end">${sgd(total)}</td>`
    tbody.appendChild(totalRow)

    // create holdings data pie chart
    const stockData = stock_data

    const stockLabels = stockData.map(stock => stock.symbol)
    const stockValues = stockData.map(stock => Number(stock.total))
    const stockBackgroundColors = stockLabels.map((_, i) => {
        const hue = (i * 137.508) % 360;   // Golden angle
        return `hsl(${hue}, 80%, 55%)`;
    });

    Chart.register(ChartDataLabels)
    new Chart(document.getElementById("stock-breakdown-pie"), {
        type: 'pie',
        data: {
            labels: stockLabels, 
            datasets: [{
                label: "Value",
                data: stockValues,
                backgroundColor: stockBackgroundColors,
                borderColor: "black",
                borderWidth: 2, 
                hoverOffset: 10,
            }]
        }, 
        options: {
            responsive: true, 
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: "white", 
                        font: {
                            size: 18, 
                            weight: "bold"
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'Stock Breakdown', 
                    color: "white", 
                    font: {
                        size: 24
                    }, 
                    padding: {
                        top: 20, 
                        bottom: 30,
                        left: 10, 
                        right: 10
                    }
                }, 
                datalabels: {
                    color: "white",
                    anchor: "end", 
                    align: "end", 
                    offset: 10,
                    clamp: true,
                    font: {
                        weight: "bold", 
                        size: 16,
                    }, 
                    formatter: function(value, context) {
                        const total = stockValues.reduce((a, b) => a + b, 0)
                        const percentage = ((value / total) * 100).toFixed(2)

                        return `${percentage}%`
                    }, 
                },
                tooltip: {
                    callbacks: {
                    label: function(context) {
                        const total = stockValues.reduce((a, b) => a + b, 0)
                        const percentage = ((context.raw / total) * 100).toFixed(2)

                        return `${context.label}: $${context.raw.toLocaleString()} (${percentage}%)`
                        }
                    }
                }
            }
        }
    })
            

    // creating sector data pie chart
    const sectorData = sector_data

    const sectorLabels = Object.keys(sectorData)
    const sectorValues = Object.values(sectorData)
    const sectorBackgroundColors = sectorLabels.map((_, i) => {
        const hue = (i * 137.508) % 360;   // Golden angle
        return `hsl(${hue}, 80%, 55%)`;
    });

    Chart.register(ChartDataLabels)
    new Chart(document.getElementById("sector-breakdown-pie"), {
        type: 'pie',
        data: {
            labels: sectorLabels, 
            datasets: [{
                label: "Value",
                data: sectorValues,
                backgroundColor: sectorBackgroundColors,
                borderColor: "black",
                borderWidth: 2, 
                hoverOffset: 10,
            }]
        }, 
        options: {
            responsive: true, 
            maintainAspectRatio: false,
            layout: {
                padding: {
                    bottom: 30,
                }
            },
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: "white", 
                        font: {
                            size: 18, 
                            weight: "bold"
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'Sector Breakdown', 
                    color: "white", 
                    font: {
                        size: 24
                    }, 
                    padding: {
                        top: 10, 
                        bottom: 60,
                    }
                }, 
                datalabels: {
                    color: "white",
                    anchor: "end", 
                    align: "end", 
                    offset: 10,
                    font: {
                        weight: "bold", 
                        size: 16,
                    }, 
                    formatter: function(value, context) {
                        const total = sectorValues.reduce((a, b) => a + b, 0)
                        const percentage = ((value / total) * 100).toFixed(2)

                        return `${percentage}%`
                    }, 
                },
                tooltip: {
                    callbacks: {
                    label: function(context) {
                        const total = sectorValues.reduce((a, b) => a + b, 0)
                        const percentage = ((context.raw / total) * 100).toFixed(2)

                        return `${context.label}: $${context.raw.toLocaleString()} (${percentage}%)`
                        }
                    }
                }
            }
        }
    })
}

document.addEventListener("DOMContentLoaded", loadBreakdown)