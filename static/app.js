document.getElementById('scanForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const url = document.getElementById('urlInput').value;
    const resultsList = document.getElementById('resultsList');
    const resultsContainer = document.getElementById('results');
    const downloadLink = document.getElementById('downloadLink');

    resultsList.innerHTML = '';
    resultsContainer.classList.add('hidden');
    downloadLink.classList.add('hidden');

    try {
        const response = await fetch('/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        for (let key in data) {
            if (key !== 'pdf_report') {
                const li = document.createElement('li');

                if (typeof data[key] === 'object' && data[key] !== null) {
                    const subList = document.createElement('ul');
                    for (let subKey in data[key]) {
                        const subLi = document.createElement('li');
                        subLi.textContent = `${subKey}: ${data[key][subKey]}`;
                        subList.appendChild(subLi);
                    }
                    li.innerHTML = `<strong>${key}:</strong>`;
                    li.appendChild(subList);
                } else {
                    li.textContent = `${key}: ${data[key]}`;
                }

                resultsList.appendChild(li);
            }
        }

        resultsContainer.classList.remove('hidden');

        if (data.pdf_report) {
            downloadLink.href = `/reports/${data.pdf_report}`;
            downloadLink.classList.remove('hidden');
        }

    } catch (error) {
        const errorMsg = document.createElement('li');
        errorMsg.textContent = `Error: ${error.message}`;
        errorMsg.style.color = 'red';
        resultsList.appendChild(errorMsg);
        resultsContainer.classList.remove('hidden');
    }
});