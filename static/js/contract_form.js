function initContractForm() {
  const typeSelect = document.getElementById('main_or_additional');
  const extraBlock = document.getElementById('extra_fields');
  const extraType = document.getElementById('extra_type');
  const extraAmountBlock = document.getElementById('extra_amount_block');
  const mainFields = document.getElementById('main_fields');

  function updateVisibility() {
    if (!typeSelect) return;
    const isExtra = typeSelect.value === 'Доп соглашение';
    if (isExtra) {
      extraBlock.style.display = 'block';
      mainFields.style.display = 'none';
    } else {
      extraBlock.style.display = 'none';
      mainFields.style.display = 'block';
    }

    if (extraType) {
      if (extraType.value === 'add_amount') {
        mainFields.style.display = 'block';
        extraAmountBlock.style.display = 'block';
      } else {
        extraAmountBlock.style.display = 'none';
      }
    }
  }

  if (typeSelect) typeSelect.addEventListener('change', updateVisibility);
  if (extraType) extraType.addEventListener('change', updateVisibility);
  updateVisibility();
}