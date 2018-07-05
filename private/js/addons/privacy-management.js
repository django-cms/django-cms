import Cookies from 'js-cookie';

export const baseHost = window.location.hostname.replace('www\.', '');
let preferences;

const django_privacy_management = {
    PREFERENCE_COOKIE_NAME: 'django_privacy_mgmt_preferences',

    PREFERENCES: {
        ESSENTIALS: {
            required: true,
            default: true,
        },
        STATISTICS: {
            required: false,
            default: true,
        },
        MARKETING: {
            required: false,
            default: false,
        },
    },

    _isBoolean: function(value) {
        return typeof value === typeof true;
    },

    setPreference: function(name, value) {
        // sets preferences in the preferences cookie
        // used by the preferences modal

        if (!this._isBoolean(value)) {
            return;
        }

        preferences = this._getPreferences();

        try {
            preferences[name] = value;
        } catch (e) {
            // fail silently
        }
        Cookies.set(this.PREFERENCE_COOKIE_NAME, preferences, {
            // in FF this is required so that the cookie is not deleted after ending the browser session
            // we set it to a very high number of dates so that this cookie 'never' expires.
            expires: 2000,
            domain: baseHost,
        });
    },

    _getPreferences: function() {
        preferences = Cookies.getJSON(this.PREFERENCE_COOKIE_NAME);
        if (!preferences) {
            preferences = {};
        }
        return preferences;
    },

    getPreference: function(name) {
        preferences = this._getPreferences();

        if (preferences.hasOwnProperty(name)) {
            return Boolean(preferences[name]);
        } else {
            // default
            this.setPreference(name, this.PREFERENCES[name]['default']);
            return this.PREFERENCES[name]['default'];
        }
    },
};

export default django_privacy_management;
