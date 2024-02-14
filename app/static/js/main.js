const containerEl = document.getElementById('container')
const leftEl = document.getElementById('left')
const rightEl = document.getElementById('right')
//#
const userEmailEl = document.getElementById('user-email')
const invalidEmailEl = document.getElementById('invalid-email')
const emailInput = document.getElementById('email')
const submitBtnEl = document.getElementById('submit-btn')
//#
const confirmedMessageEl = document.getElementById('confirmed-message')
const dismissMessageEl = document.getElementById('dismiss-message')

function formSuccess(email) {
    fetch('/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: email })  // Send email as JSON data
    })
        .then(response => response.json())  // Parse the JSON response from server
        .then(data => {
            if (data.message && data.message === "Email sent for confirmation") {
                confirmedMessageEl.classList.add('active')
                containerEl.classList.add('success')
                leftEl.style.display = 'none'
                rightEl.style.display = 'none'
            } else {
                // Handle any other server response or error message here
                console.error("Server responded with:", data.message);
            }
        })
        .catch(error => {
            // Handle network or fetch errors here
            console.error("Fetch error:", error);
        });
}

function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
}

submitBtnEl.addEventListener('click', (e) => {
    e.preventDefault()
    const email = emailInput.value.trim()

    if (validateEmail(email)) {
        formSuccess(email)
        userEmailEl.innerText = email
        emailInput.value = ''

        invalidEmailEl.classList.remove('active')
        emailInput.classList.remove('active')
    } else {
        invalidEmailEl.classList.add('active')
        emailInput.classList.add('active')
    }
})

dismissMessageEl.addEventListener('click', () => {
    leftEl.style.display = 'block'
    rightEl.style.display = 'block'
    containerEl.classList.remove('success')
    confirmedMessageEl.classList.remove('active')

})