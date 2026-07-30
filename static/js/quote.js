// setting up linear chart
const linearChart = LightweightCharts.createChart(
    document.getElementById("performance-chart__linear"),
    {
        width: document.getElementById("performance-chart__linear").clientWidth,
        height: 500,
        layout: {
            background: { color: "#181c22" },
            textColor: "#d1d4dc",
        },
        grid: {
            vertLines: { color: "#2a3441" },
            horzLines: { color: "#2a3441" },
        }
    }
)

const linearSeries = linearChart.addSeries(LightweightCharts.AreaSeries, {
    lineWidth: 2,
})

// setting up candlestick chart
const candlestickChart = LightweightCharts.createChart(
    document.getElementById("performance-chart__candlestick"),
    {
        width: document.getElementById("performance-chart__candlestick").clientWidth,
        height: 500,
        layout: {
            background: { color: "#181c22" },
            textColor: "#d1d4dc",
        },
        grid: {
            vertLines: { color: "#2a3441" },
            horzLines: { color: "#2a3441" },
        },
        rightPriceScale: {
            borderColor: "#2a3441",
        },
        timeScale: {
            borderColor: "#2a3441",
        },
    }
)

const candlestickSeries = candlestickChart.addSeries(LightweightCharts.CandlestickSeries)

// defines function for loading history into chart
async function loadHistory(series,symbol, range, formatter) {
    const response = await fetch(`/api/history?symbol=${symbol}&range=${range}`)
    const data = await response.json()

    const firstValue = data[0].close
    const lastValue = data[data.length-1].close
    const gain = lastValue >= firstValue;

    // if graph is candlestick
    if (!formatter) {
        series.applyOptions({
            upColor: "#26a69a",
            downColor: "#ef5350",

            borderUpColor: "#26a69a",
            borderDownColor: "#ef5350",

            wickUpColor: "#26a69a",
            wickDownColor: "#ef5350",
        })

        series.setData(data)
        candlestickChart.timeScale().fitContent()
    }

    else {
        series.applyOptions({
        lineColor: gain ? "#26a69a" : "#ef5350",
        topColor: gain
            ? "rgba(38, 166, 154, 0.4)"
            : "rgba(239, 83, 80, 0.4)",
        bottomColor: gain
            ? "rgba(38, 166, 154, 0)"
            : "rgba(239, 83, 80, 0)",
        })

        series.setData(data.map(formatter))
        linearChart.timeScale().fitContent()
    }
}

// defines current values
let currentGraphType = "linear"
let currentRange = "1M"
let currentSymbol = ""

//gets symbol field, 'quote' button and graph type selector
const button = document.getElementById("get-quote")
const symbolInput = document.getElementById("symbol")
const graphTypeSelector = document.getElementById("graph-type-selector")

button.addEventListener("click", async function () {
    const symbol = symbolInput.value
    currentSymbol = symbol

    if (symbol.length == 0) {
        return;
    }

    const response = await fetch(`/api/quote?symbol=${symbol}`);
    const data = await response.json()

    const sign = data.change > 0 ? "+" : data.change < 0 ? "-" : ""

    const card = document.querySelector('.quote-card');
    card.classList.toggle('is-up', sign == "+");
    card.classList.toggle('is-down', sign == "-");

    //displays immediate data about stock
    document.getElementById("symbol-show").textContent = symbol
    document.getElementById("current-price").textContent = `$${data.current_price}`
    document.getElementById("change").textContent = `${sign}$${Math.abs(data.change)}`
    document.getElementById("percent-change").textContent = `(${data.percent_change}%)`
    document.getElementById("high").textContent = `${data.high}`
    document.getElementById("low").textContent = `${data.low}`
    document.getElementById("open").textContent = `${data.open}`
    document.getElementById("previous-close").textContent = `${data.previous_close}`

    //shows chart automatically with default type (linear) and range
    const defaultRangeButton = document.querySelector(".range-btn.active")
    currentRange = defaultRangeButton.dataset.range
    if (currentGraphType == "linear") {
        document.getElementById("performance-chart__candlestick").style.display = "none"
        document.getElementById("performance-chart__linear").style.display = "flex"
        loadHistory(linearSeries,currentSymbol,currentRange,point => ({time: point.time,value: point.close}))
        }

    else {
        document.getElementById("performance-chart__linear").style.display = "none"
        document.getElementById("performance-chart__candlestick").style.display = "flex"
        loadHistory(candlestickSeries,currentSymbol,currentRange,null)
    }
})

const rangeButtons = document.querySelectorAll(".range-btn")
rangeButtons.forEach((button) => {
    button.addEventListener("click", () => {
        rangeButtons.forEach((button) => {button.classList.remove("active")})
        button.classList.add("active")

        currentRange = button.dataset.range
        
        if (currentGraphType == "linear") {
        document.getElementById("performance-chart__candlestick").style.display = "none"
        document.getElementById("performance-chart__linear").style.display = "flex"
        loadHistory(linearSeries,currentSymbol,currentRange,point => ({time: point.time,value: point.close}))
        }

        else {
            document.getElementById("performance-chart__linear").style.display = "none"
            document.getElementById("performance-chart__candlestick").style.display = "flex"
            loadHistory(candlestickSeries,currentSymbol,currentRange,null)
        }
    })
})

graphTypeSelector.addEventListener("change", async function () {
    currentGraphType = graphTypeSelector.value

    if (currentGraphType == "linear") {
        document.getElementById("performance-chart__candlestick").style.display = "none"
        document.getElementById("performance-chart__linear").style.display = "flex"
        loadHistory(linearSeries,currentSymbol,currentRange,point => ({time: point.time,value: point.close}))
        }

    else {
        document.getElementById("performance-chart__linear").style.display = "none"
        document.getElementById("performance-chart__candlestick").style.display = "flex"
        loadHistory(candlestickSeries,currentSymbol,currentRange,null)
    }
})