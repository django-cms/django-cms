'use strict';
/*
 * Copyright https://github.com/divio/djangocms-googlemap
 */

(function () {
    var GoogleMap = (function () {
        /**
         * Helper function that retrieves a data-attribute value.
         *
         * @function getAttr
         * @param {HTMLElement} element single document node
         * @param {String} data data-attribute to retrieve
         * @return {String} value returns the value from the data-attribute
         */
        function getAttr(element, data) {
            var value = element.getAttribute('data-' + data);

            // true/false values need to be parsed from string to boolean
            // from the attributes data
            if (value === 'true') {
                return true;
            } else if (value === 'false') {
                return false;
            }
            return value;
        }

        /**
         * Initiates the GoogleMap plugin inside the ``djangocms-googlemap-container`` container.
         *
         * <div class="djangocms-googlemap js-djangocms-googlemap">
         *     <div class="djangocms-googlemap-container js-djangocms-googlemap-container"></div>
         * </div>
         *
         * @class GoogleMap
         * @constructor
         * @param {HTMLElement} container single document node
         */
        function GoogleMapConstructor(container) {
            this.container = container;
            this.markers = [];
            this.bounds = new google.maps.LatLngBounds();
            this.settings = {
                zoom: parseInt(getAttr(container, 'zoom')),
                styles: JSON.parse(getAttr(container, 'style') || false),
                zoomControl: getAttr(container, 'zoom-control'),
                streetViewControl: getAttr(container, 'street-view-control'),
                rotateControl: getAttr(container, 'rotate-control'),
                scaleControl: getAttr(container, 'scale-control'),
                fullscreenControl: getAttr(container, 'fullscreen-control'),
                panControl: getAttr(container, 'pan-control'),
                disableDoubleClickZoom: getAttr(container, 'double-click-zoom') === false,
                draggable: getAttr(container, 'draggable'),
                keyboardShortcuts: getAttr(container, 'keyboard-shortcuts'),
                scrollwheel: getAttr(container, 'scrollwheel'),
                mapTypeId: google.maps.MapTypeId[getAttr(container, 'map-type-control')],
                center: {
                    lat: parseFloat(getAttr(container, 'lat')) || 0,
                    lng: parseFloat(getAttr(container, 'lng')) || 0
                }
            };
            var mapContainer = container.getElementsByClassName('js-djangocms-googlemap-container');
            var markers = container.getElementsByClassName('js-djangocms-googlemap-marker');
            var routes = container.getElementsByClassName('js-djangocms-googlemap-route');

            // create iterable arrays
            markers = [].slice.call(markers);
            routes = [].slice.call(routes);

            // init the map
            this.map = new google.maps.Map(mapContainer[0], this.settings);

            var that = this;

            // the markers and routes need to be loaded after the map has been
            // initialised as we need to render the markers and set the correct
            // bounds and zoom level on the rendered map (ref #73)
            google.maps.event.addListenerOnce(this.map, 'idle', function () {
                if (markers.length) {
                    that.addMarkers(markers);
                }
                if (routes.length) {
                    that.addRoutes(routes);
                }
            });
        }

        // attach methods
        GoogleMapConstructor.prototype = {
            /**
             * Processes a collection of markers and passes to ``addMarker``.
             *
             * @method addMarkers
             * @param {Array} markers collection of marker nodes
             */
            addMarkers: function addMarkers(markers) {
                var list = markers.map(function (marker) {
                    return {
                        admin: getAttr(marker, 'admin'),
                        title: getAttr(marker, 'title'),
                        address: getAttr(marker, 'address'),
                        lat: getAttr(marker, 'lat'),
                        lng: getAttr(marker, 'lng'),
                        icon: getAttr(marker, 'icon'),
                        showContent: getAttr(marker, 'show-content'),
                        content: marker.innerHTML,
                        animation: google.maps.Animation.DROP
                    }
                }, this);

                list.forEach(function (marker) {
                    this.addMarker(marker);
                }, this);
            },

            /**
             * Processes a single marker and attaches to ``this.map``.
             *
             * @method addMarker
             * @param {HTMLElement} marker single marker node
             */
            addMarker: function addMarker(marker) {
                var that = this;
                var latLng = {
                    lat: parseFloat(marker.lat),
                    lng: parseFloat(marker.lng)
                };
                var geocoder = new google.maps.Geocoder();
                var pin;
                var coords;

                // if there is no manual latlng defined, start geocoder
                if (!latLng.lat || !latLng.lng) {
                    geocoder.geocode({ address: marker.address }, function (results, status) {
                        if (status === google.maps.GeocoderStatus.OK) {
                            coords = results[0].geometry.location;
                            marker.lat = coords.lat();
                            marker.lng = coords.lng();
                            that.addMarker(marker);
                        }
                    });
                } else {
                    // marker data is ready, add to map
                    marker.position = latLng;
                    marker.map = this.map;
                    pin = new google.maps.Marker(marker);
                    // updated related components
                    pin.setMap(this.map);
                    this.markers.push(pin);
                    this.bounds.extend(pin.position);
                    this._addInfoWindow(pin);
                    this._addEditing(pin);
                }

                // call update every time a new marker has been added
                if (this.map) {
                    this.update();
                }
            },

            /**
             * Update map position and bounds.
             *
             * @method update
             */
            update: function update() {
                google.maps.event.addListenerOnce(this.map, 'bounds_changed',
                    function () {
                        if (this.map.getZoom() > this.settings.zoom) {
                            this.map.setZoom(this.settings.zoom);
                        }
                    }.bind(this));
                this.map.fitBounds(this.bounds);
            },

            /**
             * Processes a collection of routes and passes to ``addRoute``.
             * Only one route can be displayed by the default Google Maps
             * interface. Feel free to use this functionality to enhance the
             * default UI with more route options.
             *
             * @method addRoutes
             * @param {Array} routes collection of route nodes
             */
            addRoutes: function addRoutes(routes) {
                routes.forEach(function (route) {
                    this.addRoute(route);
                }, this);
            },

            /**
             * Processes a single route and attaches to ``this.map``.
             *
             * @method addRoute
             * @param {HTMLElement} route single route node
             */
            addRoute: function addRoute(route) {
                var that = this;
                var el = 'js-djangocms-googlemap-direction';
                var directions = route.getElementsByClassName(el);
                var title = getAttr(route, 'title');
                var request = {
                    origin: getAttr(route, 'origin'),
                    destination: getAttr(route, 'destination'),
                    travelMode: getAttr(route, 'travel-mode')
                };

                this.directionsDisplay = new google.maps.DirectionsRenderer();
                this.directionsService = new google.maps.DirectionsService();

                this.directionsDisplay.setPanel(directions[0]);
                this.directionsDisplay.setMap(this.map);

                // if origin is not provided ask for your location
                if (!request.origin && 'geolocation' in navigator) {
                    navigator.geolocation.getCurrentPosition(function(position) {
                        request.origin = position.coords.latitude + ',' + position.coords.longitude;
                        that.setDirection(request);
                    });
                } else {
                    that.setDirection(request);
                }
            },

            /**
             * Adds the direction to the ``djangocms-googlemap-direction``dom node.
             *
             * @method setDirection
             * @param {Object} request request to be passed to the ``directionsService``
             */
            setDirection: function setDirection(request) {
                var that = this;

                this.directionsService.route(request, function(result, status) {
                    if (status === 'OK') {
                        that.directionsDisplay.setDirections(result);
                    }
                });
            },

            /**
             * Attaches the GoogleMap info window to the marker pin.
             *
             * @method _addInfoWindow
             * @private
             * @param {Object} marker google map marker node
             */
            _addInfoWindow: function _addInfoWindow(marker) {
                if (marker.content.trim() === '') {
                    return false;
                }
                var that = this;
                var infoWindow = new google.maps.InfoWindow({
                    disableAutoPan: true,
                    content: marker.content
                });

                google.maps.event.addListener(marker, 'click', function () {
                    infoWindow.open(that.map, marker);
                    marker.setAnimation(google.maps.Animation.BOUNCE);
                    // stop animation after a certain timeframe
                    setTimeout(function () {
                        marker.setAnimation(null);
                    }, 750);
                });

                if (marker.showContent) {
                    infoWindow.open(this.map, marker);
                }
            },

            /**
             * Adds double-clock to edit on the google map pin.
             *
             * @method _addEditing
             * @private
             * @param {Object} marker google map marker node
             */
            _addEditing: function _addEditing(marker) {
                // attach double-click to edit for markers
                if (window.CMS && window.CMS.Modal) {
                    google.maps.event.addListener(marker, 'dblclick', function (e) {
                        // the native event in google.maps is stored in e.xa
                        // there's no need to continue if google decides to rename it
                        if (!e.xa) {
                            return false;
                        }
                        e.xa.stopPropagation();

                        var modal = new CMS.Modal();

                        modal.open({
                            url: marker.admin
                        });
                    });
                }
            }
        };

        return GoogleMapConstructor;
    })();

    function InitMap() {
        var elements = document.getElementsByClassName('js-djangocms-googlemap');

        elements = [].slice.call(elements);
        elements.forEach(function (element) {
            var container = element.querySelector('.djangocms-googlemap-container');
            // make sure google map wasn't already initialized on that element
            if (!container.hasChildNodes()) {
                new GoogleMap(element);
            }
        }, this);

    }

    // make sure google maps is loaded after our dom is ready
    window.addEventListener('load', function () {
        InitMap();
    });

    if (window.CMS !== undefined) {
        CMS.$(window).on('cms-content-refresh', function() {
            InitMap();
        })
    }
})();
