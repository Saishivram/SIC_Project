const API = "http://127.0.0.1:5000";



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
        pregnancies: parseFloat(pregnancies.value),
        glucose: parseFloat(glucose.value),
        bp: parseFloat(bp.value),
        skin: parseFloat(skin.value),
        insulin: parseFloat(insulin.value),
        bmi: bmi,
        dpf: dpf,
        age: parseFloat(age.value),
        email: email.value
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