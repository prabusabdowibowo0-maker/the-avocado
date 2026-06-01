// LOADING SCREEN
window.addEventListener('load', () => {
    const loader = document.getElementById('loader');
    loader.style.opacity = '0';
    setTimeout(() => { loader.style.display = 'none'; }, 500);
});

// TOAST
function showToast(message){
    const toastBox = document.getElementById('toastBox');
    const toast = document.createElement('div');
    toast.classList.add('toast-custom');
    toast.innerHTML = `<i class="bi bi-check-circle-fill"></i> ${message}`;
    toastBox.appendChild(toast);
    setTimeout(() => { toast.remove(); }, 3000);
}

// SMOOTH SCROLL
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e){
        e.preventDefault();
        document.querySelector(this.getAttribute('href'))
            .scrollIntoView({ behavior: 'smooth' });
    });
});

// REALTIME SEARCH
const searchInput = document.getElementById('searchInput');
if(searchInput){
    searchInput.addEventListener('keyup', () => {
        const filter = searchInput.value.toLowerCase();
        document.querySelectorAll('.product-item').forEach(item => {
            item.style.display = item.innerText.toLowerCase().includes(filter) ? '' : 'none';
        });
    });
}

// ADD TO CART (AJAX)
document.querySelectorAll('.add-cart-btn').forEach(button => {
    button.addEventListener('click', function(e){
        e.preventDefault();
        const url = this.getAttribute('href');
        this.classList.add('clicked');
        fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
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
        const id     = this.dataset.id;
        const action = this.dataset.action;
        const url    = '/' + action + '_quantity/' + id;
        fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(res => res.json())
        .then(data => {
            if(data.success){
                const qtyEl      = document.getElementById('qty-' + id);
                const subtotalEl = document.getElementById('subtotal-' + id);
                const totalEl    = document.getElementById('cartTotal');
                const counterEl  = document.getElementById('cartCounter');
                if(data.removed){
                    const row = document.getElementById('cart-row-' + id);
                    if(row) row.remove();
                } else {
                    if(qtyEl)      qtyEl.innerText      = data.quantity;
                    if(subtotalEl) subtotalEl.innerText = 'Rp ' + data.subtotal.toLocaleString('id-ID');
                }
                if(totalEl)   totalEl.innerText   = 'Rp ' + data.total.toLocaleString('id-ID');
                if(counterEl) counterEl.innerText = data.cart_count;
            }
        });
    });
});

// REMOVE BUTTON (AJAX)
document.querySelectorAll('.remove-btn').forEach(button => {
    button.addEventListener('click', function(){
        const id = this.dataset.id;
        fetch('/remove_from_cart/' + id, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(res => res.json())
        .then(data => {
            if(data.success){
                const row = document.getElementById('cart-row-' + id);
                if(row) row.remove();
                const totalEl   = document.getElementById('cartTotal');
                const counterEl = document.getElementById('cartCounter');
                if(totalEl)   totalEl.innerText   = 'Rp ' + data.total.toLocaleString('id-ID');
                if(counterEl) counterEl.innerText = data.cart_count;
                showToast('Produk dihapus dari cart');
                if(data.cart_count === 0) location.reload();
            }
        });
    });
});

// PAYMENT FORM - QRIS shown in modal after bayar sekarang
const paymentForm = document.getElementById('paymentForm');
if(paymentForm){
    paymentForm.addEventListener('submit', function(e){
        e.preventDefault();
        
        const paymentMethod = document.querySelector('.payment-select').value;
        
        if(!paymentMethod){
            showToast('Pilih metode pembayaran dulu!');
            return;
        }
        
        showToast('Memproses pembayaran...');
        
        setTimeout(() => {
            const paymentContent = document.getElementById('paymentContent');
            
            if(paymentMethod === 'QRIS'){
                // Show QRIS code
                paymentContent.innerHTML = `
                    <div class="success-icon mb-3"><i class="bi bi-qr-code"></i></div>
                    <h3 class="fw-bold text-success mb-3">QRIS Payment</h3>
                    <p class="text-muted mb-4">Scan kode QR di bawah dengan smartphone mu</p>
                    <img src="https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=TheAvocadosPayment" 
                         class="img-fluid mb-4" style="max-width:250px;">
                    <p class="text-muted small mb-4">Setelah berhasil scan, klik tombol di bawah untuk lanjut</p>
                    <a href="/receipt/QRIS" class="btn btn-success w-100">
                        Lanjut ke Struk
                    </a>
                `;
            } else {
                // Cash payment
                paymentContent.innerHTML = `
                    <div class="success-icon mb-3"><i class="bi bi-check-circle-fill"></i></div>
                    <h3 class="fw-bold text-success mb-3">Pembayaran Berhasil</h3>
                    <p class="text-muted mb-4">Terima kasih telah berbelanja di The Avocados</p>
                    <a href="/receipt/Cash" class="btn btn-success w-100">
                        Lihat Struk
                    </a>
                `;
            }
            
            const modal = new bootstrap.Modal(document.getElementById('paymentModal'));
            modal.show();
        }, 1500);
    });
}

// DELETE CONFIRM
document.querySelectorAll('.delete-btn').forEach(button => {
    button.addEventListener('click', () => {
        if(confirm('Yakin ingin menghapus produk ini?')){
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