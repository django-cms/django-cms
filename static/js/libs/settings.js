// This JavaScript file is created by Cision and holds settings for all our client modules.
// This file works as a config file for all the modules and here you will find general settings 
// and a specific sektion for each module with its access key that is used to fetch the data from our API. 

var cision = cision || {};
cision.websolution = cision.websolution || {};
cision.websolution.settings = cision.websolution.settings || {};

cision.websolution.settings = {
    general: {
        // Settings that apply to all modules 
        serviceEndpoint: 'https://publish.ne.cision.com/papi/',
        uiLanguage: 'en',
        useProxyHandler: false,
        // proxyHandler: 'ProxyCallsHttpHandler.ashx',
        startDate: '',
        endDate: '',
        pageIndex: 0,
        pageSize: 5,
        maxAmountOfItems: 10,
        numberFormatOptions: {
            thousandSeparator: ' ',
            decimalSeparator: ',',
            decimalPrecision: 2
        },
        dateFormatOptions: {
            dateTimeFormat: 'DD MMM YYYY HH:mm',
            dateFormat: 'DD MMM YYYY',
            timeFormat: 'HH:mm'
        },

        // Newsfeed specific settings
        separateFirstRelease: false,
        introMaxLength: 155,
        titleMaxLength: null,
        newsfeedYearsStartYear: 1980,

        // ownership specific settings
        LargestPieShowCount: 25,
        LargestListShowCount: 25,

        // Calendar specific settings
        separateFirstEvent: false,

        // Printed Material specific settings
        printedMaterialCategory: '',

        // Ticker specific settings
        tickerImageMinus: "Images/down.png",
        tickerImagePlus: "Images/up.png",
        tickerImageUnchanged: "Images/unadjusted.png",

        //Share calculator specific settings
        startDateYear: 2007,

        // Sharegraph specific settings
        chartContainerId: 'sharegraph-container',
        chartTitle: '',
        backgroundImage: '',
        lineWidth: 2,
        gridLineWidth: '0',
        plotBackgroundColor: 'white',
        plotBorderWidth: '0',
        defaultSeriesType: 'spline', //area, areaspline, bar, column, line, pie, scatter, spline, candlestick or ohlc, arearange, areasplinerange and columnrange.
        chartComparison: 'none', /* Default comparison type */
        typeOfChart: 'EndOfDay',
        showVolume: true,
        showHorisontalTicker: true,
        useHighchartsElements: false, // enabling highcharts own exports and range selectors, can be used if cisions custom ones are removed 
        enableLegend: false,
        enableScrollbar: false,
        enableNavigator: true,
        dividendType: 'Annual', // Annual, Bonus, Monthly, Quarterly, HalfYear 
        effectiveYieldSuffix: 'EFFECTIVEYIELD',
        yAxisSize: { share: { top: 0, height: 250 }, volume: { top: 300, height:80 } }, // sizes for the share graph and the volume graph. only applies when volume is displayed
        mainInstruments: [ /* Array of instruments to consider primary while others become Peers and Indexes */
            { symbol: 'OVZON', marketPlace: 'FNSE', currency: 'SEK', name: 'Ovzon test data', hasEffectiveYield: false }
        ],
        indexInstruments: [
            { symbol: 'FNSESEKPI', marketPlace: 'XSTO', currency: 'SEK', name: 'First North Sweden SEK PI' }
        ],
        peersInstruments: [
            //{ symbol: 'OVZON', marketPlace: 'XSTO', currency: 'SEK', name: 'Tele 2' }
        ],
        instrumentColors: [
            { uniqueKey: 'OVZONFNSESEK', preferredColor: '#FF6C36' },
            { uniqueKey: 'FNSESEKPIXSTOSEK', preferredColor: '#4286f4' },
            { uniqueKey: 'OVZONFNSESEKVOLUME', preferredColor: '#FF6C36' }
        ],
        // Displaying releases, reports, insiders and dividend in the graph.
        // If the indicators should be attached to a line in the graph add correct symbol, marketplace and currency as seriesId otherwise it will stick to the bottom
        // shape = squarepin, flag or circlepin
        indicatorsOnSeries: [
            { uniqueKey: 'Regulatory RPT', translationKey: 'TextReport', seriesId: 'OVZONFNSESEK', shape: 'circlepin', title: 'R', shapeColor: '#FF6C36', shapeOutlineColor: '#FF6C36', shapeTextColor: 'white' },  
            { uniqueKey: 'Regulatory PRM', translationKey: 'TextPress', seriesId: '', shape: 'circlepin', title: 'P', shapeColor: '#FF6C36', shapeOutlineColor: '#FF6C36', shapeTextColor: 'white' },
            { uniqueKey: 'INSIDERS', translationKey: 'TextInsider', shape: 'flag', title: 'INS', shapeColor: '#a4c5fc', shapeOutlineColor: '#4970af', shapeTextColor: 'black' },
            { uniqueKey: 'DIVIDEND', translationKey: 'TextDividend', shape: 'squarepin', title: 'U', shapeColor: '#ecefbf', shapeOutlineColor: '#bec18d', shapeTextColor: 'black' }  
        ],
        // Sharegraph releases specific settings
        showReleaseLink: true,
        enableReleasesOnIntraday: true,
        releaseLinkFormatter: 'https://publish.ne.cision.com/Release/ViewReleaseHtml/',

        // Estimates specific settings
        estimateCurrency: '', // should never be necessary, filters out data with specific currency in the same data set 
        field: 'SALES' /* default historical graph choose between SALES/EBIT/DPS/EPS */,
        valuePrefix: '',
        valueSuffix: ' SEK',
        tooltipHeaderEstimate: "Estimate - ",
        tooltipHeaderReal: "Actual - ",
        tooltipDateLabel: "",
        tooltipAmountLabel: "",
        suffixEstimate: ' FC',
        suffixActual: '',
        periodStart: '',
        periodEnd: '',
        dateString: "",
        amountString: "",
        hideEstimateIfActualExists: true,

        //stores data if ownership tab is rendered
        ownershipTabLoaded: [],
        //stores data if estimate tab is rendered
        estimateTabLoaded: [],
        cisionChartsColors: [
            { uniqueKey: 'gray', preferredColor: '#5C5C61' },
            { uniqueKey: 'blue', preferredColor: '#00607f' },
            { uniqueKey: 'orange', preferredColor: '#ff6c36' }
        ]
    },
    // All accesskeys from source WebSolutions demo
    orderbook: {
        accessKey: 'F1C02FCDB1F4418DBC0B46EB80A8ACF5'
    },
    ownership: {
        accessKey: ''
    },
    estimate: {
        accessKey: '',
        accessKeyTicker: ''
    },
    ticker: {
        accessKey: 'F96270AF6EA64AD1886A44EF431B1001'
    },
    sharegraph: {
        accessKey: '8142C82A78CA4D779EB0BC716D8448DF',
        shareHistoryKey: '04BF3D4F53A5471AB0B40C85AA68A194'
    },
    sharecalculator: {
        accessKey: '75DDB493E0DD4AB797AB75BA7E3BD8D1'
    },
    minisharegraph: {
        accessKey: '8142C82A78CA4D779EB0BC716D8448DF'
    },
    newsfeed: {
        accessKey: 'B6B94687E7F4488FB0DE9168DB52BA06'
    },
    mediafeed: {
        accessKey: 'B6B94687E7F4488FB0DE9168DB52BA06'
    },
    insider: {
        accessKey: ''
    },
    calendar: {
        accessKey: ''
    },
    printedMaterial: {
        accessKey: ''
    },
    totalreturn: {
        accessKey: ''
    }
};

// Switch moment language
try {
    moment.locale(cision.websolution.settings.general.uiLanguage);
} catch (e) {
    console.log(e);
}

try {
    Highcharts.setOptions({
        lang: {
            decimalPoint: cision.websolution.settings.general.numberFormatOptions.decimalSeparator,
            thousandsSep: cision.websolution.settings.general.numberFormatOptions.thousandSeparator
        }
    });
} catch (e) {
    console.log(e);
}

$(function () {
    $("footer").load("footer.html");
    $("header").load("menu.html");
});