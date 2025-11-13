// Небольшие клиентские функции: подтверждение перед удалением/архивацией/восстановлением/удалением услуг
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('a[href*="/contract_delete/"]').forEach(function(el){
    el.addEventListener('click', function(e){
      if(!confirm('Вы уверены, что хотите удалить договор? Эту операцию нельзя отменить.')){
        e.preventDefault();
      }
    });
  });
  document.querySelectorAll('a[href*="/contract_archive/"]').forEach(function(el){
    el.addEventListener('click', function(e){
      if(!confirm('Переместить договор в архив?')) e.preventDefault();
    });
  });
  document.querySelectorAll('a[href*="/contract_unarchive/"]').forEach(function(el){
    el.addEventListener('click', function(e){
      if(!confirm('Восстановить договор из архива?')) e.preventDefault();
    });
  });

  // подтверждение удаления услуг
  document.querySelectorAll('a[href*="/service_delete/"]').forEach(function(el){
    el.addEventListener('click', function(e){
      if(!confirm('Удалить услугу?')) e.preventDefault();
    });
  });
  document.querySelectorAll('a[href*="/extra_service_delete/"]').forEach(function(el){
    el.addEventListener('click', function(e){
      if(!confirm('Удалить дополнительную услугу?')) e.preventDefault();
    });
  });
});