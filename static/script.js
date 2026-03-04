const eventSource = new EventSource("/progress");

eventSource.onmessage = function(event){

let percent = event.data;

document.getElementById("progress_text").innerText = "Progress: " + percent;

let number = parseFloat(percent);

if(!isNaN(number)){

document.getElementById("bar").style.width = number + "%";

}

};