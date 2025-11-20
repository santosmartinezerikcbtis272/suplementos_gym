function addToCart(productId) {
    fetch(`/add_to_cart/${productId}`)
    .then(response => {
        if(response.ok){
            showAlert("Producto agregado al carrito");
        } else {
            showAlert("Error al agregar el producto", true);
        }
    })
    .catch(err => console.error(err));
}

// Alerta flotante
function showAlert(message, error=false){
    let alertBox = document.createElement("div");
    alertBox.textContent = message;
    alertBox.style.position = "fixed";
    alertBox.style.top = "20px";
    alertBox.style.right = "20px";
    alertBox.style.padding = "15px 25px";
    alertBox.style.backgroundColor = error ? "#e74c3c" : "#27ae60";
    alertBox.style.color = "#fff";
    alertBox.style.borderRadius = "10px";
    alertBox.style.boxShadow = "0 4px 15px rgba(0,0,0,0.2)";
    alertBox.style.zIndex = 1000;
    document.body.appendChild(alertBox);
    setTimeout(()=>{ alertBox.remove(); }, 2500);
}
