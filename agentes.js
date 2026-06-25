
/* === CÓMO FUNCIONA: scroll animations & progress nav === */
(function(){
  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var steps = document.querySelectorAll('.cf-step');
  var progressNav = document.getElementById('cfProgressNav');
  var progressItems = document.querySelectorAll('.cf-progress-item');
  var progressTrackFill = document.getElementById('cfProgressTrackFill');
  var section = document.getElementById('como-funciona');
  if(!steps.length) return;

  function countUp(el, target, duration) {
    if(reducedMotion){ el.textContent = target.toLocaleString('es-ES'); return; }
    var startTime = null;
    function tick(ts){
      if(!startTime) startTime = ts;
      var p = Math.min((ts - startTime) / duration, 1);
      var ease = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(target * ease).toLocaleString('es-ES');
      if(p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  var inDone = [], simDone = [];
  steps.forEach(function(){ inDone.push(false); simDone.push(false); });

  // Show/hide progress nav when section is on screen
  if(section && progressNav){
    new IntersectionObserver(function(entries){
      progressNav.classList.toggle('visible', entries[0].isIntersecting);
    }, { threshold: 0.05 }).observe(section);
  }

  // cf-in: reveal text elements
  new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      var idx = parseInt(e.target.dataset.step, 10);
      if(e.isIntersecting && !inDone[idx]){ inDone[idx]=true; e.target.classList.add('cf-in'); }
    });
  }, { threshold: 0.2, rootMargin: '0px 0px -60px 0px' }).observe ? void 0 : null;

  var inObs = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      var idx = parseInt(e.target.dataset.step, 10);
      if(e.isIntersecting && !inDone[idx]){ inDone[idx]=true; e.target.classList.add('cf-in'); }
    });
  }, { threshold: 0.2, rootMargin: '0px 0px -60px 0px' });
  steps.forEach(function(s){ inObs.observe(s); });

  // cf-sim: trigger visual card animations once
  var simObs = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      var idx = parseInt(e.target.dataset.step, 10);
      if(!e.isIntersecting || simDone[idx]) return;
      simDone[idx] = true;
      var step = e.target;
      step.classList.add('cf-sim');

      // Paso 3 — count-up valoración
      if(idx === 2){
        var el = step.querySelector('.cf-count-report');
        if(el) setTimeout(function(){ countUp(el, 757500, 1200); }, 300);
      }

      // Paso 5 — count-up stats + new row
      if(idx === 4){
        var leadsEl = step.querySelector('.cf-count-leads');
        var convEl  = step.querySelector('.cf-count-conv');
        var valEl   = step.querySelector('.cf-count-val');
        if(leadsEl) setTimeout(function(){ countUp(leadsEl, 12, 800);  }, 200);
        if(convEl)  setTimeout(function(){ countUp(convEl,  34, 900);  }, 350);
        if(valEl)   setTimeout(function(){ countUp(valEl,  420, 1000); }, 500);

        setTimeout(function(){
          var tbody = document.getElementById('cfDashBody');
          var badge = document.getElementById('cfDashBadge');
          if(!tbody) return;
          var row = document.createElement('tr');
          row.className = 'cf-dash-row cf-dash-row-new';
          row.innerHTML = '<td>Josep M.</td><td>Ático · Salou</td><td><span class="cf-dash-status nuevo">Nuevo</span></td>';
          tbody.insertBefore(row, tbody.firstChild);
          setTimeout(function(){ row.classList.add('show'); }, 50);
          setTimeout(function(){ row.classList.add('settle'); }, 1400);
          if(badge){
            badge.textContent = '13 leads';
            badge.classList.add('bump');
            setTimeout(function(){ badge.classList.remove('bump'); }, 400);
          }
        }, 700);
      }
    });
  }, { threshold: 0.35 });
  steps.forEach(function(s){ simObs.observe(s); });

  // Closing count-up
  var closingEl = document.querySelector('.cf-count-secs');
  if(closingEl){
    var closingDone = false;
    var closingTarget = closingEl.closest('.cf-closing');
    if(closingTarget){
      new IntersectionObserver(function(entries){
        if(entries[0].isIntersecting && !closingDone){ closingDone=true; countUp(closingEl, 60, 900); }
      }, { threshold: 0.5 }).observe(closingTarget);
    }
  }

  // Progress nav: update active/done on scroll
  function updateProgress(){
    if(!progressNav || !progressNav.classList.contains('visible')) return;
    var mid = window.innerHeight / 2;
    var activeIdx = -1;
    steps.forEach(function(s, i){
      var r = s.getBoundingClientRect();
      if(r.top <= mid && r.bottom >= mid) activeIdx = i;
    });
    if(activeIdx === -1){
      steps.forEach(function(s, i){ if(s.getBoundingClientRect().bottom < mid) activeIdx = i; });
    }
    progressItems.forEach(function(item, i){
      item.classList.toggle('active', i === activeIdx);
      item.classList.toggle('done', i < activeIdx);
    });
    if(progressTrackFill && activeIdx >= 0){
      progressTrackFill.style.height = (activeIdx / (steps.length - 1) * 100) + '%';
    }
  }
  window.addEventListener('scroll', updateProgress, { passive: true });
  updateProgress();

  // Progress nav click → scroll to step
  progressItems.forEach(function(item){
    item.addEventListener('click', function(){
      var s = steps[parseInt(item.dataset.target, 10)];
      if(s) s.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
  });

  // Reduced motion: show everything immediately
  if(reducedMotion){
    steps.forEach(function(s){ s.classList.add('cf-in','cf-sim'); });
    var re = document.querySelector('.cf-count-report');
    if(re) re.textContent = '757.500';
    if(closingEl) closingEl.textContent = '60';
    var le = document.querySelector('.cf-count-leads');
    var ce = document.querySelector('.cf-count-conv');
    var ve = document.querySelector('.cf-count-val');
    if(le) le.textContent = '12';
    if(ce) ce.textContent = '34';
    if(ve) ve.textContent = '420';
  }
})();

/* EDITAR: ID Pixel — sustituir 0000000000000 por el Pixel ID real */
!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;
n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,
document,'script','https://connect.facebook.net/en_US/fbevents.js');
fbq('init', '0000000000000');
fbq('track', 'PageView');

