export function whenNoTrackingProtection() {
    if (!whenNoTrackingProtection.promise) {
        whenNoTrackingProtection.promise = new Promise(function(resolve, reject) {
            const time = Date.now();
            const script = document.createElement('script');
            script.onload = resolve;
            script.onerror = function() {
                const diff = Date.now() - time;
                if (diff < 50) {
                    reject();
                } else {
                    // the request took to long, it seams this is a real network error
                    resolve();
                }
            };
            script.src = 'https://widget.intercom.io/widget/bgmmsfro/';
            document.body.appendChild(script);
        });
    }

    return whenNoTrackingProtection.promise;
}
window.whenNoTrackingProtection = whenNoTrackingProtection;

export function initSupportLink() {
    $('.js-support').on('click', e => {
        e.preventDefault();

        whenNoTrackingProtection()
            .catch(() => {
                $('.js-tracking-protection-modal').modal('show');
            });
    });
}
