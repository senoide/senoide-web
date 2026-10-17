/* Trabajos publicados desde la app de SENOIDE (partes de trabajo con permiso del cliente).
   Rellena cualquier contenedor con data-trabajos="N" (N = cuántos mostrar; vacío = todos). */
(function(){
  var boxes = document.querySelectorAll('[data-trabajos]');
  var API = document.body.dataset.api || '';
  if (!boxes.length || !API || !window.fetch) return;
  var MESES = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
  function esc(t){ return String(t == null ? '' : t).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  function mes(f){ var p = String(f || '').split('-'); return p.length > 1 ? MESES[(+p[1]) - 1] + ' de ' + p[0] : ''; }
  function tarjeta(t){
    var fotos = t.fotos || [];
    var portada = fotos[0] ? '<img src="' + esc(fotos[0]) + '" alt="' + esc(t.titulo) + '" loading="lazy" width="800" height="600">' : '';
    var mini = fotos.length > 1 ? '<div class="thumbs">' + fotos.map(function(u, i){ return '<a href="' + esc(u) + '" target="_blank" rel="noopener"><img src="' + esc(u) + '" alt="' + esc(t.titulo) + ', foto ' + (i + 1) + '" loading="lazy"></a>'; }).join('') + '</div>' : '';
    var meta = [t.municipio, t.servicio, mes(t.fecha)].filter(Boolean).join(' · ');
    return '<article class="card static">' + portada + '<div class="body"><span class="meta">' + esc(meta) + '</span><h3>' + esc(t.titulo) + '</h3><p>' + esc(t.resumen) + '</p></div>' + mini + '</article>';
  }
  fetch(API + '/api/trabajos').then(function(r){ return r.ok ? r.json() : {trabajos: []}; }).then(function(j){
    var L = (j && j.trabajos) || [];
    if (!L.length) return;
    boxes.forEach(function(b){
      var n = +b.dataset.trabajos || L.length;
      b.insertAdjacentHTML('beforeend', L.slice(0, n).map(tarjeta).join(''));
      var sec = b.closest('section'); if (sec) sec.hidden = false;
      var vacio = document.getElementById('trabajos-vacio'); if (vacio) vacio.hidden = true;
    });
  }).catch(function(){});
})();
