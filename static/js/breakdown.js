const sectorData = JSON.parse(document.getElementById("sector-data").textContent)

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