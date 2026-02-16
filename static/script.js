const API = "http://localhost:5000";

function handleGenderChange() {
    const gender = document.getElementById("gender").value;
    const pregInput = document.getElementById("pregnancies");

    if (gender === "male") {
        pregInput.value = 0;
        pregInput.disabled = true;
    } else {
        pregInput.disabled = false;
    }
}


function calculateBMI() {

    const w = parseFloat(document.getElementById("weight").value);

    const h = parseFloat(document.getElementById("height").value);

    if (w && h) {

        const bmi = w / (h * h);

        document.getElementById("bmiDisplay").innerText =

            "BMI: " + bmi.toFixed(2);

        return bmi;

    }

    return 0;

}



function calculateDPF() {
    const relatives = parseFloat(document.getElementById("relatives").value) || 0;
    const avgAge = parseFloat(document.getElementById("avgAge").value) || 50;

    /*
    Normalize into dataset-like range
    PIMA DPF typically ranges from 0 to ~2.5
    */

    let dpf = (relatives / 5) * (60 / avgAge);

    // clamp to dataset range
    dpf = Math.min(Math.max(dpf, 0.05), 2.5);

    document.getElementById("dpfDisplay").innerText =
        "DPF: " + dpf.toFixed(3);

    return dpf;
}


document.getElementById("gender").addEventListener("change", handleGenderChange);
handleGenderChange();

document.getElementById("weight").addEventListener("input", calculateBMI);

document.getElementById("height").addEventListener("input", calculateBMI);

document.getElementById("relatives").addEventListener("input", calculateDPF);

document.getElementById("avgAge").addEventListener("input", calculateDPF);



document.getElementById("predictForm").addEventListener("submit", async function(e) {
    e.preventDefault();

    document.getElementById("loadingOverlay").style.display = "flex";

    const bmi = calculateBMI();
    const dpf = calculateDPF();

    const payload = {
    pregnancies: parseFloat(document.getElementById("pregnancies").value),
    glucose: parseFloat(document.getElementById("glucose").value),
    bp: parseFloat(document.getElementById("bp").value),
    skin: parseFloat(document.getElementById("skin").value),
    insulin: parseFloat(document.getElementById("insulin").value),
    bmi: bmi,
    dpf: dpf,
    age: parseFloat(document.getElementById("age").value),
    name: document.getElementById("name").value,
    email: document.getElementById("email").value
    };


    const res = await fetch(`${API}/predict`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
    });

    const data = await res.json();

    document.getElementById("loadingOverlay").style.display = "none";

    document.getElementById("result").style.display = "block";
    document.getElementById("result").innerText = data.message;

    if (data.risk) {
        document.getElementById("riskBox").style.display = "block";
        document.getElementById("riskBox").innerText =
            "Predicted Diabetes Risk: " + (data.risk * 100).toFixed(2) + "%";
    }
});




function downloadReport() {

    window.location.href = `${API}/download`;

}



async function chat() {

    const q = document.getElementById("question").value;



    const res = await fetch(`${API}/chat`, {

        method: "POST",

        headers: {"Content-Type": "application/json"},

        body: JSON.stringify({question: q})

    });



    const data = await res.json();

    document.getElementById("chatResponse").innerText = data.answer;

}