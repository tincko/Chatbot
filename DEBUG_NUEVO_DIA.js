// Test para verificar que el modal funciona
// Pega esto en la consola del navegador:

// 1. Verificar estado actual
console.log("soloMode:", window.App?.state?.soloMode);
console.log("patient_name:", window.App?.state?.config?.patient_name);
console.log("showNewDayModal:", window.App?.state?.showNewDayModal);

// 2. Simular click en botón
const buttons = document.querySelectorAll('button');
const nuevoDiaBtn = Array.from(buttons).find(btn => btn.textContent.includes('Nuevo Día'));
console.log("Botón encontrado:", nuevoDiaBtn);
if (nuevoDiaBtn) {
    console.log("Clicando botón...");
    nuevoDiaBtn.click();
} else {
    console.log("Botón NO encontrado en el DOM");
}
