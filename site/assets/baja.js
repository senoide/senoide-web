/* Formulario de baja del mantenimiento (senoide.es/baja/). Envía a la app de gestión, que guarda la solicitud y manda el acuse con la fecha de recepción. */
(function(){
  var f = document.getElementById('baja-form'); if (!f) return;
  var API = document.body.dataset.api || '', $ = function(id){ return document.getElementById(id); }, enviando = false;
  var hoy = new Date(); var iso = hoy.getFullYear() + '-' + String(hoy.getMonth() + 1).padStart(2, '0') + '-' + String(hoy.getDate()).padStart(2, '0');
  $('b-fecha').min = iso;
  function alc(){ $('b-aptos-w').hidden = !$('b-alc-aptos').checked; }
  $('b-alc-todo').addEventListener('change', alc); $('b-alc-aptos').addEventListener('change', alc); alc();
  function modo(){ var m = document.querySelector('input[name="b-modo"]:checked'); return m ? m.value : 'recepcion'; }
  function verFecha(){ $('b-fecha-w').hidden = modo() !== 'fecha'; }
  ['recepcion','finmes','fecha'].forEach(function(k){ $('b-modo-' + k).addEventListener('change', verFecha); }); verFecha();
  function msg(t, ok){ var m = $('b-msg'); m.className = 'send-msg ' + (ok ? 'ok' : 'err'); m.innerHTML = t; }
  f.addEventListener('submit', function(e){
    e.preventDefault(); if (enviando) return;
    var d = {nombre: $('b-nombre').value.trim(), email: $('b-email').value.trim(), telefono: $('b-tel').value.trim(), contrato: $('b-contrato').value.trim(),
      alcance: $('b-alc-aptos').checked ? 'apartamentos' : 'todo', apartamentos: $('b-aptos').value.trim(), modo: modo(), fecha: modo() === 'fecha' ? $('b-fecha').value : '', comentario: $('b-com').value.trim(),
      privacidad: $('b-priv').checked, web: $('b-web').value};
    if (d.nombre.length < 2){ msg('Escribe el nombre del titular del contrato.'); $('b-nombre').focus(); return; }
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(d.email)){ msg('Escribe un correo válido: ahí te confirmamos la baja.'); $('b-email').focus(); return; }
    if (d.alcance === 'apartamentos' && d.apartamentos.length < 2){ msg('Indica qué apartamentos das de baja.'); $('b-aptos').focus(); return; }
    if (d.modo === 'fecha' && !d.fecha){ msg('Elige la fecha de efecto.'); $('b-fecha').focus(); return; }
    if (d.fecha && d.fecha < iso){ msg('La fecha de efecto no puede ser anterior a hoy.'); $('b-fecha').focus(); return; }
    if (!d.privacidad){ msg('Marca la casilla de la política de privacidad.'); $('b-priv').focus(); return; }
    if (!API){ msg('Ahora mismo no podemos recibirla desde aquí. Escríbenos a info@senoide.es, por favor.'); return; }
    enviando = true; var b = $('b-send'); b.disabled = true; b.textContent = 'Enviando…';
    fetch(API + '/api/baja', {method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify(d)})
      .then(function(r){ return r.json().catch(function(){ return {}; }).then(function(j){ return {ok: r.ok, j: j}; }); })
      .then(function(x){
        if (x.ok && x.j.ok){ msg('<b>Solicitud de baja recibida</b> el ' + new Date(x.j.recibida).toLocaleString('es-ES', {dateStyle: 'long', timeStyle: 'short'}) + '. Te hemos enviado el justificante a tu correo y te confirmaremos la baja por escrito. No tienes que hacer nada más.', true); b.textContent = 'Solicitud enviada'; }
        else { msg((x.j && x.j.error ? x.j.error : 'No se ha podido enviar.') + ' También puedes escribirnos a info@senoide.es.'); b.disabled = false; b.textContent = 'Enviar la solicitud de baja'; }
      })
      .catch(function(){ msg('No se ha podido enviar (sin conexión o servidor no disponible). Escríbenos a info@senoide.es o por WhatsApp al 621 018 374.'); b.disabled = false; b.textContent = 'Enviar la solicitud de baja'; })
      .then(function(){ enviando = false; });
  });
})();
