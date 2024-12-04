document.addEventListener('DOMContentLoaded', function() {
    const converterForm = document.getElementById('currencyConverter');
    const resultDiv = document.getElementById('conversionResult');
    
    if (converterForm) {
        converterForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const amount = document.getElementById('amount').value;
            const fromCurrency = document.getElementById('fromCurrency').value;
            const toCurrency = document.getElementById('toCurrency').value;
            
            // Basic validation
            if (!amount || amount <= 0) {
                showResult('Please enter a valid amount', 'error');
                return;
            }
            
            if (fromCurrency === toCurrency) {
                showResult('Please select different currencies', 'error');
                return;
            }
            
            try {
                const response = await fetch('/api/convert-currency', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                    },
                    body: JSON.stringify({
                        amount: parseInt(amount),
                        from_currency: fromCurrency,
                        to_currency: toCurrency
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showResult(data.message, 'success');
                    // Refresh the page to update balances
                    setTimeout(() => window.location.reload(), 1500);
                } else {
                    showResult(data.error || 'Conversion failed', 'error');
                }
            } catch (error) {
                showResult('Error processing conversion', 'error');
                console.error('Conversion error:', error);
            }
        });
    }
    
    function showResult(message, type) {
        resultDiv.innerHTML = `<div class="alert alert-${type === 'success' ? 'success' : 'danger'}">${message}</div>`;
        setTimeout(() => {
            resultDiv.innerHTML = '';
        }, 5000);
    }
});
