document.addEventListener('DOMContentLoaded', function() {
  // Botões de filtro de tempo
  const timeButtons = document.querySelectorAll('.time-filters button');

  function updateChart(filter) {
    // Lógica para atualizar o gráfico conforme o filtro
    console.log('Atualizar gráfico para filtro:', filter);
  }

  timeButtons.forEach(button => {
    button.addEventListener('click', function() {
      timeButtons.forEach(btn => btn.classList.remove('active'));
      this.classList.add('active');
      updateChart(this.dataset.filter);
    });
  });

  // Animação dos cards ao entrarem na viewport
  const animateCards = function() {
    const cards = document.querySelectorAll('.metric-card, .stat-card, .feature');
    cards.forEach((card, index) => {
      const cardPosition = card.getBoundingClientRect().top;
      const screenPosition = window.innerHeight / 1.2;

      if (cardPosition < screenPosition && !card.classList.contains('animated')) {
        card.style.animation = `fadeInUp 0.7s cubic-bezier(.4,1.4,.6,1) ${index * 0.08}s forwards`;
        card.classList.add('animated');
      }
    });
  };

  window.addEventListener('scroll', animateCards);
  animateCards(); // Rodar na carga da página

  // Fade-in global para o conteúdo principal
  const main = document.querySelector('main');
  if (main) {
    main.style.opacity = 0;
    main.style.transition = 'opacity 1s cubic-bezier(.4,1.4,.6,1)';
    setTimeout(() => { main.style.opacity = 1; }, 200);
  }

  // Animação de contagem para números (ex: produção, estatísticas)
  function animateCountUp(element, target, duration = 1200) {
    let start = 0;
    const increment = target / (duration / 16);
    function update() {
      start += increment;
      if (start < target) {
        element.textContent = start.toFixed(1);
        requestAnimationFrame(update);
      } else {
        element.textContent = target.toFixed(1);
      }
    }
    update();
  }
  document.querySelectorAll('.count-animate').forEach(el => {
    const target = parseFloat(el.dataset.target || el.textContent);
    animateCountUp(el, target);
  });

  // Efeito de hover nos cards e features
  document.querySelectorAll('.metric-card, .stat-card, .feature').forEach(card => {
    card.addEventListener('mouseenter', function() {
      this.style.transform = 'translateY(-6px) scale(1.03)';
      this.style.boxShadow = '0 8px 32px 0 rgba(31,38,135,0.13)';
      this.style.transition = 'transform 0.3s, box-shadow 0.3s';
    });
    card.addEventListener('mouseleave', function() {
      this.style.transform = '';
      this.style.boxShadow = '';
    });
  });

  // Efeito de digitação em títulos com a classe .typing
  document.querySelectorAll('.typing').forEach(el => {
    const text = el.textContent;
    el.textContent = '';
    let i = 0;
    function type() {
      if (i < text.length) {
        el.textContent += text.charAt(i);
        i++;
        setTimeout(type, 40);
      }
    }
    type();
  });

  // Efeito de background animado (leve parallax)
  const bg = document.querySelector('.bg-animate');
  if (bg) {
    window.addEventListener('scroll', function() {
      bg.style.backgroundPositionY = `${window.scrollY * 0.2}px`;
    });
  }

  // Atualização simulada do valor de produção em tempo real
  let currentValue = 15.2;
  function updateProductionValue() {
    const productionElement = document.querySelector('.production-value .value');
    if (productionElement) {
      const variation = (Math.random() * 0.2 - 0.1).toFixed(2); // variação suave
      currentValue = (parseFloat(currentValue) + parseFloat(variation)).toFixed(1);
      productionElement.textContent = currentValue;
    }
  }
  setInterval(updateProductionValue, 5000);

  // Efeito de scroll suave para âncoras
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });

  // Efeito de animação nos botões principais
  document.querySelectorAll('.btn, button').forEach(btn => {
    btn.addEventListener('mousedown', function() {
      this.style.transform = 'scale(0.96)';
    });
    btn.addEventListener('mouseup', function() {
      this.style.transform = '';
    });
    btn.addEventListener('mouseleave', function() {
      this.style.transform = '';
    });
  });

  // Animação de fade nos elementos com .fade-on-scroll
  function fadeOnScroll() {
    document.querySelectorAll('.fade-on-scroll').forEach(el => {
      const rect = el.getBoundingClientRect();
      if (rect.top < window.innerHeight - 60) {
        el.style.opacity = 1;
        el.style.transform = 'none';
        el.style.transition = 'opacity 0.7s, transform 0.7s';
      }
    });
  }
  window.addEventListener('scroll', fadeOnScroll);
  fadeOnScroll();
});