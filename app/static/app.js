// Restriccion de UI para el rol "consulta": evita copiar texto en pantalla.
// Nota: esto es una restriccion de interfaz, no una medida de seguridad.
// Un usuario con conocimientos tecnicos puede evadirla desde las
// herramientas de desarrollador del navegador. Se documenta esta
// limitacion en docs/quickstart.md.

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
