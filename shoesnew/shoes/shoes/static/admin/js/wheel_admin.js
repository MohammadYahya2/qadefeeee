// Wheel Configuration Admin JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const prizeTypeField = document.getElementById('id_prize_type');
    const giftDescriptionRow = document.querySelector('.field-gift_description');
    const valueRow = document.querySelector('.field-value');
    
    if (prizeTypeField && giftDescriptionRow) {
        // Function to toggle gift description visibility
        function toggleGiftDescription() {
            const prizeType = prizeTypeField.value;
            
            if (prizeType === 'gift') {
                giftDescriptionRow.style.display = 'block';
                // Make gift description required for gifts
                const giftDescriptionField = document.getElementById('id_gift_description');
                if (giftDescriptionField) {
                    giftDescriptionField.required = true;
                }
            } else {
                giftDescriptionRow.style.display = 'none';
                // Remove required attribute when not a gift
                const giftDescriptionField = document.getElementById('id_gift_description');
                if (giftDescriptionField) {
                    giftDescriptionField.required = false;
                }
            }
            
            // Update value field label and placeholder based on prize type
            updateValueField(prizeType);
        }
        
        // Function to update value field based on prize type
        function updateValueField(prizeType) {
            const valueField = document.getElementById('id_value');
            const valueLabel = document.querySelector('label[for="id_value"]');
            
            if (valueField && valueLabel) {
                switch (prizeType) {
                    case 'discount':
                        valueLabel.textContent = 'نسبة الخصم (%)';
                        valueField.placeholder = 'أدخل نسبة الخصم من 1 إلى 100';
                        valueField.min = '1';
                        valueField.max = '100';
                        break;
                    case 'gift':
                        valueLabel.textContent = 'القيمة (اختياري)';
                        valueField.placeholder = 'قيمة الهدية (اختياري)';
                        valueField.min = '0';
                        valueField.removeAttribute('max');
                        break;
                    case 'free_shipping':
                        valueLabel.textContent = 'القيمة (0 للشحن المجاني)';
                        valueField.placeholder = '0';
                        valueField.value = '0';
                        valueField.min = '0';
                        valueField.max = '0';
                        break;
                    case 'no_prize':
                        valueLabel.textContent = 'القيمة (0 لعدم وجود جائزة)';
                        valueField.placeholder = '0';
                        valueField.value = '0';
                        valueField.min = '0';
                        valueField.max = '0';
                        break;
                    default:
                        valueLabel.textContent = 'القيمة';
                        valueField.placeholder = '';
                        valueField.removeAttribute('min');
                        valueField.removeAttribute('max');
                }
            }
        }
        
        // Add event listener for prize type changes
        prizeTypeField.addEventListener('change', toggleGiftDescription);
        
        // Initial toggle on page load
        toggleGiftDescription();
    }
}); 