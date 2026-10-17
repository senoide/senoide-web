
(function(){
  /* Solo la portada tiene presupuestador, pestañas y onda */
  if (!document.getElementById('catalog')) return;
  /* ===== Precios (sin IVA), modelo A del 15/10/2026 =====
     - Trabajos: precio por unidad = material de gama comercial + minutos de trabajo a 45 €/h (Excel «Precios por trabajo», columna S).
     - SALIDA (35 €) se suma UNA vez por visita cuando hay algún trabajo que no es de precio cerrado.
     - closed:1 = precio cerrado que ya incluye la visita (visita y diagnóstico, trámites, revisiones, instalaciones por m²). */
  var SALIDA = 35;
  var CATALOG = [
    /* c: a quién se muestra cada trabajo. p = particular, e = empresa o autónomo, c = comunidad. d: lo que incluye */
    {id:'g', name:'Visita y mano de obra', cable:'all', items:[
      {id:'e1', closed:1, c:'pec', name:'Visita y diagnóstico (salida y primera hora)', unit:'visita', min:65, max:65,
        d:'Para averías o cuando no sabes qué hay que hacer. Incluye la salida y la primera hora de trabajo; si es algo sencillo, lo dejamos resuelto en esa hora.'},
      {id:'e2', closed:1, c:'pec', name:'Hora adicional de trabajo', unit:'h', min:45, max:45,
        d:'Electricidad, fontanería o remates de albañilería, a partir de la primera hora.'}
    ]},
    {id:'e', name:'Electricidad', cable:'phase', items:[
      {id:'e3', c:'pe', name:'Enchufe nuevo con cableado', unit:'ud', min:38, max:38,
        d:'Caja, mecanismo y cable desde el cuadro o la caja más cercana.'},
      {id:'e4', c:'pe', name:'Punto de luz nuevo con cableado', unit:'ud', min:46, max:46,
        d:'Punto con interruptor y cableado. La lámpara no está incluida.'},
      {id:'e5', c:'pe', name:'Cambio de enchufe o interruptor existente', unit:'ud', min:18, max:18,
        d:'Mecanismo nuevo de gama comercial en la misma caja.'},
      {id:'e6', c:'p', name:'Colgar lámpara o luminaria (la aportas tú)', unit:'ud', min:23, max:23,
        d:'Montaje y conexión de la lámpara que ya tengas.'},
      {id:'e7', c:'p', name:'Cambio de cuadro eléctrico de vivienda', unit:'ud', min:396, max:396,
        d:'Cuadro nuevo con diferencial y protección para cada circuito.'},
      {id:'e8', closed:1, c:'p', name:'Boletín eléctrico (CIE) de vivienda', unit:'ud', min:185, max:185,
        d:'Revisión, certificado y registro para dar de alta la luz.'},
      {id:'e9', closed:1, c:'pe', name:'Aumento de potencia (adecuación y boletín)', unit:'ud', min:280, max:280,
        d:'Adecuación de protecciones y boletín. Las tasas de la distribuidora van aparte.'},
      {id:'e11', closed:1, c:'p', name:'Instalación eléctrica completa de vivienda', unit:'m²', min:38, max:38,
        d:'Cableado, cajas, mecanismos y cuadro nuevos, con boletín.'},
      {id:'e12', closed:1, c:'e', name:'Boletín eléctrico (CIE) de local u oficina', unit:'ud', min:280, max:280,
        d:'Revisión y certificado de la instalación para dar de alta la luz del local.'},
      {id:'e13', closed:1, c:'e', name:'Adecuación del cuadro eléctrico del local', unit:'ud', min:550, max:550,
        d:'Cuadro nuevo o ampliado con las protecciones que necesita el local.'},
      {id:'e14', closed:1, c:'e', name:'Instalación eléctrica de local u oficina', unit:'m²', min:45, max:45,
        d:'Líneas, cajas, mecanismos y cuadro nuevos, con boletín.'},
      {id:'e15', c:'e', name:'Luminaria LED de techo (panel o downlight)', unit:'ud', min:33, max:33,
        d:'Luminaria LED de gama comercial, instalada y conectada.'},
      {id:'e16', c:'e', name:'Toma de red de datos (RJ45)', unit:'ud', min:42, max:42,
        d:'Toma con cableado desde el router o el armario de red.'},
      {id:'e17', c:'ec', name:'Luz de emergencia', unit:'ud', min:50, max:50,
        d:'Luz de emergencia autónoma, instalada y probada.'},
      {id:'e19', closed:1, c:'e', name:'Revisión puntual de apartamento turístico (sin contrato)', unit:'visita', min:150, max:150,
        d:'Revisión de electricidad, termo y grifos. Las piezas o reparaciones se presupuestan aparte. Con un plan de mantenimiento sale más barato.'},
      {id:'e20', closed:1, c:'ec', name:'Visita de mantenimiento preventivo', unit:'visita', min:90, max:90,
        d:'Revisión periódica de cuadros, protecciones e iluminación, con parte de trabajo. Las reparaciones que salgan se presupuestan aparte.'},
      {id:'e21', closed:1, c:'c', name:'Revisión de la instalación de zonas comunes, con informe', unit:'ud', min:150, max:150,
        d:'Revisamos cuadros, protecciones e iluminación de portal, escaleras y garaje. Las reparaciones que salgan se presupuestan aparte.'},
      {id:'e22', c:'c', name:'Luminaria LED con detector para portal o escalera', unit:'ud', min:50, max:50,
        d:'Luz LED que se enciende sola al pasar y gasta mucho menos.'},
      {id:'e23', c:'c', name:'Detector de presencia o temporizador de escalera', unit:'ud', min:25, max:25,
        d:'Para que la luz de zonas comunes no se quede encendida.'},
      {id:'e24', c:'c', name:'Luminaria LED estanca para garaje', unit:'ud', min:43, max:43,
        d:'Luminaria LED resistente a la humedad y al polvo.'}
    ]},
    {id:'v', name:'Recarga de coche eléctrico', cable:'phase', items:[
      {id:'v1', c:'pec', name:'Punto de recarga con cargador de 7,4 kW (hasta 10 m de línea)', unit:'ud', min:1073, max:1073,
        d:'Línea desde tu cuadro o contador, protecciones, cargador de gama comercial y certificado.'},
      {id:'v2', c:'pec', name:'Metro adicional de línea', unit:'m', min:12, max:12,
        d:'Si el cargador queda a más de 10 m del cuadro o del contador. En garajes comunitarios suele hacer falta.'},
      {id:'v3', closed:1, c:'pec', name:'Suplemento por cargador trifásico (11–22 kW)', unit:'ud', min:300, max:300,
        d:'Si tienes o quieres suministro trifásico para cargar más rápido.'}
    ]},
    {id:'f', name:'Fontanería', cable:'neutral', items:[
      {id:'f1', c:'pe', name:'Cambio de grifo', unit:'ud', min:87, max:87,
        d:'Grifo de gama comercial, montaje y retirada del viejo.'},
      {id:'f2', c:'pe', name:'Reparación de cisterna o fuga', unit:'ud', min:48, max:48,
        d:'Mecanismo de cisterna nuevo o reparación de una fuga visible.'},
      {id:'f3', c:'pe', name:'Cambio de termo eléctrico de 80 L', unit:'ud', min:311, max:311,
        d:'Termo de gama comercial, montaje y retirada del viejo.'},
      {id:'f4', c:'pe', name:'Cambio de inodoro', unit:'ud', min:218, max:218,
        d:'Inodoro de gama comercial, montaje y retirada del viejo.'},
      {id:'f5', c:'pe', name:'Desatasco sencillo', unit:'ud', min:34, max:34,
        d:'Fregadero, lavabo o ducha.'},
      {id:'f6', c:'c', name:'Reparación de fuga en zonas comunes', unit:'ud', min:45, max:45,
        d:'Localización y reparación de una fuga visible.'},
      {id:'f7', c:'c', name:'Desatasco de bajante o arqueta comunitaria', unit:'ud', min:68, max:68,
        d:'Desatasco con herramienta mecánica.'}
    ]},
    {id:'a', name:'Remates de albañilería (con trabajo eléctrico)', cable:'earth', items:[
      {id:'a2', c:'pe', name:'Reposición de alicatado o solado (sin pieza cerámica)', unit:'m²', min:30, max:30,
        d:'Para dejar rematada la zona tras un trabajo eléctrico. Incluye colocación, cemento cola y junta; la pieza cerámica la aportas tú o la presupuestamos aparte. Mínimo 1 m².'},
      {id:'a3', c:'pec', name:'Abrir y tapar rozas', unit:'m', min:15, max:15,
        d:'Apertura para pasar los tubos de la instalación eléctrica y tapado con yeso.'},
      {id:'a4', c:'pec', name:'Pintura de reparación', unit:'m²', min:6, max:6,
        d:'Pintura plástica de la zona reparada tras el trabajo eléctrico.'}
    ]}
  ];
  var INTRO = {
    particular: 'Trabajos habituales en casas y pisos.',
    profesional: 'Trabajos para locales, oficinas y apartamentos turísticos. Factura con todos los datos y parte de cada intervención.',
    comunidad: 'Trabajos en zonas comunes: portal, escaleras, garaje y cuarto de contadores. Presupuesto a nombre de la comunidad.'
  };
  var TRAVEL = [0, 15, 30];          // € por zona
  var URG_FIXED = [0, 30, 60];        // € por intervención: urgente en horario / salida fuera de horario
  var URG_HOURS = [0, 0, 0.50];       // recargo solo sobre las horas de mano de obra (fuera de horario)
  var HOUR_ITEMS = {e1:1, e2:1};      // líneas que son horas de mano de obra
  var URG_LABEL = ['', 'urgente en horario (24 h)', 'fuera de horario'];
  var URG_NOTE = ['',
    'Urgente en horario (L–V de 8 a 18 h): +30 € por intervención. Las horas se cobran a tarifa normal.',
    'Fuera de horario (L–V antes de las 8 h o después de las 18 h, sábados, domingos y festivos): +60 € por salida y +50 % sobre las horas de mano de obra, incluida la primera. Fuera de horario atendemos averías; las instalaciones y reformas se programan en horario normal.'];
  var PHONE = (document.body.dataset.whatsapp || '34621018374');

  var qty = {};
  var $ = function(s){return document.querySelector(s)};
  var eur = function(n){return Math.round(n).toLocaleString('es-ES') + ' €'};
  var range = function(a,b){return a===b ? eur(a) : Math.round(a).toLocaleString('es-ES') + '–' + eur(b)};
  var desde = function(n){return 'desde ' + eur(n)};
  var CODE = {particular:'p', profesional:'e', comunidad:'c'};

  /* build catalog */
  var cat = $('#catalog');
  CATALOG.forEach(function(g, gi){
    var d = document.createElement('details');
    d.className = 'cat'; d.id = 'grp-' + g.id;
    d.innerHTML = '<summary><span class="cable ' + g.cable + '"></span>' + g.name + '<span class="count" id="cnt-' + g.id + '"></span></summary><div class="items"></div>';
    var box = d.querySelector('.items');
    g.items.forEach(function(it){
      qty[it.id] = 0;
      var row = document.createElement('div');
      row.className = 'item'; row.id = 'row-' + it.id;
      row.innerHTML =
        '<span class="name">' + it.name + '</span>' +
        (it.d ? '<span class="desc">' + it.d + '</span>' : '') +
        '<span class="price">desde ' + eur(it.min) + ' / ' + it.unit + (it.closed ? '' : ' + salida') + '</span>' +
        '<span class="stepper"><button type="button" aria-label="Quitar uno" data-d="-1">−</button>' +
        '<input id="q-' + it.id + '" type="number" min="0" step="1" value="0" inputmode="numeric" aria-label="Cantidad: ' + it.name + '">' +
        '<span class="unit">' + it.unit + '</span>' +
        '<button type="button" aria-label="Añadir uno" data-d="1">+</button></span>';
      var input = row.querySelector('input');
      row.querySelectorAll('button').forEach(function(b){
        b.addEventListener('click', function(){
          var v = Math.max(0, (parseFloat(input.value) || 0) + parseFloat(b.dataset.d));
          input.value = v; qty[it.id] = v; update();
        });
      });
      input.addEventListener('input', function(){
        var v = Math.max(0, parseFloat(input.value) || 0); qty[it.id] = v; update();
      });
      box.appendChild(row);
    });
    cat.appendChild(d);
  });

  function val(name){var el = document.querySelector('input[name="' + name + '"]:checked'); return el ? el.value : null}

  var last = {text:''};
  // Festivos de la Comunitat Valenciana 2026 (DOGV 07/07/2025). Los locales de Oropesa se añaden cuando se publiquen.
  var FEST_CV = {'2026-01-01':'Año Nuevo','2026-01-06':'Epifanía','2026-03-19':'San José','2026-04-03':'Viernes Santo','2026-04-06':'Lunes de Pascua','2026-05-01':'Fiesta del Trabajo','2026-06-24':'San Juan','2026-08-15':'Asunción','2026-10-09':'Día de la Comunitat Valenciana','2026-10-12':'Fiesta Nacional','2026-12-08':'Inmaculada Concepción','2026-12-25':'Navidad'};
  var OPEN_DAY = '2026-11-02';
  var DISP = null; // horas ocupadas publicadas desde la agenda: {fecha: ['08','09',…] o ['d'] = día completo}
  var HORAS = ['08','09','10','11','12','15','16','17'];
  function isoD(d){ return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0'); }
  function libres(f){ var oc = (DISP && DISP[f]) || []; if (oc.indexOf('d') >= 0) return []; return HORAS.filter(function(h){ return oc.indexOf(h) < 0; }); }
  function renderDisp(){
    var box = $('#disp'), ch = $('#disp-chips'); if (!box || !ch || !DISP) return;
    var out = [], d = new Date(Date.now() + 864e5), cur = $('#f-day') ? $('#f-day').value : '';
    for (var i = 0; i < 60 && out.length < 8; i++, d = new Date(d.getTime() + 864e5)) {
      var f = isoD(d), wd = d.getDay(); if (f < OPEN_DAY || wd === 0 || wd === 6 || FEST_CV[f]) continue;
      var n = libres(f).length; if (!n) continue;
      out.push([f, d.toLocaleDateString('es-ES', {weekday:'short', day:'numeric', month:'short'}) + ' · ' + n + (n === 1 ? ' hora libre' : ' horas libres')]);
    }
    ch.innerHTML = '';
    out.forEach(function(o){ var b = document.createElement('button'); b.type = 'button'; b.textContent = o[1]; b.setAttribute('aria-pressed', String(cur === o[0]));
      b.addEventListener('click', function(){ $('#f-day').value = o[0]; update(); $('#f-slot').focus(); }); ch.appendChild(b); });
    box.hidden = !out.length;
  }
  fetch('/api/disponibilidad', {cache:'no-store'}).then(function(r){ return r.ok ? r.json() : null; }).then(function(j){ if (j && j.ocupado) { DISP = j.ocupado; update(); } }).catch(function(){});
  function update(){
    var client = val('client');
    var zone = +val('zone'), urg = +val('urg');
    var vatWrap = $('#vat-wrap'), vatNote = $('#vat-note');
    var isPart = client === 'particular';
    vatWrap.hidden = !isPart; vatNote.hidden = !isPart;
    if (!isPart) $('#v21').checked = true;
    var vat = +val('vat') / 100;

    var list = $('#sum-list'); list.innerHTML = '';
    var wMin = 0, wMax = 0, hMin = 0, hMax = 0, lines = [], items = [], code = CODE[client], needSal = false, diag = false;
    var intro = $('#cat-intro'); if (intro) intro.textContent = INTRO[client] + ' Abre cada categoría y pulsa + en los trabajos que necesites. Los precios son por unidad; la salida y visita (' + SALIDA + ' €) se cobra una sola vez por visita. ¿No sabes qué marcar? Elige «Visita y diagnóstico» y cuéntanos el problema más abajo.';
    CATALOG.forEach(function(g){
      var n = 0, vis = 0;
      g.items.forEach(function(it){
        var show = it.c.indexOf(code) >= 0;
        $('#row-' + it.id).hidden = !show;
        if (show) vis++;
        else if (qty[it.id]) { qty[it.id] = 0; $('#q-' + it.id).value = 0; }
        var q = qty[it.id] || 0;
        $('#row-' + it.id).classList.toggle('on', q > 0);
        if (q > 0){
          n++;
          var a = it.min * q, b = it.max * q; wMin += a; wMax += b;
          if (!it.closed) needSal = true;
          if (it.id === 'e1') diag = true;
          if (HOUR_ITEMS[it.id]) { hMin += a; hMax += b; }
          var li = document.createElement('li');
          li.innerHTML = '<span>' + q + ' ' + it.unit + ' · ' + it.name + '</span><span>' + desde(a) + '</span>';
          list.appendChild(li);
          lines.push('- ' + q + ' ' + it.unit + ' · ' + it.name + ': ' + desde(a));
          items.push({id: it.id, nombre: it.name, cant: q, unidad: it.unit, desde: it.min});
        }
      });
      $('#grp-' + g.id).hidden = !vis;
      $('#cnt-' + g.id).textContent = n ? n + ' marcado' + (n > 1 ? 's' : '') : '';
    });
    var has = lines.length > 0;
    $('#sum-empty').hidden = has;
    $('#sum-lines').hidden = !has;

    var travel = has ? TRAVEL[zone] : 0;
    var sal = (needSal && !diag) ? SALIDA : 0;
    var fix = has ? URG_FIXED[urg] : 0;
    var xMin = sal + travel + fix + hMin * URG_HOURS[urg], xMax = sal + travel + fix + hMax * URG_HOURS[urg];
    var extras = [];
    if (sal) extras.push(['Salida y visita (una por visita)', sal]);
    if (travel) extras.push(['Desplazamiento (' + (zone === 1 ? 'hasta 20 km' : '20 a 40 km') + ')', travel]);
    if (fix) extras.push([urg === 1 ? 'Suplemento urgencia en horario' : 'Salida fuera de horario', fix]);
    if (hMin * URG_HOURS[urg]) extras.push(['Recargo 50 % sobre horas fuera de horario', hMin * URG_HOURS[urg]]);
    extras.forEach(function(x){
      var li = document.createElement('li'); li.className = 'extra';
      li.innerHTML = '<span>' + x[0] + '</span><span>' + eur(x[1]) + '</span>';
      list.appendChild(li); lines.push('- ' + x[0] + ': ' + eur(x[1]));
    });
    var un = $('#urg-note'); if (un) { un.textContent = URG_NOTE[urg]; un.hidden = !urg; }
    var bMin = wMin + xMin, bMax = wMax + xMax;
    $('#l-work').textContent = range(wMin, wMax);
    $('#l-extra').textContent = range(xMin, xMax);
    $('#l-base').textContent = range(bMin, bMax);
    $('#l-vat-k').textContent = 'IVA ' + Math.round(vat * 100) + ' %';
    $('#l-vat').textContent = range(bMin * vat, bMax * vat);
    $('#total').innerHTML = has ? '<small>desde</small> ' + eur(bMin * (1 + vat)) : '0 €';

    var fotos = !!($('#f-fotos') && $('#f-fotos').checked);
    var day = $('#f-day') ? $('#f-day').value : '', slot = $('#f-slot') ? $('#f-slot').value : '';
    var dayTxt = '', dn = $('#day-note');
    if ($('#f-slot')) [].forEach.call($('#f-slot').options, function(o){ o.disabled = false; });
    if (day) {
      var dd = new Date(day + 'T12:00:00'), wd = dd.getDay(), fest = FEST_CV[day];
      dayTxt = dd.toLocaleDateString('es-ES', {weekday:'long', day:'numeric', month:'long'});
      var lib = libres(day), full = !!DISP && !lib.length;
      if ($('#f-slot')) [].forEach.call($('#f-slot').options, function(o){ o.disabled = !!o.value && !!DISP && lib.indexOf(o.value) < 0; if (o.disabled && o.selected) { $('#f-slot').value = ''; slot = ''; } });
      if (dn) {
        dn.textContent = day < OPEN_DAY ? 'Empezamos a atender el 2 de noviembre de 2026; elige un día a partir de esa fecha.' :
          fest ? 'El ' + dayTxt + ' es festivo (' + fest + '). Te propondremos otro día, salvo urgencia.' :
          full ? 'El ' + dayTxt + ' ya está completo. Elige otro de los días con huecos libres.' :
          (wd === 0 || wd === 6) ? 'Los fines de semana solo atendemos urgencias. Te propondremos un día laborable.' :
          'Es una preferencia: te confirmamos día y hora por WhatsApp según la agenda.';
        dn.classList.toggle('warn', day < OPEN_DAY || !!fest || full || wd === 0 || wd === 6);
      }
    }
    var name = $('#f-name').value.trim(), phone = $('#f-phone').value.trim(), town = $('#f-town').value.trim(), desc = $('#f-desc').value.trim();
    var clientLabel = {particular:'Particular', profesional:'Empresa o autónomo', comunidad:'Comunidad de propietarios'}[client];
    var t = 'Hola, quiero presupuesto con SENOIDE.\n' +
      'Cliente: ' + clientLabel + (name ? ' · ' + name : '') + (phone ? ' · ' + phone : '') + '\n' +
      (town ? 'Municipio: ' + town + '\n' : '') +
      (day || slot ? 'Visita preferida: ' + [dayTxt, slot ? 'a las ' + (+slot) + ':00' : ''].filter(Boolean).join(', ') + ' — pendiente de confirmar\n' : '') +
      (urg ? 'Urgencia: ' + URG_LABEL[urg] + '\n' : '') +
      (has ? 'Trabajos:\n' + lines.join('\n') + '\nTotal con IVA ' + Math.round(vat * 100) + '%: ' + desde(bMin * (1 + vat)) + '\n' : '') +
      (desc ? 'Detalle: ' + desc : '') +
      (fotos ? '\nTe adjunto fotos en este chat.' : '');
    last.text = t;
    last.data = {nombre: name, telefono: phone, email: $('#f-email') ? $('#f-email').value.trim() : '', municipio: town, descripcion: desc, tipoCliente: client,
      dia: day, hora: slot, urgencia: urg, zona: zone, iva: Math.round(vat * 100), fotos: fotos, totalDesde: has ? Math.round(bMin * (1 + vat) * 100) / 100 : 0, trabajos: items};
    renderDisp();
    $('#wa').href = 'https://wa.me/' + PHONE + '?text=' + encodeURIComponent(t);
  }

  document.querySelectorAll('input[name="client"],input[name="zone"],input[name="urg"],input[name="vat"]').forEach(function(r){r.addEventListener('change', update)});
  ['#f-name','#f-phone','#f-town','#f-desc','#f-day','#f-slot'].forEach(function(s){ if ($(s)) { $(s).addEventListener('input', update); $(s).addEventListener('change', update); } });
  if ($('#f-day')) { var tm = new Date(Date.now() + 864e5), iso = function(d){ return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0'); }; $('#f-day').min = iso(tm) > OPEN_DAY ? iso(tm) : OPEN_DAY; }
  if ($('#f-fotos')) $('#f-fotos').addEventListener('change', update);
  $('#wa').addEventListener('click', function(){
    if ($('#f-fotos') && $('#f-fotos').checked){ var t = $('#toast'); t.textContent = 'Envía el mensaje en WhatsApp y después adjunta las fotos con el clip.'; setTimeout(function(){t.textContent=''}, 8000); }
  });
  $('#req').addEventListener('submit', function(e){e.preventDefault()});

  /* Enviar la solicitud a SENOIDE (llega a la app de gestión y por correo) */
  var API = document.body.dataset.api || '';
  var sending = false;
  function sendMsg(txt, ok){
    var m = $('#send-msg'); if (!m){ m = document.createElement('div'); m.id = 'send-msg'; m.setAttribute('role', 'status'); $('.summary .acts').insertAdjacentElement('afterend', m); }
    m.className = 'send-msg ' + (ok ? 'ok' : 'err'); m.innerHTML = txt;
  }
  if ($('#send')) $('#send').addEventListener('click', function(){
    if (sending) return;
    update();
    var d = last.data || {}, tel = String(d.telefono || '').replace(/\D/g, '');
    if (!d.nombre){ sendMsg('Escribe tu nombre en el paso 4.'); $('#f-name').focus(); return; }
    if (tel.length < 9){ sendMsg('Escribe un teléfono de contacto en el paso 4.'); $('#f-phone').focus(); return; }
    if (d.email && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(d.email)){ sendMsg('El correo no parece correcto.'); $('#f-email').focus(); return; }
    if (!d.trabajos.length && (d.descripcion || '').length < 5){ sendMsg('Marca algún trabajo o cuéntanos en el paso 4 qué necesitas.'); $('#f-desc').focus(); return; }
    if (!$('#f-priv').checked){ sendMsg('Marca la casilla de la política de privacidad para poder enviarla.'); $('#f-priv').focus(); return; }
    if (!API){ sendMsg('Ahora mismo no podemos recibirla desde aquí. Envíala por WhatsApp, por favor.'); return; }
    sending = true; var b = $('#send'); b.disabled = true; b.textContent = 'Enviando…';
    var body = Object.assign({}, d, {privacidad: true, web: ($('#f-web') || {}).value || ''});
    fetch(API + '/api/solicitud', {method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify(body)})
      .then(function(r){ return r.json().catch(function(){ return {}; }).then(function(j){ return {ok: r.ok, j: j}; }); })
      .then(function(x){
        if (x.ok && x.j.ok){
          sendMsg('<b>¡Recibida!</b> Te llamamos o escribimos en horario laboral (L–V, 8 a 18 h) para confirmar la visita.' + (d.email ? ' Te hemos enviado una copia a tu correo.' : '') + (d.fotos ? ' Si quieres, mándanos ya las fotos por WhatsApp con el botón de al lado.' : ''), true);
          b.textContent = 'Solicitud enviada';
        } else { sendMsg((x.j && x.j.error ? x.j.error : 'No se ha podido enviar.') + ' También puedes enviarla por WhatsApp o llamarnos al 621 018 374.'); b.disabled = false; b.textContent = 'Enviar solicitud'; }
      })
      .catch(function(){ sendMsg('No se ha podido enviar (sin conexión o servidor no disponible). Envíala por WhatsApp o llámanos al 621 018 374.'); b.disabled = false; b.textContent = 'Enviar solicitud'; })
      .then(function(){ sending = false; });
  });

  function copyText(text, msg){
    var toast = $('#toast');
    var done = function(){ if (msg){ toast.textContent = msg; setTimeout(function(){toast.textContent=''}, 2500);} };
    try{
      navigator.clipboard.writeText(text).then(done, function(){fallback(text); done();});
    }catch(e){ fallback(text); done(); }
  }
  function fallback(text){
    var ta = document.createElement('textarea'); ta.value = text; document.body.appendChild(ta); ta.select();
    try{document.execCommand('copy')}catch(e){} ta.remove();
  }
  $('#copy').addEventListener('click', function(){ copyText(last.text, 'Resumen copiado. Pégalo en WhatsApp o en un correo.'); });
  document.querySelectorAll('[data-copy]').forEach(function(b){
    b.addEventListener('click', function(){ copyText(b.dataset.copy); b.textContent = 'Copiado'; setTimeout(function(){b.textContent='Copiar'}, 2000); });
  });

  /* tabs */
  var tabs = [['#tab-part','#pane-part'],['#tab-pro','#pane-pro']];
  tabs.forEach(function(p){
    $(p[0]).addEventListener('click', function(){
      tabs.forEach(function(q){ var on = q === p; $(q[0]).setAttribute('aria-selected', on); $(q[1]).hidden = !on; });
    });
  });
  document.querySelectorAll('[data-client]').forEach(function(a){
    a.addEventListener('click', function(){
      var map = {particular:'#c-part', profesional:'#c-pro', comunidad:'#c-com'};
      $(map[a.dataset.client]).checked = true; update();
    });
  });

  /* el presupuestador arranca vacío */
  update();

  /* hero sine wave */
  var cv = $('#wave'), ctx = cv.getContext('2d');
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function size(){ var r = cv.getBoundingClientRect(), d = window.devicePixelRatio || 1; cv.width = r.width * d; cv.height = r.height * d; ctx.setTransform(d,0,0,d,0,0); }
  function draw(t){
    var w = cv.clientWidth, h = cv.clientHeight, cs = getComputedStyle(document.documentElement);
    ctx.clearRect(0,0,w,h);
    var waves = [
      {c: cs.getPropertyValue('--signal').trim(), a: .5, amp: h * .16, k: 2.2, s: .0006, o: 0, lw: 2.5},
      {c: cs.getPropertyValue('--line').trim(), a: 1, amp: h * .12, k: 2.2, s: .0006, o: 2.094, lw: 1.5},
      {c: cs.getPropertyValue('--line').trim(), a: 1, amp: h * .12, k: 2.2, s: .0006, o: 4.188, lw: 1.5}
    ];
    waves.forEach(function(wv){
      ctx.beginPath(); ctx.globalAlpha = wv.a; ctx.strokeStyle = wv.c; ctx.lineWidth = wv.lw;
      for (var x = 0; x <= w; x += 4){
        var y = h * .72 + Math.sin(x / w * Math.PI * 2 * wv.k + wv.o - t * wv.s) * wv.amp;
        x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.stroke();
    });
    ctx.globalAlpha = 1;
  }
  size(); draw(0);
  window.addEventListener('resize', function(){ size(); draw(0); });
  if (!reduce){ (function loop(t){ draw(t); requestAnimationFrame(loop); })(0); }
})();
