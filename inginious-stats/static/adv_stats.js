function fillFilters(query) {
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


function makeChart() {
    // Data placeholder
    const max = 100;
    data = []
    for (let i=0; i<=20; i++) {
        let tmp = Math.floor(max * Math.random());
        data[i] = tmp;
    }

    var ctx = document.getElementById('canvas').getContext('2d');
    var myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [...Array(21).keys()],
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
                        labelString: 'Number of submission'
                    }
                }]
            }
        }
    });
}

