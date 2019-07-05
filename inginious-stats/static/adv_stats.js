/* JS for template */
function checkMinMax() {
    /* Checks that the min and max (for grades) provided by the user are valid. */
    let min = $("#min_submission_grade")[0].value;
    let max = $("#max_submission_grade")[0].value;
    if (min.endsWith('%'))
        min = parseFloat(min.slice(0, -1));
    if (max.endsWith('%'))
        max = parseFloat(max.slice(0, -1));
    if (min > max)
        alert("Warning: inconsistent grade boundaries (min > max)");
}

function fillFilters(query) {
    /* Sets all the filters with the value that was requested by the user. */
    if (query.chart_type) {
        $("#chart_type")[0].value = query.chart_type;
    }
    $("#submissions_filter_" + query.submissions_filter)[0].checked = true;
    if (query.min_submission_grade) {
        $("#min_submission_grade")[0].value = query.min_submission_grade + '%';
    }
    if (query.max_submission_grade) {
        $("#max_submission_grade")[0].value = query.max_submission_grade + '%';
    }
    if (query.stats_from) {
        $("#stats_from")[0].value = query.stats_from;
    }
    if (query.stats_to) {
        $("#stats_to")[0].value = query.stats_to;
    }
    if (query.filter_tags) {
        $("#filter_tags")[0].value = query.filter_tags;
    }
    if (query.filter_exercises) {
        $("#filter_exercises")[0].value = query.filter_exercises;
    }
}

//=========== Table ==================
function addStatsTable(stats) {
    if (stats === undefined) {
        stats = {
            count: "N/A",
            min: "N/A",
            max: "N/A",
            mean: "N/A",
            median: "N/A",
            mode: "N/A",
            variance: "N/A",
            std_deviation: "N/A"
        };
    }
    /* Creates and puts a table of statistics requested by the user on the page. */
    $("#table-count")[0].innerHTML = stats.count;
    $("#table-min")[0].innerHTML = stats.min;
    $("#table-max")[0].innerHTML = stats.max;
    $("#table-mean")[0].innerHTML = stats.mean;
    $("#table-median")[0].innerHTML = stats.median;
    $("#table-mode")[0].innerHTML = stats.mode;
    $("#table-variance")[0].innerHTML = stats.variance;
    $("#table-std-deviation")[0].innerHTML = stats.std_deviation;
}

//============== Charts ====================
const chartTypeCorrespondence = {
    "grades-distribution": makeGradeDistroChart,
    "submission-before-perfect": makeNbSubmissionsBfPerfectChart,
    "lines-per-submission": makeLinePerSubmissionChart,
    "submissions-time": makeSubmissionTimeGraph,
    "tag-sorted": makeTagSortedChart
}

function makeChart(chartQuery, dataPoints) {
    /* Creates the chart requested by the user and adds it to the page. */
    if (dataPoints === undefined) {
        _showEmptyChart();
        return;
    }

    const chartTypeStr = chartQuery.chart_type;

    // Data placeholder
    const max = 100;
    data = []
    for (let i=0; i<=20; i++) {
        let tmp = Math.floor(max * Math.random());
        data[i] = tmp;
    }

    if ((chartTypeStr == "grades-distribution" || chartTypeStr == "submission-before-perfect") && dataPoints)
        chartTypeCorrespondence[chartTypeStr](chartQuery, dataPoints);
    else
        chartTypeCorrespondence[chartTypeStr](chartQuery, data);
}

function makeGradeDistroChart(query, rawData) {
    // TODO This doesn't work for non integer numbers in `rawData`
    const nbBars = 20;
    const bars = _computeBarSizes(
        "real", rawData, nbBars, parseFloat(query.min_submission_grade), parseFloat(query.max_submission_grade));
    if (bars) {
        const data = bars["bars"];
        const labels = bars["labels"];
        _displayChart("bar", labels, data);
    } else {
        _showEmptyChart();
    }
}
function makeNbSubmissionsBfPerfectChart(query, rawData) {
    const min = 0;
    const nbBars = 100;
    const bars = _computeBarSizes(
        "discrete", rawData, nbBars, min
    )
    if (bars) {
        const data = bars["bars"];
        const labels = bars["labels"];
        _displayChart("bar", labels, data);
    } else {
        _showEmptyChart();
    }
}
function makeLinePerSubmissionChart(query, data) {
    const min = 5; // TODO find min from data
    const max = 201; // TODO find max from data // TODO max is not included
    const processedData = _groupBars(data);
    const labels = _createConsecutiveLabels(min, max);
    _displayChart("bar", labels, data);
}
function makeSubmissionTimeGraph(query, data) {
    _displayChart("line", ["lundi", "mardi", "mercredi", "TODO"], data);
}
function makeTagSortedChart(query, data) {
    _displayChart("bar", ["Timeout", "Segfault", "Cannot compile", "Could compile"], data);
}


function _computeBarSizes(discreteOrReal, rawData, nbBuckets, min=undefined, max=undefined) {
    if (min === undefined)
        min =  Math.min.apply(null, rawData);
    if (max === undefined)
        max = Math.max.apply(null, rawData);
    const valuesPerBucket = Math.max(1, Math.floor((max - min) / nbBuckets));

    if (nbBuckets > max - min)
        nbBuckets = Math.ceil(max - min);
    if (nbBuckets < 0)
        return null;
    else if (nbBuckets == 0)
        nbBuckets = 1;
    while (max - min >= valuesPerBucket*nbBuckets)
        nbBuckets += 1;

    let result = new Array(nbBuckets).fill(0);

    for (let pt of rawData)
        result[Math.floor((pt - min) / valuesPerBucket)] += 1;
    

    let labels = [];
    if (discreteOrReal == "real" || valuesPerBucket > 1) {
        for (let i = 0; i < nbBuckets-1; i++) {
            const startBucket = min + i*valuesPerBucket;
            const endBucket = min + (i+1)*valuesPerBucket;
            labels.push(startBucket + " to " + endBucket);
        }
        const startLastBucket = min + (nbBuckets-1)*valuesPerBucket;
        if (startLastBucket == max)
            labels.push(max);
        else
            labels.push(startLastBucket + " to " + max);
    } else { // discrete
        for (let i = 0; i < nbBuckets-1; i++) {
            const startBucket = min + i*valuesPerBucket;
            labels.push(startBucket);
        }
        labels.push(max);
    }

    return {"bars": result, "labels": labels};
}

const maxNbBars = 200; // TODO tmp, change that number
function _groupBars(dataGroups) {
    /*
     * Returns the data with less groups of data, to be able to display a readable bar chart.
     * Currently consider each group to be a number.
     */
    if (dataGroups.length <= maxNbBars)
        return dataGroups;

    newGroups = [];
    const nbGroupsPerNewGroup = Math.floor(dataGroups.length/maxNbBars);
    let i = 0;
    let acc = 0;
    for (let currentGroup of dataGroups) {
        acc += currentGroup;
        i++;
        if (i > nbGroupsPerNewGroup) {
            i = 0;
            newGroups.push(acc);
            acc = 0;
        }
    }
    if (i > 0)
        newGroups.push(acc);
    return newGroups;
}
function _createConsecutiveLabels(min, max, maxNbGroups=maxNbBars) {
    /*
     * Returns an array containing labels for each group in a bar plot.
     * Data for the bar plot is considered to be consecutive numbers,
     * groups will thus be a range of consecutive numbers.
     * `max` is not included.
     */
    const widthGroup = Math.floor((max - min)/maxNbGroups);

    if (widthGroup == 0) {
        let labels = [];
        for (let i = min; i < max; i++) 
            labels.push(i);
        return labels;
    }
    if (widthGroup == 1) {
        let labels = [];
        for (let i = 0; i < maxNbBars; i++)
            labels.push(min + i);
        return labels;
    }
  
    let labels = [];
    for (let i = 0; i < maxNbGroups; i++) {
        const current = min + i*widthGroup;
        const currentEnd = current + widthGroup - 1;
        labels.push(current + " to " + currentEnd);
    }

    if (!labels[labels.length-1].endsWith(max-1)) {
        let lastLabel = labels[labels.length-1];
        let lastNb = parseInt(lastLabel.split(" ")[2]);
        if (lastNb+1 == max-1)
            labels.push(max-1);
        else
            labels.push((lastNb+1) + " to " + (max-1));
    }
    return labels;
}

function _displayChart(type, labels, data) {
    var ctx = document.getElementById('canvas').getContext('2d');
    var myChart = new Chart(ctx, {
        type: type,
        data: {
            labels: labels,
            datasets: [{
                label: 'Placeholder',
                data: data,
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                // backgroundColor: [
                //     'rgba(255, 99, 132, 0.2)',
                //     'rgba(54, 162, 235, 0.2)',
                //     'rgba(255, 206, 86, 0.2)',
                //     'rgba(75, 192, 192, 0.2)',
                //     'rgba(153, 102, 255, 0.2)',
                //     'rgba(255, 159, 64, 0.2)'
                // ],
                borderColor: 'rgba(255, 99, 132, 1)',
                // borderColor: [
                //     'rgba(255, 99, 132, 1)',
                //     'rgba(54, 162, 235, 1)',
                //     'rgba(255, 206, 86, 1)',
                //     'rgba(75, 192, 192, 1)',
                //     'rgba(153, 102, 255, 1)',
                //     'rgba(255, 159, 64, 1)'
                // ],
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                xAxes: [{
                    scaleLabel: {
                        display: true,
                        labelString: 'Grade'
                    }
                }],
                yAxes: [{
                    ticks: {
                        beginAtZero: true
                    },
                    scaleLabel: {
                        display: true,
                        labelString: 'Number of submissions'
                    }
                }]
            }
        }
    });
}

function _showEmptyChart() {
    let canvas = document.getElementById("canvas");
    let ctx = canvas.getContext("2d");
    ctx.font = "16px Arial";
    ctx.fillStyle = "red";
    ctx.fillText("Nothing to display. lol", 10, 50);
}

