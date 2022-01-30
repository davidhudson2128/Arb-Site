console.log("test")
document.body.onload = addElement;

function addElement () {
    
    var andrewsSection = document.getElementById("andrewsSection")
    
    console.log(andrewsSection)
    
    newHeader = andrewsSection.appendChild(document.createElement("h1"))
    newHeader.innerHTML = "CHICKEN"
}