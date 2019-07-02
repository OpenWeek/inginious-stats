//js for template

function submitForm() {
    alert("Submitting form");
    let from = $("#stats_from").val();
    let to = $("#stats_to").val();
    alert("Data: from: " + from + " to: " + to);
}


// Placeholders for a chart
window.onload = function() {
    // Data placeholder
    const max = 100;
    data = []
    for (let i=0; i<=20; i++) {
        let tmp = Math.floor(max * Math.random());
        data[i] = tmp;
    }
    console.log(data);

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
						labelString: 'Number of submissions'
					}
                }]
            }
        }
    });
};

