(function(){
  document.addEventListener('DOMContentLoaded', function(){
    const wrapper = document.getElementById('special-fields-wrapper');
    if(!wrapper) return;
    const titleCb = document.getElementById('toggle-title');
    const idCb = document.getElementById('toggle-id');
    const createdCb = document.getElementById('toggle-date-created');

    function apply(){
      const titleEl = document.getElementById('record-title');
      if(titleEl) titleEl.classList.toggle('hidden', !titleCb.checked);
      const idEl = document.getElementById('record-id');
      if(idEl) idEl.classList.toggle('hidden', !idCb.checked);
      const createdEl = document.getElementById('draggable-field-date_created');
      if(createdEl) createdEl.classList.toggle('hidden', !createdCb.checked);
    }

    [titleCb, idCb, createdCb].forEach(cb => cb && cb.addEventListener('change', apply));

    window.showSpecialFieldToggles = function(show){
      wrapper.classList.toggle('hidden', !show);
    };

    apply();
  });
})();
