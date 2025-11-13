// Подтверждения для действий удаления/архивации/восстановления (работает и для ссылок, и для форм)
document.addEventListener('DOMContentLoaded', function () {
  function confirmPrompt(message) {
    return confirm(message || 'Подтвердите действие');
  }

  // Для ссылок <a href="..."> (если где-то остались ссылки вместо форм)
  document.querySelectorAll('a[href*="/contract_delete/"]').forEach(function(el){
    el.addEventListener('click', function(e){
      if (!confirmPrompt('Вы уверены, что хотите удалить договор? Эту операцию нельзя отменить.')) {
        e.preventDefault();
      }
    });
  });
  document.querySelectorAll('a[href*="/contract_archive/"]').forEach(function(el){
    el.addEventListener('click', function(e){
      if (!confirmPrompt('Переместить договор в архив?')) e.preventDefault();
    });
  });
  document.querySelectorAll('a[href*="/contract_unarchive/"]').forEach(function(el){
    el.addEventListener('click', function(e){
      if (!confirmPrompt('Восстановить договор из архива?')) e.preventDefault();
    });
  });
  document.querySelectorAll('a[href*="/service_delete/"]').forEach(function(el){
    el.addEventListener('click', function(e){
      if (!confirmPrompt('Удалить услугу?')) e.preventDefault();
    });
  });
  document.querySelectorAll('a[href*="/extra_service_delete/"]').forEach(function(el){
    el.addEventListener('click', function(e){
      if (!confirmPrompt('Удалить дополнительную услугу?')) e.preventDefault();
    });
  });

  // Для форм POST: перехватываем submit и показываем подтверждение перед отправкой
  function attachFormConfirm(selector, message) {
    document.querySelectorAll(selector).forEach(function(form){
      // если форма уже имеет onsubmit/confirmAction, пропустим — но перехват безопасен
      form.addEventListener('submit', function(e){
        if (!confirmPrompt(message)) {
          e.preventDefault();
        }
      });
    });
  }

  // Формы для удаления/архивации/восстановления
  attachFormConfirm('form[action*="/contract_delete/"]', 'Вы уверены, что хотите удалить договор? Эту операцию нельзя отменить.');
  attachFormConfirm('form[action*="/contract_archive/"]', 'Переместить договор в архив?');
  attachFormConfirm('form[action*="/contract_unarchive/"]', 'Восстановить договор из архива?');
  attachFormConfirm('form[action*="/service_delete/"]', 'Удалить услугу?');
  attachFormConfirm('form[action*="/extra_service_delete/"]', 'Удалить дополнительную услугу?');

  // Защита на случай динамически добавляемых форм/ссылок (делегирование)
  document.body.addEventListener('click', function(e){
    var t = e.target;
    // поднимаемся вверх до ссылки, если клик по вложенному элементу
    while (t && t !== document.body) {
      if (t.tagName === 'A' && t.getAttribute('href')) {
        var href = t.getAttribute('href');
        if (href.indexOf('/contract_delete/') !== -1) {
          if (!confirmPrompt('Вы уверены, что хотите удалить договор? Эту операцию нельзя отменить.')) {
            e.preventDefault();
            return;
          }
        }
        if (href.indexOf('/contract_archive/') !== -1) {
          if (!confirmPrompt('Переместить договор в архив?')) {
            e.preventDefault();
            return;
          }
        }
        if (href.indexOf('/contract_unarchive/') !== -1) {
          if (!confirmPrompt('Восстановить договор из архива?')) {
            e.preventDefault();
            return;
          }
        }
        if (href.indexOf('/service_delete/') !== -1) {
          if (!confirmPrompt('Удалить услугу?')) {
            e.preventDefault();
            return;
          }
        }
        if (href.indexOf('/extra_service_delete/') !== -1) {
          if (!confirmPrompt('Удалить дополнительную услугу?')) {
            e.preventDefault();
            return;
          }
        }
      }
      t = t.parentElement;
    }
  });
});