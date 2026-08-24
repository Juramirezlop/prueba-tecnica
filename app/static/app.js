// Restriccion para el rol "consulta": evita copiar texto en pantalla.

(function () {
    if (!document.body.classList.contains("rol-consulta")) {
        return;
    }

    document.addEventListener("copy", function (evento) {
        evento.preventDefault();
    });

    document.addEventListener("contextmenu", function (evento) {
        evento.preventDefault();
    });
})();
