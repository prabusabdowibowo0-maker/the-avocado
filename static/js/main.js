// LOADING SCREEN

window.addEventListener('load', () => {

    const loader = document.getElementById('loader');

    loader.style.opacity = '0';

    setTimeout(() => {

        loader.style.display = 'none';

    }, 500);

});

// TOAST FUNCTION

function showToast(message){

    const toastBox = document.getElementById('toastBox');

    const toast = document.createElement('div');

    toast.classList.add('toast-custom');

    toast.innerHTML = `
        <i class="bi bi-check-circle-fill"></i>
        ${message}
    `;

    toastBox.appendChild(toast);

    setTimeout(() => {

        toast.remove();

    }, 3000);

}

// SMOOTH SCROLL

document.querySelectorAll('a[href^="#"]').forEach(anchor => {

    anchor.addEventListener('click', function(e){

        e.preventDefault();

        document.querySelector(this.getAttribute('href'))
            .scrollIntoView({
                behavior:'smooth'
            });

    });

});

// REALTIME SEARCH

const searchInput = document.getElementById('searchInput');

if(searchInput){

    searchInput.addEventListener('keyup', () => {

        const filter = searchInput.value.toLowerCase();

        const products = document.querySelectorAll('.product-item');

        products.forEach(item => {

            const text = item.innerText.toLowerCase();

            if(text.includes(filter)){

                item.style.display = '';

            }else{

                item.style.display = 'none';

            }

        });

    });

}

// ADD TO CART (AJAX - no page reload)

document.querySelectorAll('.add-cart-btn').forEach(button => {

    button.addEventListener('click', function(e){

        e.preventDefault();

        const url = this.getAttribute('href');

        this.classList.add('clicked');

        fetch(url, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(res => res.json())
        .then(data => {
            if(data.success){
                showToast('Produk berhasil ditambahkan ke cart 🛒');
                const counter = document.getElementById('cartCounter');
                if(counter) counter.innerText = data.cart_count;
            }
        })
        .finally(() => {
            setTimeout(() => this.classList.remove('clicked'), 200);
        });

    });

});

// QUANTITY BUTTONS (AJAX)

document.querySelectorAll('.qty-btn').forEach(button => {

    button.addEventListener('click', function(){

        const id   = this.dataset.id;
        const action = this.dataset.action;
        const url  = '/' + action + '_quantity/' + id;

        fetch(url, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(res => res.json())
        .then(data => {

            if(data.success){

                // update angka qty
                const qtyEl = document.getElementById('qty-' + id);
                const subtotalEl = document.getElementById('subtotal-' + id);
                const totalEl = document.getElementById('cartTotal');
                const counterEl = document.getElementById('cartCounter');

                if(data.removed){
                    // kalau qty jadi 0, hapus baris item
                    const row = document.getElementById('cart-row-' + id);
                    if(row) row.remove();
                } else {
                    if(qtyEl) qtyEl.innerText = data.quantity;
                    if(subtotalEl) subtotalEl.innerText = 'Rp ' + data.subtotal.toLocaleString('id-ID');
                }

                if(totalEl) totalEl.innerText = 'Rp ' + data.total.toLocaleString('id-ID');
                if(counterEl) counterEl.innerText = data.cart_count;

            }

        });

    });

});

// REMOVE BUTTON (AJAX)

document.querySelectorAll('.remove-btn').forEach(button => {

    button.addEventListener('click', function(){

        const id = this.dataset.id;

        fetch('/remove_from_cart/' + id, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(res => res.json())
        .then(data => {

            if(data.success){

                const row = document.getElementById('cart-row-' + id);
                if(row) row.remove();

                const totalEl = document.getElementById('cartTotal');
                const counterEl = document.getElementById('cartCounter');

                if(totalEl) totalEl.innerText = 'Rp ' + data.total.toLocaleString('id-ID');
                if(counterEl) counterEl.innerText = data.cart_count;

                showToast('Produk dihapus dari cart');

                if(data.cart_count === 0) location.reload();

            }

        });

    });

});

// CHECKOUT BUTTON

const checkoutBtn = document.querySelector('.checkout-btn');

if(checkoutBtn){

    checkoutBtn.addEventListener('click', () => {

        showToast('Mengarahkan ke pembayaran...');

    });

}

// PAYMENT METHOD

const paymentSelect = document.querySelector('.payment-select');

const qrisBox = document.getElementById('qrisBox');

if(paymentSelect){

    paymentSelect.addEventListener('change', () => {

        if(paymentSelect.value === 'QRIS'){

            qrisBox.style.display = 'block';

        }else{

            qrisBox.style.display = 'none';

        }

    });

}

// PAYMENT BUTTON

const paymentForm = document.getElementById('paymentForm');

if(paymentForm){

    paymentForm.addEventListener('submit', function(e){

        e.preventDefault();

        showToast('Memproses pembayaran...');

        setTimeout(() => {

            const modal = new bootstrap.Modal(
                document.getElementById('successModal')
            );

            modal.show();

        }, 1500);

    });

}

// DELETE CONFIRM

const deleteButtons = document.querySelectorAll('.delete-btn');

deleteButtons.forEach(button => {

    button.addEventListener('click', () => {

        const confirmDelete = confirm(
            'Yakin ingin menghapus produk ini?'
        );

        if(confirmDelete){

            window.location.href = button.dataset.url;

        }

    });

});

// DARK MODE

const darkToggle = document.getElementById('darkModeToggle');

if(darkToggle){

    darkToggle.addEventListener('click', () => {

        document.body.classList.toggle('dark-mode');

    });

}