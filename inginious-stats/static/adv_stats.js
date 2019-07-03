/* JS for template */
function fillFilters(query) {
    /* Sets all the filters with the value that was requested by the user. */
    if (query.chart_type) {
        $("#chart_type")[0].value = query.chart_type;
    }
    $("#submissions_filter_" + query.submissions_filter)[0].checked = true;
    if (query.min_submission_grade) {
        $("#min_submission_grade")[0].value = query.min_submission_grade;
    }
    if (query.max_submission_grade) {
        $("#max_submission_grade")[0].value = query.max_submission_grade;
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
function addStatsTable() {
    /* Creates and puts a table of statistics requested by the user on the page. */
    $("#table-count")[0].innerHTML = Math.floor(100 * Math.random());
    $("#table-min")[0].innerHTML = Math.floor(100 * Math.random());
    $("#table-max")[0].innerHTML = Math.floor(100 * Math.random());
    $("#table-mean")[0].innerHTML = Math.floor(100 * Math.random());
    $("#table-median")[0].innerHTML = Math.floor(100 * Math.random());
    $("#table-mode")[0].innerHTML = Math.floor(100 * Math.random());
    $("#table-variance")[0].innerHTML = Math.floor(100 * Math.random());
    $("#table-std-deviation")[0].innerHTML = Math.floor(100 * Math.random());
}

//============== Charts ====================
const chartTypeCorrespondence = {
    "grades-distribution": makeGradeDistroChart,
    "submission-before-perfect": makeNbSubmissionsBfPerfectChart,
    "lines-per-submission": makeLinePerSubmissionChart,
    "submissions-time": makeSubmissionTimeGraph,
    "tag-sorted": makeTagSortedChart
}

function makeChart(chartTypeStr) {
    /* Creates the chart requested by the user and adds it to the page. */
    // Data placeholder
    const max = 100;
    data = []
    for (let i=0; i<=20; i++) {
        let tmp = Math.floor(max * Math.random());
        data[i] = tmp;
    }

    chartTypeCorrespondence[chartTypeStr](data);
}

function makeGradeDistroChart(data) {
    const labels = _createConsecutiveLabels(0, 101, 20);
    _displayChart("bar", labels, data);
}
function makeNbSubmissionsBfPerfectChart(data) {
    const min = 10; // TODO find min from data
    const max = 31; // TODO find max from data // TODO max is not included
    const processedData = _groupBars(data);
    const labels = _createConsecutiveLabels(min, max);
    _displayChart("bar", labels, data);
}
function makeLinePerSubmissionChart(data) {
    const min = 5; // TODO find min from data
    const max = 201; // TODO find max from data // TODO max is not included
    const processedData = _groupBars(data);
    const labels = _createConsecutiveLabels(min, max);
    _displayChart("bar", labels, data);
}
function makeSubmissionTimeGraph(data) {
    _displayChart("line", ["lundi", "mardi", "mercredi", "TODO"], data);
}
function makeTagSortedChart(data) {
    _displayChart("bar", ["Timeout", "Segfault", "Cannot compile", "Could compile"], data);
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
        newGroups[newGroups.length-1] += acc;
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
        let words = lastLabel.split(" ");
        labels[labels.length-1] = words[0] + " " + words[1] + " " + (max-1);
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

