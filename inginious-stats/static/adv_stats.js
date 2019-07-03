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


const chartTypeCorrespondence = {
    "grades-distribution": "bar",
    "submission-before-perfect": "bar",
    "lines-per-submission": "bar",
    "submissions-time": "line",
    "tag-sorted": "bar"
}
const chartTypeLabelCorrespondence = {
    "grades-distribution": [...Array(21).keys()],
    "submission-before-perfect": [...Array(31).keys()],
    "lines-per-submission": [...Array(201).keys()],
    "submissions-time": ["lundi", "mardi", "mercredi","TODO"],
    "tag-sorted": ["Timeout", "Segfault", "Cannot compile", "Could compile"]
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

    var ctx = document.getElementById('canvas').getContext('2d');
    var myChart = new Chart(ctx, {
        type: chartTypeCorrespondence[chartTypeStr],
        data: {
            labels: chartTypeLabelCorrespondence[chartTypeStr],
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

