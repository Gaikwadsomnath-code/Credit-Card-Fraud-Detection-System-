// static/js/script.js
document.addEventListener('DOMContentLoaded', function () {
    const safeTxns = parseInt(document.getElementById('txnChart').dataset.safe);
    const fraudTxns = parseInt(document.getElementById('txnChart').dataset.fraud);

    const ctx = document.getElementById('txnChart').getContext('2d');
    const myChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Safe', 'Fraud'],
            datasets: [{
                label: 'Transactions',
                data: [safeTxns, fraudTxns],
                backgroundColor: [
                    'rgba(54, 162, 235, 0.7)',
                    'rgba(255, 99, 132, 0.7)'
                ],
                borderColor: [
                    'rgba(54, 162, 235, 1)',
                    'rgb(255, 99, 107)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
});
