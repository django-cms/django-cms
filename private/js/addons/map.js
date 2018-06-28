/* global google */
import { memoize } from 'lodash';

class Map {

    constructor(options) {
        this.options = $.extend({}, Map.options, options);

        this._setupUI();
        this._bindUI();
    }

    /**
     * Stores all jQuery references within `this.ui`
     *
     * @method _setupUI
     * @private
     */
    _setupUI() {
        this.ui = {
            modal_container: $(this.options.modal_container),
            links: $(this.options.links),
        };
    }

    /**
     * Handle click on links
     *
     * @method _bindUI
     * @private
     */
    _bindUI() {
        var that = this;
        this.ui.links.on('click', function(e) {
            e.preventDefault();
            that.location = $(this).data('location');
            that._initMap();
        });

        this.ui.modal_container.on('shown.bs.modal', function() {
            that._buildMarkers();
        });
    }

    /**
     * Initialize map
     *
     * @method _initMap
     * @private
     */
    _initMap() {
        this._showModal();
    }

    /**
     * Build list of markers and set it on map
     *
     * @method _buildMarkers
     * @private
     */
    _buildMarkers() {
        var that = this;

        var LatLngList = [];

        this.map = new google.maps.Map(
            document.getElementById(this.options.map_canvas),
            $.extend(
                {},
                {
                    center: {
                        lat: this.location[0][0],
                        lng: this.location[0][1],
                    },
                },
                this.options.map_settings
            )
        );

        for (var i = 0, len = this.location.length; i < len; i++) {
            new google.maps.Marker({
                position: new google.maps.LatLng(this.location[i][0], this.location[i][1]),
                map: this.map,
                title: this.options.title,
            });

            LatLngList.push(new google.maps.LatLng(this.location[i][0], this.location[i][1]));
        }

        var bounds = new google.maps.LatLngBounds();

        for (var j = 0, LtLgLen = LatLngList.length; j < LtLgLen; j++) {
            bounds.extend(LatLngList[j]);
        }

        if (this.location.length > 1) {
            this.map.fitBounds(bounds);
        }

        var listener = google.maps.event.addListener(this.map, 'idle', function() {
            that.map.panBy(0, 0);
            google.maps.event.removeListener(listener);
        });
    }

    /**
     * Show modal with map
     *
     * @method _showModal
     * @private
     */
    _showModal() {
        this.ui.modal_container.modal('show');
    }
}

Map.options = {
    map_canvas: 'network-detail-map',
    modal_container: '#mapShow',
    links: '.js-show-map',
    map_settings: {
        zoom: 13,
    },
};

export const loadGoogleMaps = memoize(token => {
    var script = document.createElement('script');
    var deferred = new $.Deferred();

    window.__mapCallback = function() {
        deferred.resolve();
        delete window.__mapCallback;
    };

    script.type = 'text/javascript';
    script.async = true;
    script.src =
        'https://maps.googleapis.com/maps/api/js?' + 'key=' + token + '&libraries=places&callback=__mapCallback';
    document.getElementsByTagName('head')[0].appendChild(script);

    return deferred.promise();
});

export function initPartnerMap() {
    const detailMap = $('#network-detail-map');

    if (detailMap.length) {
        loadGoogleMaps(detailMap.data('map').apiKey).then(() => {
            new Map(detailMap.data('map'));
        });
    }
}

export default Map;
