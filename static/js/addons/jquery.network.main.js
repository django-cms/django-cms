
// custom map init
function initCustomMap() {
    var styles = [
        {
          featureType: "road",
          elementType: "geometry",
          stylers: [
            { lightness: 100 },
            { visibility: "simplified" }
          ]
        },{
          featureType: "road",
          elementType: "labels",
          stylers: [
            { visibility: "off" }
          ]
        }
      ];

    var styledMap = new google.maps.StyledMapType(styles,
        {name: "Styled Map"});

    var isTouchDevice = /Windows Phone/.test(navigator.userAgent) || ('ontouchstart' in window) || window.DocumentTouch && document instanceof DocumentTouch;
    jQuery('.map-container').each(function() {
        jQuery(this).data('CustomMap', new CustomMap({
            holder: this,
            startCooords: [50.950007, 3.158636],
            mapOptions: {
                maxZoom: 18,
                minZoom: 2,
                zoom: 6,
                streetViewControl: false,
                draggable: !isTouchDevice,
                scrollwheel: false,
                mapTypeControlOptions: {
                  mapTypeIds: [google.maps.MapTypeId.ROADMAP, 'map_style']
                }
            }
        }));

        jQuery(this).data('CustomMap').mapCanvas.mapTypes.set('map_style', styledMap);
        jQuery(this).data('CustomMap').mapCanvas.setMapTypeId('map_style');
    });
}


// custom map init
function CustomMap(opt) {
    this.options = jQuery.extend(true, {
        holder: null,
        holderRatio: 1.9,
        map: '.map-canvas',
        startCooords: [-33.512065, 143.125073],
        templateID: 'new_marker',
        mapOptions: {
            maxZoom: 18,
            zoom: 6
        }
    }, opt);
    this.init();
}

CustomMap.prototype = {
    init: function() {
        if (this.options.holder) {
            this.findElements();
            this.createMap();
            this.attachEvents();
            this.makeCallback('onInit', this);
        }
    },
    findElements: function() {
        this.holder = jQuery(this.options.holder);
        this.map = this.holder.find(this.options.map);
    },
    createMap: function() {
        var self = this;
        this.mapOptions = jQuery.extend({}, this.options.mapOptions);
        this.mapOptions.center = new google.maps.LatLng(this.options.startCooords[0], this.options.startCooords[1]);
        this.mapCanvas = new google.maps.Map(this.map[0], this.mapOptions);
    },
    attachEvents: function() {
        var self = this;

        jQuery(window).on('resize orientationchange', function() {
            if (self.activeMarker && self.activeMarker.length && self.activeMarker.data('popupAPI')) {
                self.activeMarker.data('popupAPI').hidePopup();
            }
            clearTimeout(self.resizeTimer);
            self.resizeTimer = setTimeout(function() {
                if (self.bounds) {
                    self.mapCanvas.fitBounds(self.bounds);
                }
            }, 100);
        });

    },
    loadMarkersJSON: function(url, complete) {
        jQuery.getJSON(url, function(data) {
            complete(data);
        });
    },
    prepareMarker: function(marker) {
        var self = this;
        var coordinates = new google.maps.LatLng(marker.location[0], marker.location[1]);
        marker.extraClass = marker.extraClass || '';
        var markerItem = jQuery(marker.markup);
        var newMarker = {
            coordinates: coordinates,
            markerItem: markerItem
        };
        return newMarker;
    },
    filterMarkers: function() {
        var self = this;
        this.preparedMarkers = [];
        jQuery.each(this.markers, function(key, marker) {
                var readyMarker = self.prepareMarker(marker);
                self.preparedMarkers.push(readyMarker);
        });
        this.addMarkers();
    },
    removeMarkers: function() {
        if (this.addedMarkers && this.addedMarkers.length) {
            for (var i = 0; i < this.addedMarkers.length ; i++) {
                this.removeMarker(this.addedMarkers[i]);
            }
        }
        this.addedMarkers = [];
    },
    removeMarker: function(marker) {
        marker.remove();
        marker.draw = function() {};
    },
    addMarkers: function() {
        var self = this;
        this.makeCallback('onBeforeMarkersAdded', this);
        if (!this.preparedMarkers || !this.preparedMarkers.length) return;

        // array of added markers
        this.addedMarkers = [];
        this.bounds = null;
        for (var i = 0; i < this.preparedMarkers.length; i++) {
            this.addMarker(this.preparedMarkers[i], this.preparedMarkers.length === 1);
        }
        setTimeout(function(){
            if (self.bounds) {
                self.mapCanvas.fitBounds(self.bounds);
            }
        }, 100);
        this.makeCallback('onMarkersAdded', this);
    },
    addMarker: function(obj, state) {
        if(obj.coordinates){
            var self = this, listItem, dirrectionLink, marker;
            if (!this.bounds) {
                this.bounds = new google.maps.LatLngBounds();
            }

            // modyfied from http://stackoverflow.com/questions/20490654/more-than-one-marker-on-same-place-markerclusterer
            var currentMarkers = this.addedMarkers;
            var currentLatLang = obj.coordinates;

            if (currentMarkers.length != 0) {
                for (i=0; i < currentMarkers.length; i++) {
                    var existingMarker = currentMarkers[i];
                    var pos = existingMarker.getPosition();

                    //if a marker already exists in the same position as this marker
                    if (currentLatLang.equals(pos)) {
                        //update the position of the coincident marker by applying a small multipler to its coordinates
                        var newLat = currentLatLang.lat() + (Math.random() -0.5) / 1500;// * (Math.random() * (max - min) + min);
                        var newLng = currentLatLang.lng() + (Math.random() -0.5) / 1500;// * (Math.random() * (max - min) + min);
                        currentLatLang = new google.maps.LatLng(newLat, newLng);
                    }
                }
            }

            marker = new CustomMarker({
                mapAPI: self,
                map: this.mapCanvas,
                coordinates: currentLatLang,
                markerItem: obj.markerItem,
                mapHolder: this.map,
                state: state
            });
            this.bounds.extend(marker.getPosition());
            this.addedMarkers.push(marker);
        }
    },
    groupMarkers: function() {
        var styles = {
            url: '/static/img/pin.png',
            height: 50,
            width: 50,
            textColor: 'white',
            textSize: 10
        };
        this.markerCluster = new MarkerClusterer(this.mapCanvas, this.addedMarkers, {
            styles: [styles],
            gridSize: 20
        });
    },
    makeCallback: function(name) {
        if(typeof this.options[name] === 'function') {
            var args = Array.prototype.slice.call(arguments);
            args.shift();
            this.options[name].apply(this, args);
        }
    }
};

// custom marker
function CustomMarker(obj) {
    this.options = obj;
    this.options.popupWrapClass = 'popup-marker';
    this.setMap(obj.map);

}

if (window.google) {
    CustomMarker.prototype = new google.maps.OverlayView();
    CustomMarker.prototype.draw = function() {
        var self = this,
            div = this.div_,
            jDiv;

        if (!div) {
            div = this.div_ = document.createElement('DIV');
            jDiv = jQuery(div);

            jDiv.append(this.options.markerItem);

            jDiv.addClass(this.options.popupWrapClass).css({position: 'absolute'});
            var panes = this.getPanes();
            panes.floatPane.appendChild(div);
            if (!this.options.markerItem.data('popupAPI')) {

                var popupAPI = new MapPopup({
                    mapAPI: this.options.mapAPI,
                    map: this.options.map,
                    state: this.options.state,
                    mapHolder: this.options.mapHolder,
                    holder: this.options.markerItem,
                    opener: '.opener, .close',
                    popup: '.map-popup'
                });
                this.options.markerItem.data('popupAPI', popupAPI);
            }

        }
        var point = this.getProjection().fromLatLngToDivPixel(this.options.coordinates);
        if (point) {
            div.style.left = point.x + 'px';
            div.style.top = point.y + 'px';
        }
    };
    CustomMarker.prototype.remove = function() {
        if (this.div_) {
            this.div_.parentNode.removeChild(this.div_);
            this.div_ = null;
        }
    };
    CustomMarker.prototype.getPosition = function() {
        return this.options.coordinates;
    };
}

// custom map popup init
function MapPopup(opt) {
    this.options = jQuery.extend({
        holder: null,
        popup: '.drop',
        activeClass: 'popup-active',
        opener: 'a.open'
    }, opt);
    this.init();
}

MapPopup.prototype = {
    init: function() {
        if (this.options.holder && this.options.map && this.options.mapHolder) {
            this.findElements();
            this.attachEvents();
        }
    },
    findElements: function() {
        this.doc = jQuery(document);
        this.holder = jQuery(this.options.holder);
        this.opener = this.holder.find(this.options.opener);
        this.popup = this.holder.find(this.options.popup);
    },
    attachEvents: function() {
        var self = this;
        this.opener.on('click', function(e) {
            e.preventDefault();
            if (self.state) {
                self.hidePopup();
            } else {
                self.showPopup();
            }
        });
        setTimeout(function() {
            if (self.options.state) {
                self.showPopup();
            }
        }, 500);

        this.outsideClickHandler = function(e) {
            var target = jQuery(e.target);
            if (!target.closest(self.holder).length) {
                self.hidePopup();
            }
        };
    },
    showPopup: function() {
        var self = this;
        this.holder.addClass(this.options.activeClass);
        this.state = true;
        this.checkPopupPosition();
        this.options.mapAPI.activeMarker = this.holder;

        setTimeout(function() {
            self.doc.on('click', self.outsideClickHandler);
        }, 100);
    },
    hidePopup: function() {
        this.state = false;
        this.holder.removeClass(this.options.activeClass);
        this.options.mapAPI.activeMarker = null;
        this.doc.off('click', this.outsideClickHandler);
    },
    checkPopupPosition: function() {
        var popupOffsets = {
                top: this.popup.offset().top,
                left: this.popup.offset().left,
                height: this.popup.innerHeight(),
                width: this.popup.innerWidth()
            },
            holderOffsets = {
                top: this.options.mapHolder.offset().top,
                left: this.options.mapHolder.offset().left,
                height: this.options.mapHolder.innerHeight(),
                width: this.options.mapHolder.innerWidth()
            };


        var desiredOffset = {
            left: holderOffsets.width/2 - popupOffsets.width/2,
            top: holderOffsets.height/2 - popupOffsets.height/2,
        }

        if (desiredOffset.top < 0) {
            desiredOffset.top = 20;
        }

        var vDiff = desiredOffset.top - (popupOffsets.top - holderOffsets.top);
        var	hDiff = desiredOffset.left - (popupOffsets.left - holderOffsets.left);

        //if (hDiff < 0) {
            this.repositionMap(vDiff, hDiff);
            return;
        // } else {
        //     hDiff = holderOffsets.left - popupOffsets.left + 50;
        //     if (hDiff > 0) {
        //         this.repositionMap(vDiff, hDiff);
        //         return;
        //     }
        // }
        //
        // if (vDiff < 0) {
        //     this.repositionMap(vDiff, 0);
        //     return;
        // }
    },
    repositionMap: function(vDiff, hDiff) {
        var currCenter = this.options.map.getCenter(),
            pixelpoint = this.options.map.getProjection().fromLatLngToPoint(currCenter),
            newCenter,
            scale = Math.pow(2, this.options.map.getZoom());

        pixelpoint.y = pixelpoint.y - vDiff/scale;
        pixelpoint.x = pixelpoint.x - hDiff/scale;
        newCenter = this.options.map.getProjection().fromPointToLatLng(pixelpoint);
        this.options.map.setCenter(newCenter);
    }
};

(function(){
  var cache = {};
  this.tmpl = function tmpl(str, data){
    // Figure out if we're getting a template, or if we need to
    // load the template - and be sure to cache the result.
    var fn = !/\W/.test(str) ?
      cache[str] = cache[str] ||
        tmpl(document.getElementById(str).innerHTML) :

      // Generate a reusable function that will serve as a template
      // generator (and which will be cached).
      new Function("obj",
        "var p=[],print=function(){p.push.apply(p,arguments);};" +

        // Introduce the data as local variables using with(){}
        "with(obj){p.push('" +

        // Convert the template into pure JavaScript
        str
          .replace(/[\r\t\n]/g, " ")
          .split("<%").join("\t")
          .replace(/((^|%>)[^\t]*)'/g, "$1\r")
          .replace(/\t=(.*?)%>/g, "',$1,'")
          .split("\t").join("');")
          .split("%>").join("p.push('")
          .split("\r").join("\\'")
      + "');}return p.join('');");

    // Provide some basic currying to the user
    return data ? fn( data ) : fn;
  };
})();
